"""
Clustering and classification logic.
"""

import logging

import numpy as np
import pandas as pd

from backend.config import TOPIC_MIN_SIMILARITY, UNCLASSIFIED_CLUSTER

logger = logging.getLogger(__name__)

# A speaker needs at least this many speeches before divergence from their
# party's dominant theme means anything; below it the measure is sampling noise.
MIN_SPEECHES_FOR_DIVERGENCE = 5


def assign_topics_by_semantics(
    embeddings: np.ndarray,
    model,
    topic_clusters: dict,
    min_similarity: float = TOPIC_MIN_SIMILARITY,
) -> tuple[list[int], np.ndarray, np.ndarray]:
    """
    Assign each speech to the topic it is closest to in embedding space.

    A bare argmax forces every speech into a topic, including procedural
    remarks that are about none of them. Speeches whose best match falls below
    `min_similarity` are left unclassified, and the margin between the best and
    second-best match is returned so the frontend can show how firm an
    assignment is.

    Returns:
        (assignments, similarity_matrix, confidence)
        confidence is top1 - top2, or 0 for unclassified speeches.
    """
    sorted_cluster_ids = sorted(topic_clusters.keys())

    logger.info("Generating topic embeddings...")
    topic_texts = []
    for cid in sorted_cluster_ids:
        info = topic_clusters[cid]
        # Combine label and keywords for a rich semantic representation
        text = f"{info['label']}: {', '.join(info['keywords'])}"
        topic_texts.append(text)
        logger.debug("Topic %d: %s", cid, text)

    topic_embeddings = model.encode(topic_texts, show_progress_bar=False)

    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(embeddings, topic_embeddings)

    best = np.argmax(similarities, axis=1)
    best_score = similarities[np.arange(len(similarities)), best]

    # Margin over the runner-up: a speech that matches two topics equally well
    # has been assigned arbitrarily, and the payload should say so.
    if similarities.shape[1] > 1:
        partitioned = np.partition(similarities, -2, axis=1)
        confidence = partitioned[:, -1] - partitioned[:, -2]
    else:
        confidence = np.zeros(len(similarities))

    assignments = []
    for position, index in enumerate(best):
        if best_score[position] < min_similarity:
            assignments.append(UNCLASSIFIED_CLUSTER)
            confidence[position] = 0.0
        else:
            assignments.append(sorted_cluster_ids[index])

    unclassified = sum(1 for a in assignments if a == UNCLASSIFIED_CLUSTER)
    logger.info(
        "Topic assignment: %d speeches, %d unclassified (below %.2f similarity)",
        len(assignments), unclassified, min_similarity,
    )

    return assignments, similarities, confidence


def compute_divergence_scores(df: pd.DataFrame, conformity_df: pd.DataFrame) -> dict:
    """
    Share of a speaker's interventions falling outside their party's dominant theme.

    Previously called the "rebel score", which claimed more than the number
    supports: it measures *thematic* divergence, not dissent. A member who sits
    on a different committee than most of their party scores high without ever
    disagreeing with anyone. The name and the frontend label now say what is
    actually measured, and the minimum sample is high enough that one or two
    off-topic interventions cannot produce a 100% score.
    """
    divergence = {}

    if conformity_df.empty:
        return divergence

    # Dominant theme per party (ignoring unclassified speeches)
    party_clusters = {}
    for party in df['group'].unique():
        if party == 'Unknown Group':
            continue
        party_df = df[(df['group'] == party) & (df['cluster'] != UNCLASSIFIED_CLUSTER)]
        if len(party_df) > 0:
            party_clusters[party] = party_df['cluster'].value_counts().idxmax()

    for deputy in df['deputy'].unique():
        deputy_df = df[df['deputy'] == deputy]
        if len(deputy_df) < MIN_SPEECHES_FOR_DIVERGENCE:
            continue

        party = deputy_df['group'].iloc[0]
        if party not in party_clusters:
            continue

        main_cluster = party_clusters[party]
        total = len(deputy_df)
        in_main = int((deputy_df['cluster'] == main_cluster).sum())

        cluster_dist = {int(k): int(v) for k, v in deputy_df['cluster'].value_counts().items()}

        party_df = df[df['group'] == party]
        party_cluster_dist = {
            int(k): round(v / len(party_df) * 100, 1)
            for k, v in party_df['cluster'].value_counts().items()
        }

        divergence[deputy] = {
            'divergence_pct': round(((total - in_main) / total) * 100, 1),
            'main_cluster': int(main_cluster),
            'speeches_in_main': in_main,
            'total_speeches': total,
            'party': party,
            'cluster_distribution': cluster_dist,
            'party_cluster_distribution': party_cluster_dist,
        }

    return divergence


# Previous name, kept so nothing silently imports a missing symbol.
compute_rebel_scores = compute_divergence_scores
