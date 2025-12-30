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
from sentence_transformers import SentenceTransformer

# Import reusable functions from pipeline
from backend.pipeline import generate_embeddings, reduce_dimensions, apply_clustering

# Import from backend package
from backend.scrapers import fetch_all_speeches
from backend.utils import clean_text, show_cache_info, clear_cache

# Import core functionality
from backend.core import (
    load_cached_speeches,
    save_speeches_cache,
    load_cached_embeddings,
    save_embeddings_cache,
    assign_topics_by_semantics,
    compute_rebel_scores,
    compute_source_output
)

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
    FETCH_LIMIT,
    SESSIONS_TO_FETCH,
    MIN_WORDS,
    N_CLUSTERS,
    EMBEDDING_MODEL,
    TOPIC_CLUSTERS,
    DATA_SOURCE,
    PARTY_NORMALIZATION,
    CACHE_MAX_AGE_DAYS,
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


def main(force_refetch: bool = False, force_reembed: bool = False, n_clusters_override: int = None, source: str = None, use_transformer_sentiment: bool = False, use_cloudscraper: bool = False):
    # Use override or config values
    n_clusters = n_clusters_override if n_clusters_override else N_CLUSTERS
    data_source = source if source else DATA_SOURCE
    
    logger.info("Starting data export for web visualization")
    logger.info("Configuration: limit=%d, sessions=%d, clusters=%d, source=%s", FETCH_LIMIT, SESSIONS_TO_FETCH, n_clusters, data_source)
    
    # Try to load cached speeches
    if not force_refetch:
        df = load_cached_speeches(data_source)
    else:
        df = None
        
    if df is None:
        logger.info("Fetching speeches (source=%s)...", data_source)
        df = fetch_all_speeches(source=data_source, limit=FETCH_LIMIT, sessions_to_fetch=SESSIONS_TO_FETCH, use_cloudscraper=use_cloudscraper)
        
        if df.empty:
            logger.error("No data fetched")
            return
        
        # Save to cache
        save_speeches_cache(df, data_source)
    
    logger.info("Total speeches loaded: %d", len(df))
    
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
    
    # Normalize party names (unify Camera/Senato naming conventions)
    original_parties = df['group'].unique().tolist()
    df['group'] = df['group'].apply(lambda x: PARTY_NORMALIZATION.get(x, x))
    normalized_parties = df['group'].unique().tolist()
    logger.info("Normalized party names: %d -> %d unique parties", len(original_parties), len(normalized_parties))
    
    # Try to load cached embeddings
    embeddings = None
    if not force_reembed and not force_refetch:
        embeddings = load_cached_embeddings(data_source)
        if embeddings is not None and len(embeddings) != len(df):
            logger.warning("Embeddings cache size mismatch (cache=%d, data=%d), regenerating...", len(embeddings), len(df))
            embeddings = None
            
    if embeddings is None:
        logger.info("Generating embeddings (this may take a while)...")
        embeddings = generate_embeddings(df['cleaned_text'].tolist(), model_name=EMBEDDING_MODEL)
        save_embeddings_cache(embeddings, data_source)
    else:
        logger.info("Loaded embeddings from cache")
    
    # Dimensionality reduction using pipeline function
    coords = reduce_dimensions(embeddings, method='pca')
    df['x'] = coords[:, 0]
    df['y'] = coords[:, 1]
    
    # Clustering - use semantic topic assignment if TOPIC_CLUSTERS defined, else K-Means
    topic_scores = None
    
    if TOPIC_CLUSTERS:
        logger.info("Assigning topics by semantic similarity (%d topics)", len(TOPIC_CLUSTERS))
        
        # Load model for topic embedding
        model = SentenceTransformer(EMBEDDING_MODEL)
            
        assignments, scores = assign_topics_by_semantics(embeddings, model, TOPIC_CLUSTERS)
        df['cluster'] = assignments
        topic_scores = scores
        n_clusters = len(TOPIC_CLUSTERS)
        
        # Use custom labels from config
        cluster_labels = {cid: info['label'] for cid, info in TOPIC_CLUSTERS.items()}
        cluster_topics = {cid: info['keywords'][:5] for cid, info in TOPIC_CLUSTERS.items()}
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
        mask = df['cluster'] == cid
        if mask.sum() > 0:
            cluster_centroids[cid] = embeddings[mask].mean(axis=0)
    
    df['cluster_label'] = df['cluster'].map(cluster_labels)
    
    # Add rhetoric scores
    logger.info("Analyzing rhetoric patterns...")
    df = add_rhetoric_scores(df)
    df['rhetoric_style'] = df.apply(classify_rhetorical_style, axis=1)
    
    # Compute conformity/rebel info
    logger.info("Computing rebel scores...")
    conformity_df = compute_senator_conformity(df, embeddings)
    rebel_scores = compute_rebel_scores(df, conformity_df)
    
    # ========================================================================
    # NEW: Compute advanced analytics with AnalyticsOrchestrator
    # ========================================================================
    logger.info("Computing advanced analytics with new architecture...")
    orchestrator = AnalyticsOrchestrator(
        df=df,
        embeddings=embeddings,
        cluster_labels=cluster_labels,
        cluster_centroids=cluster_centroids,
        source='combined',
        enable_cache=False,  # Don't cache combined results
        text_col='cleaned_text',
        speaker_col='deputy',
        party_col='group',
        cluster_col='cluster',
        date_col='date',
    )
    
    # Run all enabled analyzers
    analytics_data = orchestrator.run_all(use_cache=False)
    logger.info("Advanced analytics computed successfully")
    
    # Prepare cluster metadata
    cluster_meta = {}
    for cid in df['cluster'].unique():
        keywords = cluster_topics.get(cid, [])
        label = cluster_labels.get(cid, f"Cluster {cid}")
        count = len(df[df['cluster'] == cid])
        cluster_meta[int(cid)] = {
            'label': label,
            'keywords': keywords,
            'count': count
        }
    
    # Prepare speeches data used for export
    speeches_data = []
    has_scores = topic_scores is not None
    
    for idx, row in df.iterrows():
        deputy = row['deputy']
        rebel_info = rebel_scores.get(deputy, {})
        
        speech_obj = {
            'deputy': deputy,
            'party': row['group'],
            'date': row['date'],
            'text': row['cleaned_text'][:500],
            'snippet': row['text'],
            'x': float(row['x']),
            'y': float(row['y']),
            'cluster': int(row['cluster']),
            'cluster_label': row['cluster_label'],
            'rhetoric_style': row['rhetoric_style'],
            'rebel_pct': rebel_info.get('rebel_pct', 0),
            'source': row.get('source', 'senate'),
            'url': row.get('url', '')
        }
        
        if has_scores:
            # Add similarity scores for custom projection (round to 3 decimals)
            speech_obj['topic_scores'] = [round(float(s), 3) for s in topic_scores[idx]]
            
        speeches_data.append(speech_obj)
    
    # We need deputies_data for threading arguments, so check backend.core.aggregation for implementation
    from backend.core.aggregation import compute_deputies_by_period
    
    # == Deputy-level aggregation with period breakdowns ==
    logger.info("Aggregating speeches by deputy with period breakdowns...")
    deputies_by_period = compute_deputies_by_period(
        df, topic_scores, cluster_labels, rebel_scores, date_col='date'
    )
    # For backwards compatibility, keep flat list at top level
    deputies_data = deputies_by_period['global']
    
    # Determine which sources are in the data
    sources_in_data = df['source'].unique() if 'source' in df.columns else ['senate']
    
    # Map deputy -> source
    if 'source' in df.columns:
        deputy_sources = df[['deputy', 'source']].drop_duplicates().set_index('deputy')['source'].to_dict()
    else:
        deputy_sources = {d: 'senate' for d in df['deputy'].unique()}

    # Prepare arguments for parallel processing
    parallel_args = []
    for src in sources_in_data:
        if 'source' in df.columns:
            # Filter DataFrame and embeddings for this source
            source_df = df[df['source'] == src].reset_index(drop=True)
            source_embeddings = embeddings[df['source'] == src]
            source_topic_scores = topic_scores[df['source'] == src] if topic_scores is not None else None
        else:
            source_df = df
            source_embeddings = embeddings
            source_topic_scores = topic_scores
        
        # Pack arguments for this source
        args = (
            src, source_df, source_embeddings, cluster_labels, cluster_topics,
            source_topic_scores, rebel_scores, deputy_sources, speeches_data, 
            deputies_data, cluster_centroids
        )
        parallel_args.append(args)
    
    # Create output directory
    output_dir = SCRIPT_DIR.parent / 'frontend' / 'public'
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
    
    # Write output files
    for src, source_output, filename in results:
        output_file = output_dir / f'{filename}.json'
        
        # Convert numpy types to native Python types before dumping
        source_output = convert_numpy_types(source_output)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(source_output, f, ensure_ascii=False, indent=2)
        logger.info("Exported %d speeches to %s", source_output['stats']['total_speeches'], output_file)
    
    logger.info("Export completed: %d total speeches", len(speeches_data))
    logger.info("Files created: %s", ', '.join(f'{filename}.json' for _, _, filename in results))


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
    parser.add_argument('--transformer-sentiment', action='store_true',
                        help='Use transformer model for sentiment (deprecated, configured in config.yaml)')
    parser.add_argument('--cloudscraper', action='store_true',
                        help='Use cloudscraper library to bypass CloudFront blocking (for Colab/data centers)')
    
    # Cache management
    parser.add_argument('--cache-info', action='store_true', help='Show cache status and exit')
    parser.add_argument('--clear-cache', action='store_true', help='Clear all cached data and exit')
    parser.add_argument('--max-cache-age', type=int, default=CACHE_MAX_AGE_DAYS,
                        help=f'Max cache age in days (default: {CACHE_MAX_AGE_DAYS})')
    
    # Logging
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable debug logging')
    
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
        use_transformer_sentiment=args.transformer_sentiment,
        use_cloudscraper=args.cloudscraper
    )
