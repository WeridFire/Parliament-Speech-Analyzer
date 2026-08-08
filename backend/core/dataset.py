"""
SpeechDataset - speeches and their parallel arrays, kept aligned by construction.

Every metric in this project masks a DataFrame and uses the result to slice a
numpy array of the same length. Done by hand, that is a silent-corruption bug
waiting to happen: pandas indexing is by *label*, numpy indexing is by
*position*, and the two agree only while the frame happens to carry a clean
RangeIndex. Nothing raises when they stop agreeing - the numbers just become
wrong.

This type owns the frame and its arrays together and exposes exactly one way to
narrow them (`subset`), which slices all of them positionally. Callers cannot
express a misaligned slice.

    ds = SpeechDataset(df, embeddings=emb, topic_scores=scores)
    camera = ds.subset(ds.df['source'] == 'camera')
    for key, bucket in ds.by_period('month'):
        ...
"""

import hashlib
import logging
from dataclasses import dataclass, replace
from typing import Iterator, Optional, Sequence

import numpy as np
import pandas as pd

from backend.utils.dates import Granularity, parse_date_series, period_key

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpeechDataset:
    """
    A speeches frame plus any arrays that run parallel to it.

    The frame always carries a 0..n-1 RangeIndex, so label and position coincide
    and stay that way: `subset` rebuilds the index on every narrowing.
    """

    df: pd.DataFrame
    embeddings: Optional[np.ndarray] = None
    topic_scores: Optional[np.ndarray] = None

    def __post_init__(self):
        n = len(self.df)

        for name in ('embeddings', 'topic_scores'):
            array = getattr(self, name)
            if array is not None and len(array) != n:
                raise ValueError(
                    f"{name} has {len(array)} rows but the frame has {n}; "
                    "they must be parallel"
                )

        if not self._has_clean_index(self.df):
            object.__setattr__(self, 'df', self.df.reset_index(drop=True))

    @staticmethod
    def _has_clean_index(df: pd.DataFrame) -> bool:
        index = df.index
        return (
            isinstance(index, pd.RangeIndex)
            and index.start == 0
            and index.step == 1
        )

    # -------------------------------------------------------------------------
    # Narrowing
    # -------------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.df)

    @property
    def is_empty(self) -> bool:
        return len(self.df) == 0

    def take(self, positions: Sequence[int] | np.ndarray) -> "SpeechDataset":
        """Narrow to the given row *positions*, keeping every array in step."""
        positions = np.asarray(positions, dtype=int)

        return SpeechDataset(
            df=self.df.iloc[positions].reset_index(drop=True),
            embeddings=None if self.embeddings is None else self.embeddings[positions],
            topic_scores=None if self.topic_scores is None else self.topic_scores[positions],
        )

    def subset(self, mask) -> "SpeechDataset":
        """
        Narrow by a boolean mask (pandas Series or numpy array) or by positions.

        Boolean masks are converted to positions first, so a Series whose index
        does not match row order cannot smuggle in a misalignment.
        """
        if isinstance(mask, pd.Series):
            values = mask.to_numpy()
        else:
            values = np.asarray(mask)

        if values.dtype == bool:
            if len(values) != len(self.df):
                raise ValueError(
                    f"boolean mask has {len(values)} entries for {len(self.df)} rows"
                )
            positions = np.flatnonzero(values)
        else:
            positions = values

        return self.take(positions)

    def with_arrays(
        self,
        embeddings: Optional[np.ndarray] = None,
        topic_scores: Optional[np.ndarray] = None,
    ) -> "SpeechDataset":
        """Attach arrays computed after construction (validated on the way in)."""
        return replace(
            self,
            embeddings=self.embeddings if embeddings is None else embeddings,
            topic_scores=self.topic_scores if topic_scores is None else topic_scores,
        )

    # -------------------------------------------------------------------------
    # Period bucketing
    # -------------------------------------------------------------------------

    def period_keys(self, granularity: Granularity, date_col: str = 'date') -> pd.Series:
        """Period key per row ('2024', '2024-03'), positionally aligned."""
        parsed = parse_date_series(self.df[date_col])
        return parsed.apply(lambda moment: period_key(moment, granularity))

    def by_period(
        self,
        granularity: Granularity,
        date_col: str = 'date',
        min_speeches: int = 1,
        newest_first: bool = False,
    ) -> Iterator[tuple[str, "SpeechDataset"]]:
        """
        Yield `(period_key, dataset)` for each bucket meeting `min_speeches`.

        Rows with unparseable dates are dropped from the buckets (they are still
        present in the parent dataset).
        """
        keys = self.period_keys(granularity, date_col)
        present = sorted({k for k in keys.dropna().unique()}, reverse=newest_first)

        for key in present:
            bucket = self.subset(keys == key)
            if len(bucket) >= min_speeches:
                yield key, bucket
            else:
                logger.debug(
                    "Skipping %s: %d speeches < %d required", key, len(bucket), min_speeches
                )

    def available_periods(self, date_col: str = 'date') -> dict:
        """Years and months present in the data, in the order the payload uses."""
        years = sorted({int(k) for k in self.period_keys('year', date_col).dropna().unique()})
        months = sorted(self.period_keys('month', date_col).dropna().unique(), reverse=True)
        return {'years': years, 'months': list(months)}

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    def fingerprint(self, text_col: str = 'cleaned_text', **extra) -> str:
        """
        Content hash of the rows this dataset represents.

        Used as a cache key so an embeddings file can only ever be reused for the
        exact texts it was computed from - row count alone is not enough, since
        a re-scrape can change content while keeping the count identical.
        """
        digest = hashlib.sha256()
        digest.update(str(len(self.df)).encode())

        for key in sorted(extra):
            digest.update(f"{key}={extra[key]}".encode())

        if text_col in self.df.columns:
            for value in self.df[text_col].astype(str):
                digest.update(value.encode('utf-8', errors='replace'))
                digest.update(b'\x00')

        return digest.hexdigest()

    def __repr__(self) -> str:
        parts = [f"{len(self.df)} speeches"]
        if self.embeddings is not None:
            parts.append(f"emb{self.embeddings.shape}")
        if self.topic_scores is not None:
            parts.append(f"topics{self.topic_scores.shape}")
        return f"<SpeechDataset {', '.join(parts)}>"
