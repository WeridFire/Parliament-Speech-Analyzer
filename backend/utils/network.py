
import logging
import requests

logger = logging.getLogger(__name__)

def get_http_client(use_cloudscraper: bool = False):
    """
    Factory function to get HTTP client (requests or cloudscraper).
    
    Args:
        use_cloudscraper: If True, use cloudscraper to bypass CloudFront blocking
    
    Returns:
        HTTP client module (requests or cloudscraper)
    """
    if use_cloudscraper:
        try:
            import cloudscraper
            # logger.info("Using cloudscraper to bypass CloudFront protection")
            return cloudscraper.create_scraper()
        except ImportError:
            logger.warning("cloudscraper not installed, falling back to requests. Install with: pip install cloudscraper")
            return requests
    return requests
