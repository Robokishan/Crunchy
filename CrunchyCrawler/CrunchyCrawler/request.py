import pickle
from scrapy import Request
from scrapy_playwright.page import PageMethod
from scrapy.spidermiddlewares.httperror import HttpError


headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
}

# Default timeout for normal requests
DEFAULT_DOWNLOAD_TIMEOUT = 60

# Extended timeout for Cloudflare-protected sites
CLOUDFLARE_DOWNLOAD_TIMEOUT = 120


def generateRequest(url, delivery_tag, queue="normal", callback=None, previousResult={}):
    """
    Generate a Scrapy Request with Playwright support.
    
    For Crunchbase URLs, includes extended timeout and page access
    for Cloudflare challenge handling.
    """
    meta = {
        "queue": queue,
        "previousResult": previousResult,
        "delivery_tag": delivery_tag,
        "playwright": True,
        "playwright_include_page": True,  # Enable page access for Cloudflare handling
        "playwright_page_methods": [
            PageMethod("wait_for_load_state", "domcontentloaded"),
        ],
    }

    # Crunchbase: expand "Read More" under About the Company so we capture full long_description
    if "crunchbase.com" in url:
        meta["playwright_page_methods"] = [
            PageMethod("wait_for_load_state", "domcontentloaded"),
            PageMethod("wait_for_timeout", 2500),  # let content render (skip long wait so Cloudflare pages don't timeout)
            PageMethod(
                "evaluate",
                """() => {
                  var tiles = document.querySelectorAll('tile-description');
                  for (var i = 0; i < tiles.length; i++) {
                    var tile = tiles[i];
                    var btn = tile.querySelector('button');
                    if (!btn) continue;
                    var t = (btn.textContent || '').trim();
                    if (!/^(read|show|see|view)\\s*more$|^expand$/i.test(t) || t.length > 25) continue;
                    btn.scrollIntoView({ block: 'center', behavior: 'instant' });
                    btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window }));
                    btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, view: window }));
                    btn.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));
                    btn.click();
                    return true;
                  }
                  return false;
                }""",
            ),
            PageMethod("wait_for_timeout", 3500),  # wait for Angular to expand and render full text
        ]
        meta["download_timeout"] = CLOUDFLARE_DOWNLOAD_TIMEOUT
        # Allow Cloudflare challenge pages (403/503) to reach spider so we can call FlareSolverr
        meta["handle_httpstatus_list"] = [403, 503]
    else:
        meta["download_timeout"] = DEFAULT_DOWNLOAD_TIMEOUT
    
    return Request(
        url,
        headers=headers,
        callback=callback,
        meta=meta,
        dont_filter=False,
    )