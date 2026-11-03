"""
Export analysis data to JSON for the web visualization.

Features:
- Orchestrates the data pipeline: fetch -> clean -> embed -> assign topics ->
  per-speech features -> analyze -> export
- Uses modular components from backend.core and backend.analyzers
- Everything expensive is computed once per speech and cached per text, so a
  re-run only pays for speeches it has not seen
"""
import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path

# Script directory (backend folder)
SCRIPT_DIR = Path(__file__).parent.resolve()

# Add parent directory to path for imports
sys.path.insert(0, str(SCRIPT_DIR.parent))

import numpy as np

from backend.pipeline import apply_clustering, embed_texts, reduce_dimensions
from backend.ingestion import fetch_all_speeches, load_cached_sittings
from backend.utils import show_cache_info, clear_cache

from backend.core import (
    SpeechDataset,
    assign_topics_by_semantics,
    compute_source_output,
    load_cached_speeches,
    prepare_speeches,
    save_speeches_cache,
    topic_descriptions,
)
from backend.core.artifacts import ArtifactWriter
from backend.core.cache import EmbeddingStore
from backend.core.features import add_speech_features, build_term_matrix, lemmatize_corpus
from backend.analyzers.topics import cluster_keywords

from backend.config import (
    N_CLUSTERS,
    EMBEDDING_MODEL,
    TOPIC_CLUSTERS,
    DATA_SOURCE,
    CACHE_MAX_AGE_DAYS,
    UNCLASSIFIED_CLUSTER,
    UNCLASSIFIED_LABEL,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / 'frontend' / 'public' / 'data'


@contextmanager
def stage(name: str, timings: list):
    """Log how long a pipeline stage took, so a slow step is visible in the run log."""
    started = time.perf_counter()
    yield
    elapsed = time.perf_counter() - started
    timings.append((name, elapsed))
    logger.info("[%5.1fs] %s", elapsed, name)


def load_corpus(
    data_source: str,
    force_refetch: bool,
    offline: bool,
    use_cloudscraper: bool,
    max_cache_age_days: int,
):
    """Raw speech records: cached sittings (offline), the speeches cache, or a fresh fetch."""
    if offline:
        logger.info("Offline: rebuilding the corpus from cached sittings (source=%s)", data_source)
        return load_cached_sittings(data_source)

    # Stale caches are ignored rather than reused
    df = None if force_refetch else load_cached_speeches(data_source, max_age_days=max_cache_age_days)
    if df is None:
        logger.info("Fetching speeches (source=%s)...", data_source)
        df = fetch_all_speeches(source=data_source, use_cloudscraper=use_cloudscraper)
        if not df.empty:
            save_speeches_cache(df, data_source)
    return df


def main(
    force_refetch: bool = False,
    force_reembed: bool = False,
    n_clusters_override: int = None,
    source: str = None,
    use_cloudscraper: bool = False,
    max_cache_age_days: int = CACHE_MAX_AGE_DAYS,
    strict: bool = False,
    offline: bool = False,
    output_dir: Path = None,
):
    n_clusters = n_clusters_override if n_clusters_override else N_CLUSTERS
    data_source = source if source else DATA_SOURCE
    output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    timings = []

    logger.info("Starting data export (source=%s, output=%s)", data_source, output_dir)

    with stage("load speeches", timings):
        df = load_corpus(data_source, force_refetch, offline, use_cloudscraper, max_cache_age_days)

    if df is None or df.empty:
        logger.error("No data fetched")
        return

    with stage("clean and filter", timings):
        df = prepare_speeches(df)

    if df.empty:
        logger.error("No speeches remaining after filtering. Check your cache or try --refetch.")
        return

    with stage("embeddings", timings):
        if force_reembed:
            EmbeddingStore(EMBEDDING_MODEL).clear()
        embeddings = embed_texts(df['cleaned_text'].tolist(), EMBEDDING_MODEL)

    # Sentence embeddings share a large common component; every similarity
    # downstream is taken in the centred space (see core/clustering.py).
    center = embeddings.mean(axis=0)
    centered = embeddings - center

    with stage("projection", timings):
        coords = reduce_dimensions(embeddings)
        df['x'] = coords[:, 0]
        df['y'] = coords[:, 1]

    with stage("topic assignment", timings):
        if TOPIC_CLUSTERS:
            topic_ids, texts = topic_descriptions(TOPIC_CLUSTERS)
            topic_vectors = embed_texts(texts, EMBEDDING_MODEL)
            assignments, _scores, confidence = assign_topics_by_semantics(
                embeddings, topic_vectors, topic_ids, center=center,
            )
            df['cluster'] = assignments
            df['cluster_conf'] = confidence

            cluster_labels = {cid: info['label'] for cid, info in TOPIC_CLUSTERS.items()}
            cluster_topics = {cid: info['keywords'][:5] for cid, info in TOPIC_CLUSTERS.items()}
        else:
            df['cluster'] = apply_clustering(centered, n_clusters=n_clusters)
            cluster_labels, cluster_topics = {}, {}

    with stage("per-speech features", timings):
        df = add_speech_features(df)

    with stage("lemmas and term matrix", timings):
        lemma_docs = lemmatize_corpus(df['raw_text'].tolist())
        terms, vocabulary = build_term_matrix(lemma_docs)
        logger.info("Term matrix: %d speeches x %d terms", *terms.shape)

    if not TOPIC_CLUSTERS:
        # K-Means clusters have no names; label them by their distinctive terms.
        cluster_topics = cluster_keywords(df, terms, vocabulary)
        cluster_labels = {
            cid: ' / '.join(w.title() for w in words[:3]) or f"Cluster {cid}"
            for cid, words in cluster_topics.items()
        }

    # Speeches too far from every topic are labelled rather than forced.
    cluster_labels[UNCLASSIFIED_CLUSTER] = UNCLASSIFIED_LABEL
    cluster_topics.setdefault(UNCLASSIFIED_CLUSTER, [])
    df['cluster_label'] = df['cluster'].map(cluster_labels)

    # One dataset object keeps the frame, embeddings and term matrix in step;
    # every per-chamber slice below is taken from it positionally.
    dataset = SpeechDataset(df=df, embeddings=centered, terms=terms)
    sources = df['source'].unique() if 'source' in df.columns else ['senate']

    # Analytics now aggregate precomputed columns, so the chambers run in this
    # process: a worker pool cost more in process start-up and in pickling the
    # corpus than the work it parallelised.
    results = []
    for src in sources:
        with stage(f"analytics ({src})", timings):
            source_dataset = dataset.subset(df['source'] == src) if 'source' in df.columns else dataset
            results.append(compute_source_output(
                (src, source_dataset, cluster_labels, cluster_topics, vocabulary)
            ))

    # Write the chunked payload: a small manifest plus resources the frontend
    # fetches on demand.
    output_dir.mkdir(exist_ok=True, parents=True)
    writer = ArtifactWriter(output_dir)
    chambers = []
    failed_analyzers = set()

    with stage("write payload", timings):
        for src, source_output, filename in results:
            analytics = source_output.pop('analytics')
            speeches = source_output.pop('speeches')

            chambers.append(writer.write_chamber(
                chamber=src,
                filename=filename,
                core=source_output,
                speeches=speeches,
                analytics=analytics,
            ))

            failed_analyzers.update(source_output['stats']['analytics_run'].get('failed_analyzers', []))
            logger.info("Exported %s: %d speeches", filename, len(speeches))

        writer.write_manifest(chambers)

    logger.info("Export completed\n%s", writer.size_report())
    logger.info(
        "Stage timings: %s (total %.1fs)",
        ', '.join(f"{name} {seconds:.1f}s" for name, seconds in timings),
        sum(seconds for _, seconds in timings),
    )

    for violation in writer.budget_violations():
        logger.warning("Size budget exceeded: %s", violation)

    if failed_analyzers:
        logger.error("Analyzers that failed during this run: %s", sorted(failed_analyzers))
        if strict:
            raise SystemExit(f"Run failed: {sorted(failed_analyzers)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Export Italian Parliament speech data for visualization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_data.py                    # Use cached data if valid
  python export_data.py --refetch          # Force refresh from sources
  python export_data.py --offline          # Rebuild from cached sittings, no network
  python export_data.py --clear-cache      # Clear all cached data
  python export_data.py --cache-info       # Show cache age and size
"""
    )

    # Data fetching options
    parser.add_argument('--refetch', action='store_true', help='Force re-fetch from parliament sources')
    parser.add_argument('--offline', action='store_true',
                        help='Build the corpus from cached sittings only (no network)')
    parser.add_argument('--reembed', action='store_true', help='Force re-generate embeddings')
    parser.add_argument('--source', '-s', choices=['senate', 'camera', 'both'], default=None,
                        help=f'Data source (default: {DATA_SOURCE} from config)')
    parser.add_argument('--output-dir', type=Path, default=None,
                        help=f'Where to write the payload (default: {DEFAULT_OUTPUT_DIR})')

    # Analysis options
    parser.add_argument('--clusters', '-k', type=int, default=None,
                        help=f'Number of K-Means clusters (default: {N_CLUSTERS} from config)')
    parser.add_argument('--cloudscraper', action='store_true',
                        help='Use cloudscraper library to bypass CloudFront blocking (for Colab/data centers)')

    # Cache management
    parser.add_argument('--cache-info', action='store_true', help='Show cache status and exit')
    parser.add_argument('--clear-cache', action='store_true', help='Clear all cached data and exit')
    parser.add_argument('--max-cache-age', type=int, default=CACHE_MAX_AGE_DAYS,
                        help=f'Max cache age in days (default: {CACHE_MAX_AGE_DAYS})')

    # Logging / failure policy
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable debug logging')
    parser.add_argument('--strict', action='store_true',
                        help='Exit non-zero if any analyzer failed during the run')

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle cache commands
    if args.cache_info:
        show_cache_info()
        sys.exit(0)

    if args.clear_cache:
        clear_cache()
        print("✅ Cache cleared")
        sys.exit(0)

    main(
        force_refetch=args.refetch,
        force_reembed=args.reembed,
        n_clusters_override=args.clusters,
        source=args.source,
        use_cloudscraper=args.cloudscraper,
        max_cache_age_days=args.max_cache_age,
        strict=args.strict,
        offline=args.offline,
        output_dir=args.output_dir,
    )
