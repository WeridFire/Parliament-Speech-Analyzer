"""
Per-speech features, computed once for the whole corpus.

Every analyzer used to re-derive what it needed from the raw text, and the
period orchestrator re-ran every analyzer for every year and month: the corpus
was tokenised, lowercased and pattern-matched dozens of times per export, and
spaCy parsed each party's speeches seventeen times over. On the Camera corpus
that was over five minutes of the run.

Here each speech is read once. Analyzers - for the whole corpus or for a single
month - only aggregate the columns and the term matrix built below, so a period
costs a groupby rather than a re-parse.

Columns added by `add_speech_features`:
    n_words, n_sentences, n_letters   counts behind Gulpease and verbosity
    gulpease                          readability of the single speech, 0-100
    questions, self_refs, negations,  raw marker counts
    numerics
    polarization                      oppositional markers per 1000 words
    note_events                       parsed stage directions (applause, protests)
    mentions                          ids of tracked public figures named
"""

import logging
import re
from typing import Optional

import numpy as np
import pandas as pd

from backend.config import (
    ADVERSATIVE_TERMS,
    FIGURES,
    NEGATION_WORDS,
    NOTE_GROUP_RES,
    NUMERIC_PATTERNS,
    POLARIZATION_PRONOUNS,
    SELF_REFERENCE_WORDS,
    STOP_WORDS,
    US_THEM_PATTERNS,
)
from backend.scoring import rate_per_thousand

logger = logging.getLogger(__name__)

WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
SENTENCE_RE = re.compile(r"[.!?]+")
NUMERIC_RE = re.compile('|'.join(NUMERIC_PATTERNS), re.IGNORECASE)

# Relative weight of each polarization marker family: a fixed formula, stated
# here rather than buried in the arithmetic.
PRONOUN_WEIGHT = 1
ADVERSATIVE_WEIGHT = 2
PATTERN_WEIGHT = 3

FEATURE_COLUMNS = (
    'n_words', 'n_sentences', 'n_letters', 'gulpease', 'questions', 'self_refs',
    'negations', 'numerics', 'polarization', 'note_events', 'mentions',
)


# =============================================================================
# TEXT METRICS
# =============================================================================

def gulpease(n_words: int, n_sentences: int, n_letters: int) -> float:
    """
    Gulpease readability index for Italian: 89 + (300 * sentences - 10 * letters) / words.

    Sentence boundaries in a stenographic report are the stenographer's, not the
    speaker's, so this reads the transcript as much as the speech.
    """
    if n_words <= 0:
        return 0.0
    score = 89 + (300 * max(n_sentences, 1) - 10 * n_letters) / n_words
    return float(min(100.0, max(0.0, score)))


def polarization_rate(text_lower: str, tokens: list[str]) -> float:
    """Weighted "us vs them" markers per thousand words."""
    pronouns = sum(1 for t in tokens if t in POLARIZATION_PRONOUNS)
    adversatives = sum(1 for t in tokens if t in ADVERSATIVE_TERMS)
    patterns = sum(1 for p in US_THEM_PATTERNS if p in text_lower)
    weighted = (
        pronouns * PRONOUN_WEIGHT
        + adversatives * ADVERSATIVE_WEIGHT
        + patterns * PATTERN_WEIGHT
    )
    return rate_per_thousand(weighted, len(tokens))


# =============================================================================
# STAGE DIRECTIONS
# =============================================================================

# Sentence breaks inside a stage direction: a dot before a capitalised word
# ("Applausi. Commenti", "Applausi.Commenti"). A dot inside an all-caps
# abbreviation ("MIN.LING") is part of a name, not a break.
NOTE_SEGMENT_RE = re.compile(r'\.\s*(?=[A-Z][a-zà-ù])|;\s*')

NOTE_KINDS = (
    ('applausi', re.compile(r'^\W*(?:vivi(?:ssimi)?\s+|generali\s+|prolungati\s+)?applaus', re.IGNORECASE)),
    ('proteste', re.compile(r'^\W*(?:vive\s+|vivissime\s+)?proteste', re.IGNORECASE)),
    ('commenti', re.compile(r'^\W*(?:vivi\s+)?commenti', re.IGNORECASE)),
)


def parse_note(note: str) -> Optional[tuple[str, tuple[str, ...]]]:
    """
    Read one stage direction.

    "Applausi dei deputati dei gruppi MoVimento 5 Stelle e Partito
    Democratico-..." -> ('applausi', ('MoVimento 5 Stelle', 'Partito Democratico')).
    Returns None for anything that is not a reaction from the floor ("testo
    corretto", "Indossando la kefiah"). A reaction with no group named - a bare
    "(Applausi)" - comes back with an empty tuple.
    """
    text = ' '.join(str(note).split())
    for kind, pattern in NOTE_KINDS:
        if pattern.match(text):
            if 'grupp' not in text.lower():
                return kind, ()
            groups = tuple(name for name, regex in NOTE_GROUP_RES.items() if regex.search(text))
            return kind, groups
    return None


def parse_notes(notes) -> list:
    """
    All reactions recorded on a speech, as [kind, [groups...]] pairs.

    One direction can carry several reactions - "Applausi. Commenti" - so each
    sentence of it is read separately.
    """
    if notes is None or (isinstance(notes, float) and np.isnan(notes)):
        return []
    events = []
    for note in notes:
        for segment in NOTE_SEGMENT_RE.split(str(note)):
            parsed = parse_note(segment)
            if parsed:
                events.append([parsed[0], list(parsed[1])])
    return events


# =============================================================================
# MENTIONS
# =============================================================================

_FIGURE_RES = [
    (figure['id'], re.compile('|'.join(figure['patterns'])), figure['name'].split()[-1].lower())
    for figure in FIGURES
]


def find_mentions(text: str, speaker: str = '') -> list[str]:
    """
    Ids of the tracked figures a speech names, once each.

    A figure is not counted as mentioning themselves: a minister's own speech
    quoting their name is not someone else talking about them.
    """
    speaker_lower = (speaker or '').lower()
    found = []
    for figure_id, regex, surname in _FIGURE_RES:
        if surname and surname in speaker_lower:
            continue
        if regex.search(text):
            found.append(figure_id)
    return found


# =============================================================================
# THE PASS
# =============================================================================

def add_speech_features(df: pd.DataFrame, text_col: Optional[str] = None) -> pd.DataFrame:
    """
    Return a copy of `df` with every per-speech feature column.

    Reads the original-case text (`raw_text`, else `text`, else `cleaned_text`):
    sentence punctuation and capitalised names both carry signal that the
    lowercased model text has lost.
    """
    if text_col is None:
        text_col = next(c for c in ('raw_text', 'text', 'cleaned_text') if c in df.columns)

    texts = df[text_col].fillna('').astype(str).tolist()
    speakers = (
        df['speaker_base'] if 'speaker_base' in df.columns else df.get('deputy', pd.Series([''] * len(df)))
    ).fillna('').astype(str).tolist()
    notes = df['notes'].tolist() if 'notes' in df.columns else [None] * len(df)

    columns = {name: [] for name in FEATURE_COLUMNS}

    for text, speaker, speech_notes in zip(texts, speakers, notes):
        lower = text.lower()
        tokens = WORD_RE.findall(lower)
        n_words = len(tokens)
        n_sentences = max(1, sum(1 for s in SENTENCE_RE.split(text) if s.strip()))
        n_letters = sum(len(t) for t in tokens)

        columns['n_words'].append(n_words)
        columns['n_sentences'].append(n_sentences)
        columns['n_letters'].append(n_letters)
        columns['gulpease'].append(gulpease(n_words, n_sentences, n_letters))
        columns['questions'].append(text.count('?'))
        columns['self_refs'].append(sum(1 for t in tokens if t in SELF_REFERENCE_WORDS))
        columns['negations'].append(sum(1 for t in tokens if t in NEGATION_WORDS))
        columns['numerics'].append(len(NUMERIC_RE.findall(text)))
        columns['polarization'].append(polarization_rate(lower, tokens))
        columns['note_events'].append(parse_notes(speech_notes))
        columns['mentions'].append(find_mentions(text, speaker))

    out = df.copy()
    for name, values in columns.items():
        out[name] = values
    return out


def ensure_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features if they are missing - lets an analyzer run on a bare frame (tests, notebooks)."""
    if all(column in df.columns for column in FEATURE_COLUMNS):
        return df
    return add_speech_features(df)


# =============================================================================
# LEMMAS AND THE TERM MATRIX
# =============================================================================

# Content words only: the distinctive-vocabulary measures are about what is
# talked about, and function words and verbs ("chiedere", "ricordare",
# "riguardare" topped every party's list before) carry none of that.
CONTENT_POS = {'NOUN', 'PROPN', 'ADJ'}
# Lemmatisation keeps every content lemma; which ones count is decided when the
# term matrix is built, so changing the exclusion lists below never invalidates
# the lemma cache.
LEMMA_VERSION = 'v2-noun-propn-adj'
MAX_CHARS = 20_000

# Parliamentary boilerplate that is a content word grammatically but says
# nothing about the speaker: every group "presents" "proposals" to the "Aula",
# and the majority's rapporteurs "reformulate" the "commissione referente"'s text.
PROCEDURAL_LEMMAS = {
    'presidente', 'presidenza', 'governo', 'collega', 'onorevole', 'aula', 'camera',
    'senato', 'assemblea', 'parlamento', 'deputato', 'senatore', 'emendamento',
    'articolo', 'comma', 'provvedimento', 'decreto', 'legge', 'testo', 'proposta',
    'parere', 'voto', 'votazione', 'seduta', 'gruppo', 'ordine', 'giorno', 'anno',
    'volta', 'parte', 'cosa', 'modo', 'tempo', 'questione', 'punto', 'grazie',
    'signor', 'signora', 'ministro', 'ministra', 'viceministro', 'sottosegretario',
    'sottosegretaria', 'relatore', 'relatrice', 'commissione', 'dichiarazione',
    'esame', 'referente', 'riformulazione', 'premessa', 'interrogante', 'interroganto',
    'interrogazione', 'mozione', 'risoluzione', 'udito', 'numero', 'impegno', 'atto',
    'seguito', 'dispositivo', 'iter', 'sede', 'lettura', 'fiducia', 'question', 'time',
}

# Words of the groups' own names. Members say "il gruppo del MoVimento 5 Stelle"
# constantly, so each party's most "distinctive" words were its own name.
GROUP_NAME_LEMMAS = {
    'fratelli', 'fratello', 'italia', 'lega', 'forza', 'moderati', 'moderato',
    'partito', 'democratico', 'progressista', 'movimento', 'stella', 'stelle',
    'alleanza', 'verdi', 'verde', 'sinistra', 'avs', 'azione', 'viva', 'renew',
    'europa', 'europeista', 'riformatore', 'misto', 'popolare', 'maie',
}

NON_DISTINCTIVE_TERMS = PROCEDURAL_LEMMAS | GROUP_NAME_LEMMAS

_nlp = None


def _load_spacy():
    """spaCy Italian with only the tagger and lemmatizer; None if unavailable."""
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load('it_core_news_sm', disable=['parser', 'ner'])
            _nlp.max_length = MAX_CHARS + 1000
        except (ImportError, OSError) as e:
            logger.warning("spaCy Italian model unavailable (%s); keywords use surface forms", e)
            _nlp = False
    return _nlp or None


def _keep(lemma: str, stop: set) -> bool:
    return len(lemma) >= 3 and lemma.isalpha() and lemma not in stop


def lemmatize_texts(texts: list[str], batch_size: int = 256) -> list[str]:
    """
    Content-word lemmas of each text, space-joined.

    Falls back to lowercase surface tokens when spaCy is not installed, so the
    keyword analyses degrade rather than disappear.
    """
    stop = {w.lower() for w in STOP_WORDS}
    nlp = _load_spacy()

    if nlp is None:
        return [
            ' '.join(t for t in WORD_RE.findall(text.lower()) if _keep(t, stop))
            for text in texts
        ]

    docs = []
    for doc in nlp.pipe((t[:MAX_CHARS] for t in texts), batch_size=batch_size):
        docs.append(' '.join(
            lemma for lemma in (tok.lemma_.lower() for tok in doc if tok.pos_ in CONTENT_POS)
            if _keep(lemma, stop)
        ))
    return docs


def lemmatize_corpus(texts: list[str]) -> list[str]:
    """Lemma documents for `texts`, lemmatising only texts not cached yet."""
    from backend.core.cache import LemmaStore

    return LemmaStore(LEMMA_VERSION).get(list(texts), lemmatize_texts)


def build_term_matrix(docs: list[str], min_df: int = 3):
    """
    Sparse speech x term count matrix over the lemma documents.

    Returns (matrix, vocabulary) where vocabulary[j] names column j. Built once;
    every keyword analysis slices rows out of it.
    """
    from sklearn.feature_extraction.text import CountVectorizer

    if not any(docs):
        from scipy.sparse import csr_matrix

        return csr_matrix((len(docs), 0), dtype=np.int32), np.array([], dtype=object)

    vectorizer = CountVectorizer(
        tokenizer=str.split, token_pattern=None, lowercase=False,
        min_df=min(min_df, len(docs)), dtype=np.int32,
        stop_words=sorted(NON_DISTINCTIVE_TERMS),
    )
    matrix = vectorizer.fit_transform(docs).tocsr()
    return matrix, vectorizer.get_feature_names_out()
