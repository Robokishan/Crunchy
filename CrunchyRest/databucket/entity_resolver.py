"""
Entity Resolution module for matching Crunchbase and Tracxn records.

Uses a multi-signal matching strategy:
1. Exact domain match (highest confidence)
2. Fuzzy name matching
3. Composite scoring with founder overlap and founded year

Matched records are merged into the unified Company model.
Low-confidence matches go to MatchQueue for manual review.
"""

import re
from datetime import datetime
from loguru import logger

try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None
    logger.warning("thefuzz not installed. Fuzzy matching disabled.")

from databucket.models import Crunchbase, TracxnRaw, Company, MatchQueue


# Legal suffixes to strip from company names
LEGAL_SUFFIXES = {
    'inc', 'ltd', 'llc', 'corp', 'co', 'company', 'limited',
    'gmbh', 'ag', 'sa', 'plc', 'pvt', 'private', 'incorporated',
    'corporation', 'holdings', 'group', 'technologies', 'technology',
}

# Thresholds for matching decisions
AUTO_MERGE_THRESHOLD = 0.80
REVIEW_THRESHOLD = 0.50

# Source priority for field merging
SOURCE_PRIORITY = {
    'industries': 'crunchbase',
    'funding_total_usd': 'tracxn',
    'funding_rounds': 'tracxn',
    'description': 'crunchbase',
    'long_description': 'crunchbase',
    'founders': 'longest',  # whichever has more founders
    'logo': 'latest',  # whichever was scraped more recently
    'founded': 'crunchbase',
    'similar_companies': 'crunchbase',
    'acquired': 'crunchbase',
    'stocksymbol': 'crunchbase',
}


def normalize_name(name: str) -> str:
    """
    Normalize company name for comparison.
    
    - Lowercase
    - Strip punctuation
    - Remove legal suffixes (Inc, Ltd, LLC, etc.)
    
    Args:
        name: Company name to normalize
        
    Returns:
        Normalized name
    """
    if not name:
        return ''
    
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', '', name)  # Strip punctuation
    tokens = [t for t in name.split() if t not in LEGAL_SUFFIXES]
    return ' '.join(tokens)


def name_similarity(a: str, b: str) -> float:
    """
    Compute similarity score between two company names.
    
    Uses token_sort_ratio from thefuzz which handles word-order differences.
    
    Args:
        a: First company name
        b: Second company name
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if fuzz is None:
        # Fallback: simple exact match after normalization
        na, nb = normalize_name(a), normalize_name(b)
        return 1.0 if na == nb else 0.0
    
    na, nb = normalize_name(a), normalize_name(b)
    return fuzz.token_sort_ratio(na, nb) / 100.0


def founder_overlap(founders_a: list, founders_b: list) -> float:
    """
    Compute Jaccard similarity of founder names.
    
    Args:
        founders_a: List of founder names from source A
        founders_b: List of founder names from source B
        
    Returns:
        Jaccard similarity between 0.0 and 1.0
    """
    if not founders_a or not founders_b:
        return 0.0
    
    # Normalize founder names for comparison
    set_a = {normalize_name(f) for f in founders_a if f}
    set_b = {normalize_name(f) for f in founders_b if f}
    
    if not set_a or not set_b:
        return 0.0
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    return intersection / union if union > 0 else 0.0


def founded_year_match(founded_a: str, founded_b: str) -> float:
    """
    Check if founded years match.
    
    Args:
        founded_a: Founded year/date string from source A
        founded_b: Founded year/date string from source B
        
    Returns:
        1.0 if years match, 0.0 otherwise
    """
    def extract_year(s):
        if not s:
            return None
        match = re.search(r'\b(19|20)\d{2}\b', str(s))
        return match.group() if match else None
    
    year_a = extract_year(founded_a)
    year_b = extract_year(founded_b)
    
    if year_a and year_b:
        return 1.0 if year_a == year_b else 0.0
    return 0.0


class EntityResolver:
    """
    Entity resolution service for matching Crunchbase and Tracxn records.
    """
    
    def compute_score(self, cb: Crunchbase, tx: TracxnRaw) -> float:
        """
        Compute composite matching score between Crunchbase and Tracxn records.
        
        Weights:
        - Domain match: 0.50
        - Name similarity: 0.30
        - Founded year: 0.10
        - Founder overlap: 0.10
        
        Args:
            cb: Crunchbase record
            tx: TracxnRaw record
            
        Returns:
            Composite score between 0.0 and 1.0
        """
        score = 0.0
        signals = {}
        
        # Domain match (weight: 0.50)
        domain_match = 0.0
        if cb.normalized_domain and tx.normalized_domain:
            if cb.normalized_domain == tx.normalized_domain:
                domain_match = 1.0
        signals['domain'] = domain_match
        score += domain_match * 0.50
        
        # Name similarity (weight: 0.30)
        name_score = name_similarity(cb.name or '', tx.name or '')
        signals['name'] = name_score
        score += name_score * 0.30
        
        # Founded year match (weight: 0.10)
        founded_score = founded_year_match(cb.founded or '', tx.founded or '')
        signals['founded'] = founded_score
        score += founded_score * 0.10
        
        # Founder overlap (weight: 0.10)
        founder_score = founder_overlap(cb.founders or [], tx.founders or [])
        signals['founders'] = founder_score
        score += founder_score * 0.10
        
        logger.debug(f"Match score for {cb.name} <-> {tx.name}: {score:.2f} | signals: {signals}")
        
        return score
    
    def build_name_regex(self, name: str) -> str:
        """
        Build a regex pattern for fuzzy name search in MongoDB.
        
        Creates a pattern that matches the first significant word(s) of the company name.
        
        Args:
            name: Company name to build pattern for
            
        Returns:
            Regex pattern string
        """
        normalized = normalize_name(name)
        words = normalized.split()
        if not words:
            return '.*'
        
        # Use first 1-2 words for initial filtering
        prefix = ' '.join(words[:2]) if len(words) > 1 else words[0]
        # Escape regex special chars and make case-insensitive
        escaped = re.escape(prefix)
        return f'(?i).*{escaped}.*'
    
    def merge(self, cb: Crunchbase, tx: TracxnRaw, confidence: float) -> Company:
        """
        Merge Crunchbase and Tracxn records into unified Company.
        
        Uses SOURCE_PRIORITY to determine which source to use for each field.
        
        Args:
            cb: Crunchbase record
            tx: TracxnRaw record
            confidence: Match confidence score
            
        Returns:
            Created or updated Company record
        """
        # Determine domain (prefer non-null)
        domain = cb.normalized_domain or tx.normalized_domain
        
        # Pick best founders (longest list)
        cb_founders = cb.founders or []
        tx_founders = tx.founders or []
        best_founders = cb_founders if len(cb_founders) >= len(tx_founders) else tx_founders
        
        # Pick best logo (prefer most recent)
        best_logo = tx.logo or cb.logo  # Tracxn is likely fresher
        
        # Build source provenance
        source_priority = {}
        for field, source in SOURCE_PRIORITY.items():
            if source == 'longest':
                source_priority[field] = {'source': 'crunchbase' if len(cb_founders) >= len(tx_founders) else 'tracxn'}
            elif source == 'latest':
                source_priority[field] = {'source': 'tracxn'}  # Assume Tracxn is fresher
            else:
                source_priority[field] = {'source': source}
        
        company, created = Company.objects.update_or_create(
            normalized_domain=domain,
            defaults={
                'name': cb.name or tx.name,  # Prefer Crunchbase name
                'website': cb.website or tx.website,
                'crunchbase_url': cb.crunchbase_url,
                'tracxn_url': tx.tracxn_url,
                'match_confidence': confidence,
                
                # From Crunchbase (primary)
                'industries': cb.industries or [],
                'similar_companies': cb.similar_companies or [],
                'description': cb.description or tx.description or '',
                'long_description': cb.long_description or '',
                
                # From Tracxn (primary)
                'funding_total_usd': tx.funding_total_usd or 0,
                'funding_rounds': tx.funding_rounds or [],
                'last_funding_date': '',  # Can be extracted from funding_rounds if needed
                'last_funding_type': '',
                
                # Common fields (prefer Crunchbase, fallback to Tracxn when null/empty)
                'founders': best_founders,
                'logo': best_logo or '',
                'founded': (cb.founded or '').strip() or (tx.founded or '').strip() or '',
                'acquired': cb.acquired or '',
                'stocksymbol': cb.stocksymbol or '',
                
                # Provenance
                'sources': ['crunchbase', 'tracxn'],
                'source_priority': source_priority,
            }
        )
        
        # Mark TracxnRaw as matched
        tx.matched = True
        tx.save(update_fields=['matched'])
        
        action = "Created" if created else "Updated"
        logger.info(f"{action} Company: {company.name} (confidence: {confidence:.2f})")
        
        return company
    
    def queue_for_review(self, cb: Crunchbase, tx: TracxnRaw, confidence: float) -> MatchQueue:
        """
        Add low-confidence match to review queue.
        
        Args:
            cb: Crunchbase record
            tx: TracxnRaw record  
            confidence: Match confidence score
            
        Returns:
            Created MatchQueue record
        """
        # Compute detailed signals for reviewer
        signals = {
            'domain_cb': cb.normalized_domain,
            'domain_tx': tx.normalized_domain,
            'name_cb': cb.name,
            'name_tx': tx.name,
            'name_similarity': name_similarity(cb.name or '', tx.name or ''),
            'founders_cb': cb.founders,
            'founders_tx': tx.founders,
            'founder_overlap': founder_overlap(cb.founders or [], tx.founders or []),
        }
        
        match_queue, created = MatchQueue.objects.update_or_create(
            crunchbase_id=str(cb._id),
            tracxn_id=str(tx._id),
            defaults={
                'confidence': confidence,
                'match_signals': signals,
                'status': 'pending',
            }
        )
        
        logger.info(f"Queued for review: {cb.name} <-> {tx.name} (confidence: {confidence:.2f})")
        
        return match_queue
    
    def create_from_tracxn(self, tx: TracxnRaw) -> Company:
        """
        Create Company record from Tracxn data only (no Crunchbase match).
        
        Args:
            tx: TracxnRaw record
            
        Returns:
            Created Company record
        """
        company, created = Company.objects.update_or_create(
            normalized_domain=tx.normalized_domain,
            defaults={
                'name': tx.name,
                'website': tx.website or '',
                'crunchbase_url': None,
                'tracxn_url': tx.tracxn_url,
                'match_confidence': 1.0,  # Single source, high confidence
                
                # Empty Crunchbase fields
                'industries': [],
                'similar_companies': [],
                'description': tx.description or '',
                'long_description': '',
                
                # From Tracxn
                'funding_total_usd': tx.funding_total_usd or 0,
                'funding_rounds': tx.funding_rounds or [],
                'last_funding_date': '',
                'last_funding_type': '',
                
                # Common fields
                'founders': tx.founders or [],
                'logo': tx.logo or '',
                'founded': tx.founded or '',
                'acquired': '',
                'stocksymbol': '',
                
                # Provenance
                'sources': ['tracxn'],
                'source_priority': {},
            }
        )
        
        # Mark TracxnRaw as matched
        tx.matched = True
        tx.save(update_fields=['matched'])
        
        logger.info(f"Created Company from Tracxn only: {company.name}")
        
        return company
    
    def create_from_crunchbase(self, cb: Crunchbase) -> Company:
        """
        Create Company record from Crunchbase data only (no Tracxn match).
        
        Args:
            cb: Crunchbase record
            
        Returns:
            Created Company record
        """
        company, created = Company.objects.update_or_create(
            normalized_domain=cb.normalized_domain,
            defaults={
                'name': cb.name,
                'website': cb.website or '',
                'crunchbase_url': cb.crunchbase_url,
                'tracxn_url': None,
                'match_confidence': 1.0,  # Single source, high confidence
                
                # From Crunchbase
                'industries': cb.industries or [],
                'similar_companies': cb.similar_companies or [],
                'description': cb.description or '',
                'long_description': cb.long_description or '',
                
                # Empty Tracxn fields
                'funding_total_usd': cb.funding_usd or 0,  # Use Crunchbase funding if available
                'funding_rounds': [],
                'last_funding_date': cb.lastfunding or '',
                'last_funding_type': '',
                
                # Common fields
                'founders': cb.founders or [],
                'logo': cb.logo or '',
                'founded': cb.founded or '',
                'acquired': cb.acquired or '',
                'stocksymbol': cb.stocksymbol or '',
                
                # Provenance
                'sources': ['crunchbase'],
                'source_priority': {},
            }
        )
        
        logger.info(f"Created Company from Crunchbase only: {company.name}")
        
        return company
