"""
Export analysis data to JSON for the web visualization.

Features:
- Orchestrates the data pipeline: fetch -> clean -> embed -> cluster -> analyze -> export
- Uses modular components from backend.core and backend.analyzers
- Supports parallel processing for multiple data sources
"""
import json
import logging
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Script directory (backend folder)
SCRIPT_DIR = Path(__file__).parent.resolve()

# Add parent directory to path for imports
sys.path.insert(0, str(SCRIPT_DIR.parent))

import numpy as np
import pandas as pd

# Import reusable functions from pipeline
from backend.pipeline import (
    apply_clustering,
    generate_embeddings,
    get_embedding_model,
    reduce_dimensions,
)

# Import from backend package
from backend.ingestion import fetch_all_speeches
from backend.utils import clean_text, show_cache_info, clear_cache

# Import core functionality
from backend.core import (
    SpeechDataset,
    load_cached_speeches,
    save_speeches_cache,
    load_cached_embeddings,
    save_embeddings_cache,
    assign_topics_by_semantics,
    compute_divergence_scores,
    compute_source_output
)
from backend.core.artifacts import ArtifactWriter

# Import analyzers
from backend.analyzers import (
    AnalyticsOrchestrator,
    extract_cluster_topics,
    compute_senator_conformity,
)
from backend.analyzers.rhetoric import add_rhetoric_scores, classify_rhetorical_style
from backend.analyzers.topics import get_cluster_labels

# Import configuration
from backend.config import (
    MONTHS_BACK,
    MIN_WORDS,
    N_CLUSTERS,
    EMBEDDING_MODEL,
    TOPIC_CLUSTERS,
    DATA_SOURCE,
    PARTY_NORMALIZATION,
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


def convert_numpy_types(obj):
    """Recursively convert numpy types to standard Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {convert_numpy_types(k): convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(i) for i in obj)
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.generic):
        # Fallback for other numpy scalars
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    else:
        return obj


def main(
    force_refetch: bool = False,
    force_reembed: bool = False,
    n_clusters_override: int = None,
    source: str = None,
    use_cloudscraper: bool = False,
    max_cache_age_days: int = CACHE_MAX_AGE_DAYS,
    strict: bool = False,
):
    # Use override or config values
    n_clusters = n_clusters_override if n_clusters_override else N_CLUSTERS
    data_source = source if source else DATA_SOURCE
    
    logger.info("Starting data export for web visualization")
    logger.info("Configuration: months_back=%d, clusters=%d, source=%s", MONTHS_BACK, n_clusters, data_source)
    
    # Try to load cached speeches (stale caches are ignored rather than reused)
    if not force_refetch:
        df = load_cached_speeches(data_source, max_age_days=max_cache_age_days)
    else:
        df = None
        
    if df is None:
        logger.info("Fetching speeches (source=%s)...", data_source)
        df = fetch_all_speeches(source=data_source, use_cloudscraper=use_cloudscraper)
        
        if df.empty:
            logger.error("No data fetched")
            return
        
        # Save to cache
        save_speeches_cache(df, data_source)
    
    
    # Filter out PRESIDENTE/Presidenza (procedural speeches)
    if 'group' in df.columns:
        df = df[df['group'] != 'Presidenza']
    if 'deputy' in df.columns:
        df = df[~df['deputy'].str.contains('PRESIDENTE', case=False, na=False)]
    
    logger.info("Speeches after filtering procedural/Presidente: %d", len(df))

    # Clean text
    df['cleaned_text'] = df['text'].apply(clean_text)
    
    # Filter short speeches
    df = df[df['cleaned_text'].str.split().str.len() >= MIN_WORDS].reset_index(drop=True)
    logger.info("After filtering (>=%d words): %d speeches", MIN_WORDS, len(df))
    
    # Filter out unrecognized parties
    INVALID_PARTIES = {'?', 'Unknown Group', '', None}
    df = df[~df['group'].isin(INVALID_PARTIES)].reset_index(drop=True)
    df = df[df['group'].notna()].reset_index(drop=True)
    logger.info("After party filter: %d speeches", len(df))
    
    # Early exit if no speeches remain after filtering
    if len(df) == 0:
        logger.error("No speeches remaining after filtering. Check your cache file or try --refetch to re-download data.")
        logger.info("Hint: Run with --clear-cache to clear stale cache, then --refetch to download fresh data")
        return
    
    # Normalize party names (unify Camera/Senato naming conventions)
    original_parties = df['group'].unique().tolist()
    df['group'] = df['group'].apply(lambda x: PARTY_NORMALIZATION.get(x, x))
    normalized_parties = df['group'].unique().tolist()
    logger.info("Normalized party names: %d -> %d unique parties", len(original_parties), len(normalized_parties))
    
    # Embeddings are cached against a fingerprint of the exact texts they encode,
    # so a corpus that changed without changing size cannot reuse stale vectors.
    corpus_fingerprint = SpeechDataset(df=df).fingerprint(model=EMBEDDING_MODEL)

    embeddings = None
    if not force_reembed:
        embeddings = load_cached_embeddings(data_source, corpus_fingerprint)

    if embeddings is None:
        logger.info("Generating embeddings (this may take a while)...")
        embeddings = generate_embeddings(df['cleaned_text'].tolist(), model_name=EMBEDDING_MODEL)
        save_embeddings_cache(embeddings, data_source, corpus_fingerprint)
    
    # Dimensionality reduction (method comes from config)
    coords = reduce_dimensions(embeddings)
    df['x'] = coords[:, 0]
    df['y'] = coords[:, 1]
    
    # Clustering - use semantic topic assignment if TOPIC_CLUSTERS defined, else K-Means
    topic_scores = None
    
    if TOPIC_CLUSTERS:
        logger.info("Assigning topics by semantic similarity (%d topics)", len(TOPIC_CLUSTERS))
        
        # Reuses the process-wide model rather than loading a second copy
        model = get_embedding_model(EMBEDDING_MODEL)

        assignments, scores, confidence = assign_topics_by_semantics(
            embeddings, model, TOPIC_CLUSTERS
        )
        df['cluster'] = assignments
        df['cluster_conf'] = confidence
        topic_scores = scores
        n_clusters = len(TOPIC_CLUSTERS)

        # Use custom labels from config
        cluster_labels = {cid: info['label'] for cid, info in TOPIC_CLUSTERS.items()}
        cluster_topics = {cid: info['keywords'][:5] for cid, info in TOPIC_CLUSTERS.items()}

        # Speeches too far from every topic are labelled rather than forced.
        cluster_labels[UNCLASSIFIED_CLUSTER] = UNCLASSIFIED_LABEL
        cluster_topics[UNCLASSIFIED_CLUSTER] = []
    else:
        # Use shared clustering function from pipeline
        df['cluster'] = apply_clustering(embeddings, n_clusters=n_clusters)

        # Auto-generate labels and keywords
        cluster_labels = get_cluster_labels(df)
        cluster_topics = extract_cluster_topics(df, top_n=5)

    # Compute cluster centroids for advanced analytics
    logger.info("Computing cluster centroids...")
    cluster_centroids = np.zeros((n_clusters, embeddings.shape[1]))
    for cid in range(n_clusters):
        mask = (df['cluster'] == cid).to_numpy()
        if mask.sum() > 0:
            cluster_centroids[cid] = embeddings[mask].mean(axis=0)

    df['cluster_label'] = df['cluster'].map(cluster_labels)

    # Keep the original-case text for display; `cleaned_text` is for the models.
    df['raw_text'] = df['text']

    # Add rhetoric scores
    logger.info("Analyzing rhetoric patterns...")
    df = add_rhetoric_scores(df)
    df['rhetoric_style'] = df.apply(classify_rhetorical_style, axis=1)

    # Thematic divergence from each party's dominant theme
    logger.info("Computing thematic divergence scores...")
    conformity_df = compute_senator_conformity(df, embeddings)
    divergence_scores = compute_divergence_scores(df, conformity_df)
    
    # Analytics are computed per source in compute_source_output(), which is what
    # the payload actually ships. A combined-corpus pass used to run here and be
    # discarded - every analyzer over every speech, for nothing.

    # One dataset object keeps the frame, embeddings and topic scores in step;
    # every per-source slice below is taken from it positionally.
    dataset = SpeechDataset(df=df, embeddings=embeddings, topic_scores=topic_scores)

    sources_in_data = df['source'].unique() if 'source' in df.columns else ['senate']

    # Each worker receives only its own chamber's data. Previously every worker
    # was handed every chamber's speeches and deputies and filtered them back
    # down, which meant pickling the entire corpus once per source.
    parallel_args = []
    for src in sources_in_data:
        source_dataset = (
            dataset.subset(df['source'] == src) if 'source' in df.columns else dataset
        )
        parallel_args.append((
            src, source_dataset, cluster_labels, cluster_topics,
            divergence_scores, cluster_centroids,
        ))

    # Create output directory
    output_dir = SCRIPT_DIR.parent / 'frontend' / 'public' / 'data'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Process sources in parallel if we have multiple sources
    results = []
    if len(parallel_args) > 1:
        logger.info("Processing %d sources in PARALLEL using ProcessPoolExecutor...", len(parallel_args))
        max_workers = min(2, len(parallel_args))
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all sources for parallel processing
            futures = {executor.submit(compute_source_output, args): args[0] for args in parallel_args}
            
            # Collect results as they complete
            for future in as_completed(futures):
                src_name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info("✓ Completed processing for source: %s", result[0])
                except Exception as exc:
                    logger.error("✗ Source %s generated an exception: %s", src_name, exc)
                    raise
    else:
        # Single source - no need for parallelization
        logger.info("Processing single source sequentially...")
        results = [compute_source_output(parallel_args[0])]
    
    # Write the chunked payload: a small manifest plus resources the frontend
    # fetches on demand, instead of one file it must download in full to render
    # anything.
    writer = ArtifactWriter(output_dir)
    chambers = []
    failed_analyzers = set()

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
  python export_data.py --clear-cache      # Clear all cached data
  python export_data.py --cache-info       # Show cache age and size
"""
    )
    
    # Data fetching options
    parser.add_argument('--refetch', action='store_true', help='Force re-fetch from parliament sources')
    parser.add_argument('--reembed', action='store_true', help='Force re-generate embeddings')
    parser.add_argument('--source', '-s', choices=['senate', 'camera', 'both'], default=None,
                        help=f'Data source (default: {DATA_SOURCE} from config)')
    
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
    )
