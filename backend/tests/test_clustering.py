"""
Tests for topic assignment and the per-text embedding store.
"""

import numpy as np
import pytest

from backend.core.cache import ArtifactCache, EmbeddingStore, LemmaStore
from backend.core.clustering import assign_topics_by_semantics, topic_descriptions


class TestTopicAssignment:

    @pytest.fixture
    def generic_pull(self):
        """
        Every speech shares a large common direction (axis 0), as sentence
        embeddings do. Topic 0's description leans on that common direction;
        topic 1's is about axis 2. Speeches 0-3 are about axis 1 (topic 0's
        real subject), speeches 4-7 about axis 2.
        """
        common = np.array([5.0, 0, 0])
        speeches = np.array([common + [0, 1, 0]] * 4 + [common + [0, 0, 1]] * 4)
        topics = np.array([[5.0, 1, 0], [1.0, 0, 1]])
        return speeches, topics

    def test_centring_removes_the_shared_component(self, generic_pull):
        speeches, topics = generic_pull
        assignments, _, _ = assign_topics_by_semantics(speeches, topics, [0, 1], min_similarity=-1)

        assert assignments == [0, 0, 0, 0, 1, 1, 1, 1]

    def test_below_threshold_is_unclassified(self, generic_pull):
        speeches, topics = generic_pull
        assignments, _, confidence = assign_topics_by_semantics(speeches, topics, [0, 1], min_similarity=1.1)

        assert set(assignments) == {-1}
        assert np.all(confidence == 0)

    def test_topic_ids_follow_the_given_order(self, generic_pull):
        speeches, topics = generic_pull
        assignments, _, _ = assign_topics_by_semantics(speeches, topics, [7, 3], min_similarity=-1)

        assert set(assignments) == {7, 3}

    def test_descriptions_are_ordered_by_id(self):
        ids, texts = topic_descriptions({2: {'label': 'B', 'keywords': ['y']}, 1: {'label': 'A', 'keywords': ['x']}})

        assert ids == [1, 2]
        assert texts == ['A: x', 'B: y']


class TestEmbeddingStore:

    def test_only_new_texts_are_encoded(self, tmp_path):
        store = EmbeddingStore('test-model', cache=ArtifactCache(tmp_path))
        calls = []

        def encode(texts):
            calls.append(list(texts))
            return np.array([[len(t), 1.0] for t in texts])

        first = store.get(['aa', 'bbb'], encode)
        second = store.get(['bbb', 'cccc', 'aa'], encode)

        assert calls == [['aa', 'bbb'], ['cccc']]
        assert np.array_equal(second[0], first[1])
        assert second[1][0] == 4

    def test_models_do_not_share_vectors(self, tmp_path):
        cache = ArtifactCache(tmp_path)
        EmbeddingStore('model-a', cache=cache).get(['x'], lambda t: np.ones((len(t), 2)))

        calls = []
        EmbeddingStore('model-b', cache=cache).get(['x'], lambda t: calls.append(t) or np.zeros((len(t), 2)))

        assert calls == [['x']]

    def test_lemma_store_caches_per_text(self, tmp_path):
        store = LemmaStore('v-test', cache=ArtifactCache(tmp_path))
        calls = []

        def lemmatize(texts):
            calls.append(list(texts))
            return [t.upper() for t in texts]

        store.get(['a', 'b'], lemmatize)
        assert store.get(['b', 'c'], lemmatize) == ['B', 'C']
        assert calls == [['a', 'b'], ['c']]
