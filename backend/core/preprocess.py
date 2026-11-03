"""
From scraped records to the corpus the models and analyzers see.

The one correctness trap here was the chair filter. It dropped every row whose
speaker key contained "PRESIDENTE" - and the key embeds the group label, which
for Forza Italia is "FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE". Every Forza
Italia speech at the Camera (698 of them) was discarded as if it were the
chair's, and a party of government vanished from every analysis. The chair is
now recognised by its role, which the parsers record.
"""

import logging

import pandas as pd

from backend.config import MIN_WORDS, normalize_party, party_bloc
from backend.utils import clean_text

logger = logging.getLogger(__name__)

INVALID_GROUPS = {'?', 'Unknown Group', 'Presidenza', ''}


def _fill_missing_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Give a speech with no group label its speaker's usual group.

    Senato reports print the group next to a senator's name most of the time
    but not always, and the Senato register does not carry groups at all, so
    those speeches used to be dropped as "Unknown Group" - about one in twenty.
    """
    if 'speaker_base' not in df.columns:
        return df

    missing = df['group'].isin(INVALID_GROUPS)
    if not missing.any():
        return df

    known = df[~missing]
    usual = known.groupby('speaker_base')['group'].agg(lambda g: g.mode().iloc[0])
    filled = df.loc[missing, 'speaker_base'].map(usual)

    df = df.copy()
    df.loc[missing, 'group'] = filled.fillna(df.loc[missing, 'group'])
    logger.info("Recovered the group of %d of %d unlabelled speeches", int(filled.notna().sum()), int(missing.sum()))
    return df


def prepare_speeches(df: pd.DataFrame, min_words: int = MIN_WORDS) -> pd.DataFrame:
    """
    Filter, clean and normalise raw speech records.

    Returns a new frame with a clean RangeIndex and these columns added or
    rewritten:
        group        canonical group name (see config.party_normalization)
        bloc         maggioranza | opposizione | altro
        deputy       "Speaker Name [Canonical Group]"
        raw_text     the text as delivered, for display and linguistic features
        cleaned_text lowercased, procedural phrases removed, for the models
    """
    df = df.copy()
    initial = len(df)

    if 'role_category' in df.columns:
        df = df[df['role_category'].fillna('') != 'presidenza']
    df = df[df['group'].fillna('') != 'Presidenza']

    df['group'] = df['group'].map(normalize_party)
    df = _fill_missing_groups(df)
    df = df[~df['group'].isin(INVALID_GROUPS)]

    df['raw_text'] = df['text']
    df['cleaned_text'] = df['text'].map(clean_text)
    df = df[df['cleaned_text'].str.split().str.len() >= min_words]

    # Rebuild the key from the canonical group, so the same member is one
    # speaker whichever spelling of their group a sitting used.
    if 'speaker_base' in df.columns:
        base = df['speaker_base'].fillna('').astype(str)
        df['deputy'] = (base + ' [' + df['group'] + ']').where(base != '', df['deputy'])

    df['bloc'] = df['group'].map(party_bloc)
    df = df.reset_index(drop=True)

    logger.info(
        "Prepared %d of %d speeches (%d groups): %s",
        len(df), initial, df['group'].nunique(),
        df['group'].value_counts().to_dict(),
    )
    return df
