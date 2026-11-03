"""
Topic assignment.

Speeches are matched to the configured topic descriptions by cosine similarity
- after centring. Sentence embeddings share a large common component, so the
raw similarities are dominated by how *generic* a text is rather than by what it
is about: descriptions that happen to sound like generic parliamentary language
("parlamento", "riforma costituzionale") attracted everything. On the Camera
corpus two topics, Premierato and Riforme Elettorali, took 62% of all speeches.

Subtracting the corpus mean from the speeches and from the topic vectors removes
that shared component. Checked against speeches whose own keywords clearly name
one topic, agreement rose from 51% to 72%, and no topic takes more than about
15% of the corpus.
"""

import logging
from typing import Optional

import numpy as np

from backend.config import TOPIC_MIN_SIMILARITY, UNCLASSIFIED_CLUSTER

logger = logging.getLogger(__name__)


def topic_descriptions(topic_clusters: dict) -> tuple[list[int], list[str]]:
    """Topic ids in order, and the text each one is embedded from."""
    ids = sorted(topic_clusters)
    texts = [
        f"{topic_clusters[cid]['label']}: {', '.join(topic_clusters[cid]['keywords'])}"
        for cid in ids
    ]
    return ids, texts


def _unit(rows: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(rows, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return rows / norms


def assign_topics_by_semantics(
    embeddings: np.ndarray,
    topic_embeddings: np.ndarray,
    topic_ids: list[int],
    min_similarity: float = TOPIC_MIN_SIMILARITY,
    center: Optional[np.ndarray] = None,
) -> tuple[list[int], np.ndarray, np.ndarray]:
    """
    Assign each speech to the topic it is closest to in embedding space.

    Args:
        embeddings: speech vectors
        topic_embeddings: one vector per topic, in `topic_ids` order
        topic_ids: topic id for each row of `topic_embeddings`
        min_similarity: below this best-match similarity a speech is left
            unclassified rather than forced into the least-bad topic
        center: vector subtracted from both sides before comparing; the
            corpus mean of `embeddings` when omitted

    Returns:
        (assignments, similarity_matrix, confidence)
        confidence is top1 - top2, or 0 for unclassified speeches.
    """
    if center is None:
        center = embeddings.mean(axis=0)

    similarities = _unit(embeddings - center) @ _unit(np.asarray(topic_embeddings) - center).T

    best = np.argmax(similarities, axis=1)
    best_score = similarities[np.arange(len(similarities)), best]

    # Margin over the runner-up: a speech that matches two topics equally well
    # has been assigned arbitrarily, and the payload should say so.
    if similarities.shape[1] > 1:
        partitioned = np.partition(similarities, -2, axis=1)
        confidence = partitioned[:, -1] - partitioned[:, -2]
    else:
        confidence = np.zeros(len(similarities))

    unclassified = best_score < min_similarity
    confidence[unclassified] = 0.0
    ids = np.asarray(topic_ids)
    assignments = np.where(unclassified, UNCLASSIFIED_CLUSTER, ids[best]).tolist()

    logger.info(
        "Topic assignment: %d speeches, %d unclassified (below %.2f similarity)",
        len(assignments), int(unclassified.sum()), min_similarity,
    )

    return assignments, similarities, confidence
