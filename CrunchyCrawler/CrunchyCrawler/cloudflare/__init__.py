"""
Cloudflare challenge detection and bypass module.

This module provides functionality to:
- Detect Cloudflare challenges in responses
- Solve challenges using FlareSolverr (free, open-source)
- Retrieve solved HTML content and cookies
"""

from .handler import (
    is_cloudflare_challenge,
    is_cloudflare_challenge_async,
    solve_with_flaresolverr,
    create_flaresolverr_session,
    destroy_flaresolverr_session,
    CloudflareHandler,
)

__all__ = [
    'is_cloudflare_challenge',
    'is_cloudflare_challenge_async',
    'solve_with_flaresolverr',
    'create_flaresolverr_session',
    'destroy_flaresolverr_session',
    'CloudflareHandler',
]
