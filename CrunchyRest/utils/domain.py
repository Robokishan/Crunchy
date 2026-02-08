"""Domain normalization utilities for entity matching."""

import tldextract


def normalize_domain(url: str) -> str | None:
    """
    Normalize a URL to its root domain.
    
    Examples:
        - https://www.stripe.com/about -> stripe.com
        - http://stripe.com/ -> stripe.com
        - www.stripe.com -> stripe.com
        - stripe.com/pricing -> stripe.com
    
    Args:
        url: The URL or domain string to normalize
        
    Returns:
        The normalized domain (e.g., "stripe.com") or None if invalid
    """
    if not url:
        return None
    
    try:
        ext = tldextract.extract(url)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}".lower()
    except Exception:
        pass
    
    return None
