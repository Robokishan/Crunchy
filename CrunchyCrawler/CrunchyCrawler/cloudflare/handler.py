"""
Cloudflare challenge handler using FlareSolverr.

Provides detection and solving capabilities for Cloudflare challenges
using the free, open-source FlareSolverr proxy server.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from loguru import logger

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed. FlareSolverr integration disabled.")


# Cloudflare challenge detection markers
CLOUDFLARE_MARKERS = [
    'cf-turnstile',
    'challenges.cloudflare.com',
    'Just a moment',
    'Checking your browser',
    'cf-challenge-running',
    'cf-spinner',
]

# Page title markers for Cloudflare challenge
CLOUDFLARE_TITLE_MARKERS = [
    'Just a moment',
    'Attention Required',
    'Please Wait',
]


def is_cloudflare_challenge(response) -> bool:
    """
    Detect if the response contains a Cloudflare challenge page.
    
    Args:
        response: Scrapy response object
        
    Returns:
        True if Cloudflare challenge detected, False otherwise
    """
    body = response.text if hasattr(response, 'text') else response.body.decode('utf-8', errors='ignore')
    
    # Check for Cloudflare markers in body
    for marker in CLOUDFLARE_MARKERS:
        if marker in body:
            logger.info(f"Cloudflare challenge detected: found '{marker}'")
            return True
    
    # Check page title
    try:
        from scrapy.selector import Selector
        sel = Selector(response)
        title = sel.xpath('//title/text()').get() or ''
        for title_marker in CLOUDFLARE_TITLE_MARKERS:
            if title_marker.lower() in title.lower():
                logger.info(f"Cloudflare challenge detected: title contains '{title_marker}'")
                return True
    except Exception as e:
        logger.debug(f"Error checking title: {e}")
    
    return False


def is_cloudflare_challenge_from_html(html: str) -> bool:
    """
    Detect if HTML content contains a Cloudflare challenge.
    
    Args:
        html: HTML content string
        
    Returns:
        True if Cloudflare challenge detected, False otherwise
    """
    for marker in CLOUDFLARE_MARKERS:
        if marker in html:
            return True
    return False


async def is_cloudflare_challenge_async(page) -> bool:
    """
    Async version to detect Cloudflare challenge using Playwright page.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if Cloudflare challenge detected, False otherwise
    """
    try:
        content = await page.content()
        
        # Check for Cloudflare markers in content
        for marker in CLOUDFLARE_MARKERS:
            if marker in content:
                logger.info(f"Cloudflare challenge detected (async): found '{marker}'")
                return True
        
        # Check page title
        title = await page.title()
        for title_marker in CLOUDFLARE_TITLE_MARKERS:
            if title_marker.lower() in title.lower():
                logger.info(f"Cloudflare challenge detected (async): title contains '{title_marker}'")
                return True
                
    except Exception as e:
        logger.debug(f"Error in async Cloudflare detection: {e}")
    
    return False


def solve_with_flaresolverr(
    url: str,
    flaresolverr_url: str = "http://localhost:8191/v1",
    max_timeout: int = 60000,
    session: Optional[str] = None,
    cookies: Optional[List[Dict]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Solve Cloudflare challenge using FlareSolverr.
    
    FlareSolverr opens a real browser, solves the challenge, and returns
    the solved HTML content along with cookies and user agent.
    
    Args:
        url: The URL to solve Cloudflare challenge for
        flaresolverr_url: FlareSolverr API endpoint
        max_timeout: Maximum time to wait for solution (milliseconds)
        session: Optional session ID for cookie persistence
        cookies: Optional cookies to send with request
        
    Returns:
        Dictionary containing:
            - 'response': Solved HTML content
            - 'cookies': List of cookies after solving
            - 'userAgent': User agent used by FlareSolverr
            - 'status': HTTP status code
        Returns None if solving failed
    """
    if not REQUESTS_AVAILABLE:
        logger.error("requests library not installed. Cannot use FlareSolverr.")
        return None
    
    try:
        payload: Dict[str, Any] = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": max_timeout,
        }
        
        # Add session if provided (for cookie persistence)
        if session:
            payload["session"] = session
        
        # Add cookies if provided
        if cookies:
            payload["cookies"] = cookies
        
        logger.info(f"Sending URL to FlareSolverr: {url}")
        
        # Calculate timeout in seconds (add buffer for processing)
        timeout_seconds = (max_timeout / 1000) + 30
        
        response = requests.post(
            flaresolverr_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds
        )
        
        result = response.json()
        
        if result.get("status") == "ok":
            solution = result.get("solution", {})
            html_content = solution.get("response", "")
            
            # Check if the returned HTML still has Cloudflare challenge
            if is_cloudflare_challenge_from_html(html_content):
                logger.warning("FlareSolverr returned page still has Cloudflare challenge")
                return None
            
            logger.info(
                f"FlareSolverr solved successfully! "
                f"Status: {solution.get('status')}, "
                f"Cookies: {len(solution.get('cookies', []))}"
            )
            
            return {
                "response": html_content,
                "cookies": solution.get("cookies", []),
                "userAgent": solution.get("userAgent", ""),
                "status": solution.get("status", 200),
                "headers": solution.get("headers", {}),
            }
        else:
            error_msg = result.get("message", "Unknown error")
            logger.error(f"FlareSolverr failed: {error_msg}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"FlareSolverr request timed out after {max_timeout}ms")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to FlareSolverr at {flaresolverr_url}")
        return None
    except Exception as e:
        logger.error(f"FlareSolverr error: {e}")
        return None


def create_flaresolverr_session(
    flaresolverr_url: str = "http://localhost:8191/v1",
    session_id: Optional[str] = None,
) -> Optional[str]:
    """
    Create a FlareSolverr session for cookie persistence.
    
    Args:
        flaresolverr_url: FlareSolverr API endpoint
        session_id: Optional custom session ID
        
    Returns:
        Session ID string, or None if creation failed
    """
    if not REQUESTS_AVAILABLE:
        return None
    
    try:
        payload: Dict[str, Any] = {"cmd": "sessions.create"}
        if session_id:
            payload["session"] = session_id
        
        response = requests.post(
            flaresolverr_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        if result.get("status") == "ok":
            session = result.get("session")
            logger.info(f"Created FlareSolverr session: {session}")
            return session
        
    except Exception as e:
        logger.error(f"Failed to create FlareSolverr session: {e}")
    
    return None


def destroy_flaresolverr_session(
    session_id: str,
    flaresolverr_url: str = "http://localhost:8191/v1",
) -> bool:
    """
    Destroy a FlareSolverr session to free resources.
    
    Args:
        session_id: Session ID to destroy
        flaresolverr_url: FlareSolverr API endpoint
        
    Returns:
        True if destroyed successfully
    """
    if not REQUESTS_AVAILABLE:
        return False
    
    try:
        payload = {
            "cmd": "sessions.destroy",
            "session": session_id
        }
        
        response = requests.post(
            flaresolverr_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        if result.get("status") == "ok":
            logger.info(f"Destroyed FlareSolverr session: {session_id}")
            return True
        
    except Exception as e:
        logger.error(f"Failed to destroy FlareSolverr session: {e}")
    
    return False


class CloudflareHandler:
    """
    Handles Cloudflare challenges using FlareSolverr.
    
    FlareSolverr is a free, open-source proxy server that uses a real
    browser to solve Cloudflare challenges and returns the solved HTML.
    
    Usage:
        handler = CloudflareHandler(flaresolverr_url='http://localhost:8191/v1')
        result = await handler.solve(url)
        if result:
            html = result['response']
            cookies = result['cookies']
    """
    
    def __init__(
        self,
        flaresolverr_url: str = "http://localhost:8191/v1",
        solve_timeout: int = 60000,
        use_session: bool = False,
    ):
        """
        Initialize the Cloudflare handler.
        
        Args:
            flaresolverr_url: FlareSolverr API endpoint URL
            solve_timeout: Maximum time to wait for solution (milliseconds)
            use_session: Whether to use persistent sessions for cookies
        """
        self.flaresolverr_url = flaresolverr_url
        self.solve_timeout = solve_timeout
        self.use_session = use_session
        self.session_id: Optional[str] = None
        self.last_cookies: List[Dict] = []
        self.last_user_agent: str = ""
    
    def _ensure_session(self) -> Optional[str]:
        """Create a session if needed and return session ID."""
        if self.use_session and not self.session_id:
            self.session_id = create_flaresolverr_session(self.flaresolverr_url)
        return self.session_id
    
    async def detect(self, response=None, page=None) -> bool:
        """
        Detect if Cloudflare challenge is present.
        
        Args:
            response: Scrapy response object (optional)
            page: Playwright page object (optional)
            
        Returns:
            True if challenge detected
        """
        if page:
            return await is_cloudflare_challenge_async(page)
        elif response:
            return is_cloudflare_challenge(response)
        return False
    
    async def solve(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Solve Cloudflare challenge for a URL using FlareSolverr.
        
        This method sends the URL to FlareSolverr, which opens a real browser,
        solves any Cloudflare challenges, and returns the solved HTML.
        
        Args:
            url: The URL to solve
            
        Returns:
            Dictionary with 'response' (HTML), 'cookies', 'userAgent', 'status'
            Returns None if solving failed
        """
        # Run the synchronous FlareSolverr call in a thread pool
        # to avoid blocking the async event loop
        loop = asyncio.get_event_loop()
        
        session = self._ensure_session() if self.use_session else None
        
        result = await loop.run_in_executor(
            None,
            lambda: solve_with_flaresolverr(
                url=url,
                flaresolverr_url=self.flaresolverr_url,
                max_timeout=self.solve_timeout,
                session=session,
                cookies=self.last_cookies if self.last_cookies else None,
            )
        )
        
        if result:
            # Store cookies and user agent for future requests
            self.last_cookies = result.get("cookies", [])
            self.last_user_agent = result.get("userAgent", "")
            logger.info(f"Stored {len(self.last_cookies)} cookies from FlareSolverr")
        
        return result
    
    async def solve_and_get_html(self, url: str) -> Optional[str]:
        """
        Convenience method to solve and return just the HTML.
        
        Args:
            url: The URL to solve
            
        Returns:
            Solved HTML content, or None if failed
        """
        result = await self.solve(url)
        if result:
            return result.get("response")
        return None
    
    def get_cookies_for_requests(self) -> Dict[str, str]:
        """
        Get cookies in a format suitable for the requests library.
        
        Returns:
            Dictionary of cookie name -> value
        """
        return {
            cookie["name"]: cookie["value"]
            for cookie in self.last_cookies
            if "name" in cookie and "value" in cookie
        }
    
    def get_cookies_for_scrapy(self) -> Dict[str, str]:
        """
        Get cookies in a format suitable for Scrapy requests.
        
        Returns:
            Dictionary of cookie name -> value
        """
        return self.get_cookies_for_requests()
    
    async def handle_response(self, response, page=None) -> Optional[Dict[str, Any]]:
        """
        Full handling flow: detect and solve if needed.
        
        Args:
            response: Scrapy response object
            page: Playwright page object (optional, not used with FlareSolverr)
            
        Returns:
            Dictionary with solved HTML and cookies if challenge was present and solved,
            None if no challenge or solving failed
        """
        if not is_cloudflare_challenge(response):
            logger.debug("No Cloudflare challenge detected")
            return None
        
        logger.info(f"Handling Cloudflare challenge for: {response.url}")
        return await self.solve(response.url)
    
    def cleanup(self):
        """Clean up resources (destroy session if using one)."""
        if self.session_id:
            destroy_flaresolverr_session(self.session_id, self.flaresolverr_url)
            self.session_id = None
    
    def __del__(self):
        """Destructor to clean up session."""
        try:
            self.cleanup()
        except Exception:
            pass
