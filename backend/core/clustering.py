"""
Clustering and classification logic.
"""

import logging
import numpy as np
import pandas as pd
import numpy as np
import pandas as pd
# Lazy imports for heavy libraries
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def assign_topics_by_semantics(embeddings: np.ndarray, model, topic_clusters: dict) -> tuple[list[int], np.ndarray]:
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
    from sklearn.metrics.pairwise import cosine_similarity
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
