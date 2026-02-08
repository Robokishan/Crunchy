"""
Cross-discovery: find Tracxn URLs via DuckDuckGo for Crunchbase companies.

Uses the ddgs library (no API key, no signup). pip install ddgs
"""

import re
import time
from loguru import logger

from ddgs import DDGS

from databucket.models import TracxnRaw
from utils.domain import normalize_domain


# Rate limiting - seconds between requests
DUCKDUCKGO_SEARCH_DELAY = 1

# Tracxn URL pattern: .../d/companies/<slug>/__<hash> or .../d/companies/<slug>/...
_TRACXN_SLUG_RE = re.compile(r"tracxn\.com/d/companies/([^/]+)")
# Canonical company page: base URL only (strip /latest-shareholding, /funding-and-investors, etc.)
_TRACXN_BASE_RE = re.compile(r"(https?://[^/]*tracxn\.com/d/companies/[^/]+/__[A-Za-z0-9_-]+)(?:/|#|$)")


def _tracxn_canonical_url(url: str) -> str:
    """Return canonical company page URL (strip sub-pages like /latest-shareholding)."""
    m = _TRACXN_BASE_RE.search(url)
    return m.group(1) if m else url


def _slug_from_tracxn_url(url: str) -> str | None:
    """Extract company slug from Tracxn URL (e.g. 'browserstack' from .../companies/browserstack/__...)."""
    m = _TRACXN_SLUG_RE.search(url)
    return m.group(1).lower() if m else None


def _match_candidates(company_name: str, domain: str) -> set[str]:
    """Build set of slug-like strings to match against Tracxn URL slugs (lowercase)."""
    candidates = set()
    if domain:
        # e.g. browserstack.com -> browserstack, thelevel.ai -> thelevel
        candidates.add(domain.split(".")[0].lower())
    if (company_name or "").strip():
        # e.g. BrowserStack -> browserstack, The Level -> the-level (Tracxn often uses hyphens)
        slug = re.sub(r"[^\w\s-]", "", (company_name or "").strip().lower())
        slug = re.sub(r"[-\s]+", "-", slug).strip("-")
        if slug:
            candidates.add(slug)
            candidates.add(slug.replace("-", ""))  # the-level -> thelevel
    return candidates


def _duckduckgo_search(query: str, max_results: int = 10) -> list[str]:
    """Run DuckDuckGo web search; return list of result URLs."""
    try:
        results = DDGS().text(query, max_results=max_results)
        return [r["href"] for r in results if r.get("href")]
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return []


def discover_tracxn_url(company_name: str, domain: str) -> str | None:
    """
    Find a Tracxn company page URL via DuckDuckGo search.

    Args:
        company_name: The company name to search for
        domain: The normalized domain (e.g., "stripe.com")

    Returns:
        The Tracxn URL if found, None otherwise
    """
    if not domain:
        logger.debug(f"No domain provided for {company_name}, skipping discovery")
        return None

    # Skip if we already have this company in TracxnRaw
    try:
        if TracxnRaw.objects.filter(normalized_domain=domain).exists():
            logger.debug(f"Company {domain} already in TracxnRaw, skipping discovery")
            return None
    except Exception as e:
        logger.error(f"Error checking TracxnRaw: {e}")

    tracxn_url = None
    queries = []
    if (company_name or "").strip():
        queries.append(f'site:tracxn.com/d/companies "{company_name.strip()}"')
        queries.append(f'site:tracxn.com {company_name.strip()}')
    queries.append(f'site:tracxn.com/d/companies "{domain}"')

    candidates = _match_candidates(company_name, domain)
    for query in queries:
        logger.info(f"DuckDuckGo search: {query}")
        raw_urls = _duckduckgo_search(query, max_results=10)
        print(f"[discovery] Raw DuckDuckGo results ({len(raw_urls)}): {raw_urls}")
        for url in raw_urls:
            if "tracxn.com/d/companies" not in url:
                continue
            slug = _slug_from_tracxn_url(url)
            if not slug:
                continue
            # Only use URL whose slug matches our company/domain (avoid wrong company)
            if slug in candidates:
                tracxn_url = _tracxn_canonical_url(url)
                logger.info(f"Found Tracxn URL for {company_name or domain}: {tracxn_url}")
                break
        if tracxn_url:
            break
        time.sleep(DUCKDUCKGO_SEARCH_DELAY)

    if not tracxn_url:
        logger.info(f"No Tracxn URL found for {company_name} ({domain})")

    return tracxn_url
