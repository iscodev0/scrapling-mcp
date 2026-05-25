"""Interactive browser tools with Cloudflare bypass support."""

import asyncio
from typing import Any, Dict, Optional
from scrapling.core.ai import ScraplingMCPServer
from scrapling.fetchers import AsyncStealthySession


class CloudflareBypassSession:
    """Wrapper that maintains an open stealthy session with Cloudflare bypass."""
    
    def __init__(self, session: AsyncStealthySession, solve_cloudflare: bool = True):
        self.session = session
        self.solve_cloudflare = solve_cloudflare
        self._pages: Dict[str, Any] = {}
    
    async def get_page(self, session_id: str) -> Any:
        """Get or create a persistent page for a session."""
        if session_id not in self._pages:
            if not self.session.context:
                raise ValueError("Session has no browser context")
            
            page = await self.session.context.new_page()
            self._pages[session_id] = page
        
        return self._pages[session_id]
    
    async def solve_cloudflare_challenge(self, page: Any, max_attempts: int = 15) -> bool:
        """
        Solve Cloudflare challenge on the current page.
        
        Handles both non-interactive (auto-solve) and interactive (Turnstile) challenges.
        """
        for attempt in range(max_attempts):
            title = await page.title()
            
            # Non-interactive challenge: just wait
            if "just a moment" in title.lower():
                await asyncio.sleep(2)
                
                # Check if it resolved
                new_title = await page.title()
                if "just a moment" not in new_title.lower():
                    return True
                continue
            
            # Interactive Turnstile: try to click the checkbox
            try:
                # Look for Turnstile iframe
                frames = page.frames
                for frame in frames:
                    if "challenges.cloudflare.com" in frame.url:
                        # Try to find and click the checkbox
                        checkbox = frame.locator('input[type="checkbox"]')
                        if await checkbox.count() > 0:
                            await checkbox.click(timeout=5000)
                            await asyncio.sleep(3)
                            
                            # Check if solved
                            new_title = await page.title()
                            if "just a moment" not in new_title.lower():
                                return True
                        break
            except Exception:
                pass
            
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


class InteractionTools:
    """Tools for interactive browser automation with Cloudflare bypass support."""

    def __init__(self, server: ScraplingMCPServer):
        self.server = server
        self._pages: dict[str, Any] = {}  # session_id -> Playwright Page
        self._cloudflare_sessions: dict[str, CloudflareBypassSession] = {}  # session_id -> wrapper

    async def open_session_with_bypass(
        self,
        session_id: str,
        headless: bool = True,
        solve_cloudflare: bool = True,
        hide_canvas: bool = True,
        block_webrtc: bool = True,
        allow_webgl: bool = True
    ) -> dict[str, Any]:
        """
        Open a stealthy session with Cloudflare bypass capabilities.
        
        This creates a custom session that can solve Cloudflare challenges
        while maintaining an open page for interactive use.
        
        :param session_id: Unique identifier for the session
        :param headless: Run browser in headless mode
        :param solve_cloudflare: Automatically solve Cloudflare challenges
        :param hide_canvas: Add random noise to canvas operations
        :param block_webrtc: Block WebRTC to prevent IP leaks
        :param allow_webgl: Allow WebGL rendering
        :return: Dict with session info
        """
        if session_id in self._cloudflare_sessions:
            raise ValueError(f"Session '{session_id}' already exists")
        
        # Create stealthy session with all anti-detection features
        session = AsyncStealthySession(
            headless=headless,
            hide_canvas=hide_canvas,
            block_webrtc=block_webrtc,
            allow_webgl=allow_webgl,
        )
        
        await session.start()
        
        # Wrap it with Cloudflare bypass capabilities
        wrapper = CloudflareBypassSession(
            session=session,
            solve_cloudflare=solve_cloudflare
        )
        
        self._cloudflare_sessions[session_id] = wrapper
        
        return {
            "session_id": session_id,
            "session_type": "stealthy_with_bypass",
            "solve_cloudflare": solve_cloudflare,
            "status": "opened"
        }

    async def _get_page(self, session_id: str) -> Any:
        """Get or create a persistent page for a session."""
        # Check if this is a Cloudflare bypass session
        if session_id in self._cloudflare_sessions:
            wrapper = self._cloudflare_sessions[session_id]
            return await wrapper.get_page(session_id)
        
        # Fall back to official MCP sessions
        if session_id not in self._pages:
            entry = self.server._sessions.get(session_id)
            if not entry:
                raise ValueError(f"Session '{session_id}' not found")
            
            session = entry.session
            if not session.context:
                raise ValueError(f"Session '{session_id}' has no browser context")
            
            page = await session.context.new_page()
            self._pages[session_id] = page
        
        return self._pages[session_id]

    async def browser_navigate(self, session_id: str, url: str) -> dict[str, Any]:
        """
        Navigate to a URL in the browser session.
        
        For sessions created with open_session_with_bypass, automatically
        solves Cloudflare challenges if detected.
        
        :param session_id: ID of the session to use
        :param url: URL to navigate to
        :return: Dict with final URL, title, and cloudflare_solved status
        """
        page = await self._get_page(session_id)
        
        # Navigate to the URL
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Check if this is a Cloudflare bypass session
        cloudflare_solved = False
        if session_id in self._cloudflare_sessions:
            wrapper = self._cloudflare_sessions[session_id]
            if wrapper.solve_cloudflare:
                # Check if we're on a Cloudflare challenge page
                title = await page.title()
                if "just a moment" in title.lower() or "attention required" in title.lower():
                    cloudflare_solved = await wrapper.solve_cloudflare_challenge(page)
                    
                    # Wait for stability after solving
                    if cloudflare_solved:
                        await page.wait_for_load_state("networkidle", timeout=30000)
        
        return {
            "url": page.url,
            "title": await page.title(),
            "cloudflare_solved": cloudflare_solved
        }

    async def browser_navigate_back(self, session_id: str) -> dict[str, Any]:
        """Go back to the previous page.
        
        :param session_id: ID of the session to use
        :return: Dict with final URL and title
        """
        page = await self._get_page(session_id)
        await page.go_back(wait_until="networkidle")
        
        return {
            "url": page.url,
            "title": await page.title(),
        }

    async def browser_click(self, session_id: str, selector: str) -> dict[str, str]:
        """Click an element.
        
        :param session_id: ID of the session to use
        :param selector: CSS selector of the element to click
        :return: Dict with status
        """
        page = await self._get_page(session_id)
        await page.click(selector)
        return {"status": "clicked", "selector": selector}

    async def browser_type(self, session_id: str, selector: str, text: str) -> dict[str, str]:
        """Type text into an input field.
        
        :param session_id: ID of the session to use
        :param selector: CSS selector of the input field
        :param text: Text to type
        :return: Dict with status
        """
        page = await self._get_page(session_id)
        await page.fill(selector, text)
        return {"status": "typed", "selector": selector, "length": str(len(text))}

    async def browser_press_key(self, session_id: str, key: str) -> dict[str, str]:
        """Press a keyboard key.
        
        :param session_id: ID of the session to use
        :param key: Key to press (e.g., 'Enter', 'Tab', 'Escape')
        :return: Dict with status
        """
        page = await self._get_page(session_id)
        await page.keyboard.press(key)
        return {"status": "pressed", "key": key}

    async def browser_hover(self, session_id: str, selector: str) -> dict[str, str]:
        """Hover over an element.
        
        :param session_id: ID of the session to use
        :param selector: CSS selector of the element to hover
        :return: Dict with status
        """
        page = await self._get_page(session_id)
        await page.hover(selector)
        return {"status": "hovered", "selector": selector}

    async def browser_select_option(self, session_id: str, selector: str, value: str) -> dict[str, str]:
        """Select an option from a dropdown.
        
        :param session_id: ID of the session to use
        :param selector: CSS selector of the select element
        :param value: Value of the option to select
        :return: Dict with status
        """
        page = await self._get_page(session_id)
        await page.select_option(selector, value)
        return {"status": "selected", "selector": selector, "value": value}

    async def browser_evaluate(self, session_id: str, expression: str) -> Any:
        """Execute JavaScript and return the result.
        
        :param session_id: ID of the session to use
        :param expression: JavaScript expression to evaluate
        :return: Result of the evaluation
        """
        page = await self._get_page(session_id)
        return await page.evaluate(expression)

    async def browser_wait(self, session_id: str, milliseconds: int = 1000) -> dict[str, str]:
        """Wait for a specified time.
        
        :param session_id: ID of the session to use
        :param milliseconds: Time to wait in milliseconds
        :return: Dict with status
        """
        page = await self._get_page(session_id)
        await page.wait_for_timeout(milliseconds)
        return {"status": "waited", "milliseconds": str(milliseconds)}

    async def browser_snapshot(self, session_id: str) -> dict[str, Any]:
        """Get a snapshot of the current page.
        
        :param session_id: ID of the session to use
        :return: Dict with URL, title, and text content
        """
        page = await self._get_page(session_id)
        
        return {
            "url": page.url,
            "title": await page.title(),
            "content": await page.content(),
        }

    async def close_session_with_bypass(self, session_id: str) -> dict[str, str]:
        """
        Close a session created with open_session_with_bypass.
        
        :param session_id: ID of the session to close
        :return: Dict with status
        """
        if session_id not in self._cloudflare_sessions:
            raise ValueError(f"Session '{session_id}' not found or not a bypass session")
        
        wrapper = self._cloudflare_sessions[session_id]
        await wrapper.close()
        del self._cloudflare_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": "closed"
        }
