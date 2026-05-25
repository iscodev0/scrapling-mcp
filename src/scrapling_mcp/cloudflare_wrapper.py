"""
Custom wrapper for interactive browser sessions with Cloudflare bypass.

This module provides a wrapper around Scrapling's AsyncStealthySession that:
1. Maintains open pages for interactive use (not fetch-and-close)
2. Exposes Cloudflare bypass functionality for interactive sessions
3. Integrates with the MCP interaction tools
"""

import asyncio
from typing import Any, Dict, Optional
from scrapling.fetchers import AsyncStealthySession
from scrapling.engines._browsers._stealth import AsyncStealthySession as _AsyncStealthySession


class CloudflareBypassSession:
    """
    Wrapper that maintains an open stealthy session with Cloudflare bypass capabilities.
    
    Unlike the official MCP's open_session which doesn't support solve_cloudflare,
    this wrapper exposes the internal _cloudflare_solver method for interactive use.
    """
    
    def __init__(self, session: AsyncStealthySession, solve_cloudflare: bool = True):
        self.session = session
        self.solve_cloudflare = solve_cloudflare
        self._pages: Dict[str, Any] = {}  # session_id -> Page
    
    async def get_page(self, session_id: str) -> Any:
        """Get or create a persistent page for a session."""
        if session_id not in self._pages:
            if not self.session.context:
                raise ValueError(f"Session has no browser context")
            
            # Create a new page from the context
            page = await self.session.context.new_page()
            self._pages[session_id] = page
        
        return self._pages[session_id]
    
    async def navigate_with_bypass(self, session_id: str, url: str, wait_for_stability: bool = True) -> Dict[str, Any]:
        """
        Navigate to a URL with Cloudflare bypass.
        
        This method:
        1. Navigates to the URL
        2. Detects and solves Cloudflare challenges if present
        3. Waits for page stability after solving
        4. Returns the final page state
        
        Args:
            session_id: Session identifier
            url: URL to navigate to
            wait_for_stability: Wait for page to stabilize after navigation
            
        Returns:
            Dict with url, title, and cloudflare_solved status
        """
        page = await self.get_page(session_id)
        
        # Navigate to the URL
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Solve Cloudflare if enabled
        cloudflare_solved = False
        if self.solve_cloudflare:
            cloudflare_solved = await self._solve_cloudflare(page)
            
            # Wait for stability after solving
            if cloudflare_solved and wait_for_stability:
                await page.wait_for_load_state("networkidle", timeout=30000)
        
        return {
            "url": page.url,
            "title": await page.title(),
            "cloudflare_solved": cloudflare_solved
        }
    
    async def _solve_cloudflare(self, page: Any, max_attempts: int = 10) -> bool:
        """
        Solve Cloudflare challenge on the current page.
        
        This replicates the logic from Scrapling's _cloudflare_solver but for async use.
        
        Args:
            page: Playwright page object
            max_attempts: Maximum number of attempts to solve
            
        Returns:
            True if Cloudflare was solved or not present, False otherwise
        """
        for attempt in range(max_attempts):
            title = await page.title()
            
            # Check if we're on a Cloudflare challenge page
            if "just a moment" in title.lower():
                # Wait for the challenge to auto-solve (non-interactive)
                await asyncio.sleep(2)
                continue
            
            # Check for interactive Turnstile
            try:
                # Look for the Turnstile iframe
                iframe = page.frame(url=r"challenges\.cloudflare\.com")
                if iframe:
                    # Try to click the checkbox
                    checkbox = iframe.locator('input[type="checkbox"]')
                    if await checkbox.count() > 0:
                        await checkbox.click(timeout=5000)
                        await asyncio.sleep(2)
                        continue
            except Exception:
                pass
            
            # Check if we've passed the challenge
            if "just a moment" not in title.lower():
                return True
            
            await asyncio.sleep(1)
        
        # Final check
        final_title = await page.title()
        return "just a moment" not in final_title.lower()
    
    async def close(self):
        """Close all pages and the session."""
        for page in self._pages.values():
            try:
                await page.close()
            except Exception:
                pass
        
        self._pages.clear()
        
        if self.session:
            await self.session.close()


async def create_cloudflare_session(
    headless: bool = True,
    solve_cloudflare: bool = True,
    **kwargs
) -> CloudflareBypassSession:
    """
    Create a new stealthy session with Cloudflare bypass capabilities.
    
    Args:
        headless: Run browser in headless mode
        solve_cloudflare: Automatically solve Cloudflare challenges
        **kwargs: Additional arguments passed to AsyncStealthySession
        
    Returns:
        CloudflareBypassSession instance
    """
    session = AsyncStealthySession(
        headless=headless,
        **kwargs
    )
    
    await session.start()
    
    return CloudflareBypassSession(
        session=session,
        solve_cloudflare=solve_cloudflare
    )
