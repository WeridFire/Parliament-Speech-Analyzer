"""
One shape for every lexicon-derived score.

These metrics count marker words and turn the count into a number the dashboard
prints next to a politician's name, so how that number is built matters.

The previous approach multiplied a marker density by an "empirical" 500 and
clamped the result to 0-100. Two consequences: the scale had no unit anyone
could state, and everything above roughly 20% marker density saturated at 100 -
so the most extreme speakers were indistinguishable from each other precisely
where the measure claimed to be most informative.

What replaces it:

  * `raw` - markers per thousand words. A real unit, comparable across corpora,
    with no ceiling.
  * `pct` - percentile rank *within this corpus*. This is what rankings and bar
    lengths should use, because "more than 90% of their colleagues" is a claim
    the data supports, while "82 out of 100" is not.
  * `n`   - how many speeches the score rests on, so thin samples are visible.
"""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Score:
    """A metric value with its unit, its standing in the corpus and its support."""

    raw: float
    pct: float
    n: int

    def as_dict(self) -> dict:
        return {'raw': round(self.raw, 2), 'pct': round(self.pct, 1), 'n': self.n}


def rate_per_thousand(weighted_markers: float, n_words: int) -> float:
    """
    Marker density expressed per thousand words.

    Unbounded on purpose: clamping is what destroyed the top of the old scale.
    """
    if n_words <= 0:
        return 0.0
    return (weighted_markers / n_words) * 1000


def percentile_ranks(values: Mapping[str, float]) -> dict[str, float]:
    """
    Percentile rank of each value within the group, 0-100.

    Ties share the midpoint of the range they span, so a corpus where many
    speakers score zero does not hand them wildly different ranks.
    """
    if not values:
        return {}

    ordered = sorted(values.values())
    total = len(ordered)

    if total == 1:
        return {key: 50.0 for key in values}

    # For each distinct value, the midpoint of the positions it occupies.
    ranks: dict[float, float] = {}
    position = 0
    while position < total:
        value = ordered[position]
        end = position
        while end + 1 < total and ordered[end + 1] == value:
            end += 1
        midpoint = (position + end) / 2
        ranks[value] = midpoint / (total - 1) * 100
        position = end + 1

    return {key: ranks[value] for key, value in values.items()}


def score_map(
    raw_values: Mapping[str, float],
    counts: Mapping[str, int] | None = None,
) -> dict[str, dict]:
    """
    Turn `{name: raw}` into `{name: {raw, pct, n}}`.

    The single place a lexicon metric becomes a published score.
    """
    ranks = percentile_ranks(raw_values)
    counts = counts or {}

    return {
        name: Score(raw=raw, pct=ranks[name], n=counts.get(name, 0)).as_dict()
        for name, raw in raw_values.items()
    }


def classify_by_percentile(pct: float) -> str:
    """
    Bucket a percentile into a label.

    Thresholds are stated in terms of standing in the corpus - "in the top
    quarter" - rather than an absolute cut on a scale with no unit.
    """
    if pct >= 75:
        return 'alta'
    if pct >= 40:
        return 'media'
    return 'bassa'
