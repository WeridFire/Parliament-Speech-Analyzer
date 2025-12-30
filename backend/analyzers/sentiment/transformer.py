"""
Transformer Sentiment - Optional transformer-based sentiment analysis.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded transformer components
_classifier = None
_tokenizer = None
_is_available = None


def is_transformer_available() -> bool:
    """Check if transformer model is available."""
    global _is_available
    
    if _is_available is not None:
        return _is_available
    
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
        _is_available = True
    except ImportError:
        _is_available = False
        logger.info("Transformers not available for sentiment analysis")
    
    return _is_available


def _load_transformer():
    """Lazy load the transformer model."""
    global _classifier, _tokenizer
    
    if _classifier is not None:
        return _classifier, _tokenizer
    
    if not is_transformer_available():
        return None, None
    
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
        
        model_name = "MilaNLProc/feel-it-italian-sentiment"
        
        logger.info("Loading transformer model: %s", model_name)
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _classifier = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Move to GPU if available
        if torch.cuda.is_available():
            _classifier = _classifier.cuda()
            logger.info("Transformer model moved to GPU")
        
        _classifier.eval()
        logger.info("Transformer model loaded successfully")
        
    except Exception as e:
        logger.warning("Failed to load transformer model: %s", e)
        return None, None
    
    return _classifier, _tokenizer


def compute_transformer_sentiment(texts: list[str], batch_size: int = 32) -> list[dict]:
    """
    Compute sentiment using transformer model.
    
    Args:
        texts: List of texts to analyze
        batch_size: Batch size for processing
    
    Returns:
        List of {'label': str, 'score': float, 'positive': float, 'negative': float}
    """
    classifier, tokenizer = _load_transformer()
    
    if classifier is None:
        return [{'label': 'unknown', 'score': 0, 'positive': 0, 'negative': 0}] * len(texts)
    
    import torch
    
    results = []
    device = next(classifier.parameters()).device
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Truncate long texts
        batch = [text[:512] for text in batch]
        
        # Tokenize
        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(device)
        
        # Predict
        with torch.no_grad():
            outputs = classifier(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
        
        # Extract results
        for j in range(len(batch)):
            negative_prob = probs[j][0].item()
            positive_prob = probs[j][1].item()
            
            label = 'positive' if positive_prob > negative_prob else 'negative'
            score = positive_prob - negative_prob  # -1 to 1 scale
            
            results.append({
                'label': label,
                'score': round(score, 3),
                'positive': round(positive_prob, 3),
                'negative': round(negative_prob, 3)
            })
    
    return results
