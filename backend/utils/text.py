"""
Text utilities for speech preprocessing and cleaning.
"""
import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# Procedural phrases to remove (common parliamentary formalities)
PROCEDURAL_PHRASES = [
    r"grazie[,]?\s*presidente",
    r"signor[a]?\s*presidente",
    r"ho facoltà di parlare",
    r"dichiaro aperta la seduta",
    r"dichiaro chiusa la seduta",
    r"la seduta è aperta",
    r"la seduta è chiusa",
    r"prego[,]?\s*onorevole",
    r"onorevoli colleghi",
    r"colleghe e colleghi",
    r"la parola al[l']?\s*(deputato|onorevole)",
    r"passiamo al punto successivo",
    r"do lettura del",
    r"procediamo con la votazione",
]


def clean_text(text: str) -> str:
    """
    Clean a single speech text by removing procedural phrases and normalizing.
    
    Args:
        text: Raw speech text
    
    Returns:
        Cleaned text with procedural phrases removed
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convert to lowercase for pattern matching
    cleaned = text.lower()
    
    # Remove procedural phrases
    for pattern in PROCEDURAL_PHRASES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def preprocess_speeches(df: pd.DataFrame, min_words: int = 30) -> pd.DataFrame:
    """
    Preprocess the speeches DataFrame by cleaning text and filtering.
    
    Args:
        df: DataFrame with 'text' column
        min_words: Minimum number of words required (default 30)
    
    Returns:
        Preprocessed DataFrame with 'cleaned_text' column added
    """
    logger.info("Preprocessing speeches...")
    
    # Clean text
    df = df.copy()
    df['cleaned_text'] = df['text'].apply(clean_text)
    
    # Calculate word count
    df['word_count'] = df['cleaned_text'].apply(lambda x: len(x.split()) if x else 0)
    
    # Filter short speeches
    original_count = len(df)
    df = df[df['word_count'] >= min_words].reset_index(drop=True)
    
    filtered_count = original_count - len(df)
    logger.info(f"Removed {filtered_count} speeches with fewer than {min_words} words")
    logger.info(f"Remaining speeches: {len(df)}")
    
    return df
