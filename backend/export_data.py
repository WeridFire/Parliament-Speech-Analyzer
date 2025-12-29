"""
Export analysis data to JSON for the web visualization.

Features:
- Caches raw speeches to avoid re-fetching
- Processes cached data for faster iterations
- Uses shared functions from pipeline.py (DRY)
"""
import json
import logging
import sys
from pathlib import Path

# Script directory (backend folder)
SCRIPT_DIR = Path(__file__).parent.resolve()

# Add parent directory to path for imports
sys.path.insert(0, str(SCRIPT_DIR.parent))

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Import reusable functions from pipeline
from backend.pipeline import generate_embeddings, reduce_dimensions, apply_clustering

# Import from backend package
from backend.scrapers import fetch_speeches, fetch_all_speeches
from backend.utils import clean_text, is_cache_valid, save_cache_metadata, show_cache_info, clear_cache, CACHE_DIR
from backend.analyzers import (
    get_cluster_labels,
    extract_cluster_topics,
    add_rhetoric_scores,
    classify_rhetorical_style,
    compute_senator_conformity,
    PoliticalAnalytics,
)
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


def load_cached_speeches(source: str) -> pd.DataFrame | None:
    """Load speeches from cache if available for the specific source."""
    cache_file = CACHE_DIR / f'speeches_raw_{source}.json'
    if cache_file.exists():
        logger.info("Loading speeches from cache: %s", cache_file.name)
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    return None


def save_speeches_cache(df: pd.DataFrame, source: str):
    """Save speeches to cache for the specific source."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f'speeches_raw_{source}.json'
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(df.to_dict('records'), f, ensure_ascii=False, indent=2)
    # Save cache metadata for validation
    save_cache_metadata(source)
    logger.info("Cached %d speeches to %s", len(df), cache_file.name)



def load_cached_embeddings(source: str) -> np.ndarray | None:
    """Load embeddings from cache if available for the specific source."""
    cache_file = CACHE_DIR / f'embeddings_{source}.npy'
    if cache_file.exists():
        logger.info("Loading embeddings from cache: %s", cache_file.name)
        return np.load(cache_file)
    return None


def save_embeddings_cache(embeddings: np.ndarray, source: str):
    """Save embeddings to cache for the specific source."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f'embeddings_{source}.npy'
    np.save(cache_file, embeddings)
    logger.info("Cached embeddings to %s", cache_file.name)


def assign_topics_by_semantics(embeddings: np.ndarray, model: SentenceTransformer, topic_clusters: dict) -> tuple[list[int], np.ndarray]:
    """Assign speeches to closest topic cluster based on semantic similarity.
    Also returns the full similarity matrix.
    
    1. Embeds the topic definition (label + keywords)
    2. Computes cosine similarity between speech embedding and topic embeddings
    3. Assigns best match
    """
    sorted_cluster_ids = sorted(topic_clusters.keys())
    
    # Create topic texts
    topic_texts = []
    logger.info("Generating topic embeddings...")
    for cid in sorted_cluster_ids:
        info = topic_clusters[cid]
        # Combine label and keywords for a rich semantic representation
        text = f"{info['label']}: {', '.join(info['keywords'])}"
        topic_texts.append(text)
        logger.debug("Topic %d: %s", cid, text)
        
    # Embed topics
    topic_embeddings = model.encode(topic_texts, show_progress_bar=False)
    
    # Compute similarities (Speeches x Topics)
    similarities = cosine_similarity(embeddings, topic_embeddings)
    
    # Argmax for each speech
    assignments = np.argmax(similarities, axis=1)
    
    # Map back to cluster IDs (in case they aren't 0-indexed sequential)
    final_assignments = [sorted_cluster_ids[idx] for idx in assignments]
    
    return final_assignments, similarities


def compute_rebel_scores(df: pd.DataFrame, conformity_df: pd.DataFrame) -> dict:
    """Compute rebel scores: % of speeches outside party's main cluster."""
    rebels = {}
    
    if conformity_df.empty:
        return rebels
    
    # Find main cluster per party
    party_clusters = {}
    for party in df['group'].unique():
        if party == 'Unknown Group':
            continue
        party_df = df[df['group'] == party]
        if len(party_df) > 0:
            cluster_counts = party_df['cluster'].value_counts()
            party_clusters[party] = cluster_counts.idxmax()
    
    # Compute rebel score per deputy (min 3 speeches to avoid fake outliers)
    MIN_SPEECHES_FOR_REBEL = 3
    
    for deputy in df['deputy'].unique():
        deputy_df = df[df['deputy'] == deputy]
        if len(deputy_df) < MIN_SPEECHES_FOR_REBEL:
            continue
        
        party = deputy_df['group'].iloc[0]
        if party not in party_clusters:
            continue
        
        main_cluster = party_clusters[party]
        total = len(deputy_df)
        in_main = len(deputy_df[deputy_df['cluster'] == main_cluster])
        
        rebel_pct = ((total - in_main) / total) * 100 if total > 0 else 0
        
        # Compute cluster distribution for this deputy
        cluster_dist = deputy_df['cluster'].value_counts().to_dict()
        cluster_dist = {int(k): v for k, v in cluster_dist.items()}
        
        # Also compute party's cluster distribution for comparison
        party_df = df[df['group'] == party]
        party_cluster_dist = party_df['cluster'].value_counts().to_dict()
        party_cluster_dist = {int(k): round(v / len(party_df) * 100, 1) for k, v in party_cluster_dist.items()}
        
        rebels[deputy] = {
            'rebel_pct': round(rebel_pct, 1),
            'main_cluster': int(main_cluster),
            'speeches_in_main': in_main,
            'total_speeches': total,
            'party': party,
            'cluster_distribution': cluster_dist,
            'party_cluster_distribution': party_cluster_dist
        }
    
    return rebels


def compute_deputies_data(
    df: pd.DataFrame, 
    topic_scores: np.ndarray,
    cluster_labels: dict,
    rebel_scores: dict
) -> list:
    """
    Compute aggregated deputy data from speeches DataFrame.
    
    Can be called with filtered DataFrames to get per-period deputy data.
    
    Args:
        df: DataFrame with speeches (must have x, y, cluster, deputy, group columns)
        topic_scores: Topic similarity scores array (same length as df)
        cluster_labels: Dict mapping cluster_id -> label
        rebel_scores: Dict with rebel info per deputy
        
    Returns:
        List of deputy dicts with x, y, cluster, party, n_speeches, etc.
    """
    deputies_data = []
    has_scores = topic_scores is not None and len(topic_scores) > 0
    
    for deputy in df['deputy'].unique():
        deputy_df = df[df['deputy'] == deputy]
        if len(deputy_df) == 0:
            continue
            
        avg_x = deputy_df['x'].mean()
        avg_y = deputy_df['y'].mean()
        party = deputy_df['group'].iloc[0]
        n_speeches = len(deputy_df)
        
        # Dominant cluster for this deputy
        dominant_cluster = deputy_df['cluster'].mode().iloc[0] if len(deputy_df) > 0 else 0
        cluster_label = cluster_labels.get(dominant_cluster, f"Cluster {dominant_cluster}")
        
        # Get clean name (without party brackets)
        clean_name = deputy.split('[')[0].strip()
        
        rebel_info = rebel_scores.get(deputy, {})
        
        # Determine primary role (use mode or first non-empty)
        role = ""
        if 'role' in deputy_df.columns:
            roles = deputy_df[deputy_df['role'] != '']['role']
            if not roles.empty:
                role = roles.mode()[0]
        
        deputy_obj = {
            'deputy': deputy,
            'name': clean_name,
            'party': party,
            'role': role,
            'x': float(avg_x),
            'y': float(avg_y),
            'n_speeches': n_speeches,
            'cluster': int(dominant_cluster),
            'cluster_label': cluster_label,
            'rebel_pct': rebel_info.get('rebel_pct', 0),
            'source': deputy_df['source'].iloc[0] if 'source' in deputy_df.columns else 'senate'
        }
        
        if has_scores:
            # Average topic scores for this deputy
            indices = deputy_df.index
            # Ensure indices are within bounds
            valid_indices = [i for i in indices if i < len(topic_scores)]
            if valid_indices:
                dep_scores = topic_scores[valid_indices]
                avg_scores = np.mean(dep_scores, axis=0)
                deputy_obj['topic_scores'] = [round(float(s), 3) for s in avg_scores]
            
        deputies_data.append(deputy_obj)
    
    return deputies_data


def compute_deputies_by_period(
    df: pd.DataFrame,
    topic_scores: np.ndarray,
    cluster_labels: dict,
    rebel_scores: dict,
    date_col: str = 'date'
) -> dict:
    """
    Compute deputy aggregates for each year and month.
    
    Returns:
        {
            'global': [...],  # all deputies
            'by_year': {'2024': [...], '2023': [...], ...},
            'by_month': {'2024-12': [...], ...},
            'available_periods': {'years': [...], 'months': [...]}
        }
    """
    from backend.analyzers.temporal import parse_date
    
    logger.info("Computing deputies by period...")
    
    # Parse dates
    df = df.copy()
    df['_parsed_date'] = df[date_col].apply(parse_date)
    df['_year'] = df['_parsed_date'].apply(lambda x: x.year if x else None)
    df['_month'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-{x.month:02d}" if x else None
    )
    
    # Global deputies
    global_deputies = compute_deputies_data(df, topic_scores, cluster_labels, rebel_scores)
    
    # Extract available periods
    years = sorted([int(y) for y in df['_year'].dropna().unique()])
    months = sorted([m for m in df['_month'].dropna().unique()], reverse=True)
    
    # Per-year deputies
    by_year = {}
    for year in years:
        year_df = df[df['_year'] == year].reset_index(drop=True)
        if len(year_df) >= 10:  # Minimum speeches
            # Get topic_scores indices for this subset
            year_indices = df[df['_year'] == year].index.tolist()
            year_scores = topic_scores[year_indices] if topic_scores is not None else None
            year_deputies = compute_deputies_data(year_df, year_scores, cluster_labels, rebel_scores)
            if year_deputies:
                by_year[str(year)] = year_deputies
    
    logger.info("Computed deputies for %d years", len(by_year))
    
    # Per-month deputies
    by_month = {}
    for month in months:
        month_df = df[df['_month'] == month].reset_index(drop=True)
        if len(month_df) >= 5:  # Lower threshold for months
            month_indices = df[df['_month'] == month].index.tolist()
            month_scores = topic_scores[month_indices] if topic_scores is not None else None
            month_deputies = compute_deputies_data(month_df, month_scores, cluster_labels, rebel_scores)
            if month_deputies:
                by_month[month] = month_deputies
    
    logger.info("Computed deputies for %d months", len(by_month))
    
    # Update available periods to only include those with data
    available_periods = {
        'years': [int(y) for y in by_year.keys()],
        'months': list(by_month.keys())
    }
    
    return {
        'global': global_deputies,
        'by_year': by_year,
        'by_month': by_month,
        'available_periods': available_periods
    }


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
    # NEW: Compute advanced analytics
    # ========================================================================
    logger.info("Computing advanced analytics...")
    if use_transformer_sentiment:
        logger.info("Using TRANSFORMER model for sentiment analysis (slower but more accurate)")
    analytics_engine = PoliticalAnalytics(
        df=df,
        embeddings=embeddings,
        cluster_labels=cluster_labels,
        text_col='cleaned_text',
        cluster_col='cluster',
        speaker_col='deputy',
        party_col='group',
        date_col='date',
        use_transformer_sentiment=use_transformer_sentiment
    )
    
    # Compute all metrics with period breakdowns (global, yearly, monthly)
    analytics_data = analytics_engine.get_all_metrics_by_period(granularity='month')
    logger.info("Advanced analytics computed successfully (with period breakdowns)")
    
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
    
    # Prepare speeches data
    speeches_data = []
    # If using custom topics, we have scores. Convert coords to compact lists if needed or just use row index
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
    
    # == Deputy-level aggregation with period breakdowns ==
    logger.info("Aggregating speeches by deputy with period breakdowns...")
    deputies_by_period = compute_deputies_by_period(
        df, topic_scores, cluster_labels, rebel_scores, date_col='date'
    )
    # For backwards compatibility, keep flat list at top level
    deputies_data = deputies_by_period['global']
    
    # Prepare top rebels list
    top_rebels = sorted(
        [{'deputy': k, **v} for k, v in rebel_scores.items() if v['rebel_pct'] > 30],
        key=lambda x: -x['rebel_pct']
    )[:15]
    
    # All rebel scores as a map (for click on any deputy)
    all_rebel_scores = {k: v for k, v in rebel_scores.items()}
    
    # Final output
    output = {
        'speeches': speeches_data,
        'deputies': deputies_data,
        'deputies_by_period': deputies_by_period,  # NEW: period breakdowns
        'clusters': cluster_meta,
        'rebels': top_rebels,
        'all_rebel_scores': all_rebel_scores,  # NEW: all deputies
        'stats': {
            'total_speeches': len(speeches_data),
            'total_deputies': len(deputies_data),
            'total_parties': len(set(d['party'] for d in speeches_data if d['party'] != 'Unknown Group')),
            'n_clusters': n_clusters
        },
        # Advanced analytics
        'analytics': analytics_data
    }
    
    # Save JSON to public folder for Vite (frontend/public)
    # Create per-source JSON files
    output_dir = SCRIPT_DIR.parent / 'frontend' / 'public'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Determine which sources are in the data
    sources_in_data = df['source'].unique() if 'source' in df.columns else ['senate']
    
    # Map deputy -> source
    if 'source' in df.columns:
        deputy_sources = df[['deputy', 'source']].drop_duplicates().set_index('deputy')['source'].to_dict()
    else:
        deputy_sources = {d: 'senate' for d in df['deputy'].unique()}

    for src in sources_in_data:
        if 'source' in df.columns:
            source_speeches = [s for s in speeches_data if s.get('source', 'senate') == src]
            source_deputies = [d for d in deputies_data if d.get('source', 'senate') == src]
            # Filter DataFrame for this source
            source_df = df[df['source'] == src].reset_index(drop=True)
            source_embeddings = embeddings[df['source'] == src]
        else:
            source_speeches = speeches_data
            source_deputies = deputies_data
            source_df = df
            source_embeddings = embeddings
        
        # Calculate rebels for this specific source
        source_candidates = []
        source_rebel_scores_map = {}
        
        for dep, info in rebel_scores.items():
            # Check source of deputy
            dep_source = deputy_sources.get(dep, 'senate')
            if dep_source == src:
                # Add to detailed scores map
                source_rebel_scores_map[dep] = info
                # Check if candidate for top list
                if info['rebel_pct'] > 30:
                    source_candidates.append({'deputy': dep, **info})
        
        # Sort and take top 15
        source_rebels = sorted(source_candidates, key=lambda x: -x['rebel_pct'])[:15]
        
        # ====================================================================
        # Compute analytics SEPARATELY for this source
        # ====================================================================
        logger.info("Computing analytics for source: %s (%d speeches)", src, len(source_df))
        source_analytics_engine = PoliticalAnalytics(
            df=source_df,
            embeddings=source_embeddings,
            cluster_labels=cluster_labels,
            text_col='cleaned_text',
            cluster_col='cluster',
            speaker_col='deputy',
            party_col='group',
            date_col='date'
        )
        source_analytics = source_analytics_engine.get_all_metrics_by_period(granularity='month')
        
        # Build cluster metadata for this source
        source_cluster_meta = {}
        for cid in source_df['cluster'].unique():
            keywords = cluster_topics.get(cid, [])
            label = cluster_labels.get(cid, f"Cluster {cid}")
            count = len(source_df[source_df['cluster'] == cid])
            source_cluster_meta[int(cid)] = {
                'label': label,
                'keywords': keywords,
                'count': count
            }
        
        # Compute per-period deputies for this source
        source_topic_scores = topic_scores[df['source'] == src] if topic_scores is not None else None
        source_deputies_by_period = compute_deputies_by_period(
            source_df, source_topic_scores, cluster_labels, source_rebel_scores_map, date_col='date'
        )
        
        source_output = {
            'speeches': source_speeches,
            'deputies': source_deputies,
            'deputies_by_period': source_deputies_by_period,  # NEW: period breakdowns
            'clusters': source_cluster_meta,
            'rebels': source_rebels,
            'all_rebel_scores': source_rebel_scores_map,
            'stats': {
                'total_speeches': len(source_speeches),
                'total_deputies': len(source_deputies),
                'total_parties': len(set(d['party'] for d in source_speeches if d['party'] != 'Unknown Group')),
                'n_clusters': len(source_cluster_meta),
                'source': src
            },
            # Advanced analytics computed for THIS source only
            'analytics': source_analytics
        }
        
        # Map source to Italian filename
        filename_map = {'senate': 'senato', 'camera': 'camera'}
        filename = filename_map.get(src, src)
        output_file = output_dir / f'{filename}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(source_output, f, ensure_ascii=False, indent=2)
        logger.info("Exported %d speeches to %s", len(source_speeches), output_file)
    
    logger.info("Export completed: %d total speeches", len(speeches_data))
    logger.info("Files created: %s", ', '.join(f'{s}.json' for s in sources_in_data))


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
                        help='Use transformer model for sentiment (slower but more accurate)')
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
