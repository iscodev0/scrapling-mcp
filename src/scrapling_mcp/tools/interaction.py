"""Interactive browser tools that work with Scrapling sessions."""

from typing import Any
from scrapling.core.ai import ScraplingMCPServer


class InteractionTools:
    """Tools for interactive browser automation using Scrapling sessions."""

    def __init__(self, server: ScraplingMCPServer):
        self.server = server
        self._pages: dict[str, Any] = {}  # session_id -> Playwright Page

    async def _get_page(self, session_id: str) -> Any:
        """Get or create a persistent page for a session."""
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

    async def _wait_for_cloudflare(self, page: Any, timeout: int = 30000) -> bool:
        """Wait for Cloudflare challenge to resolve if present."""
        try:
            title = await page.title()
            if "just a moment" in title.lower() or "attention required" in title.lower():
                await page.wait_for_function(
                    "() => !document.title.toLowerCase().includes('just a moment') && !document.title.toLowerCase().includes('attention required')",
                    timeout=timeout
                )
                return True
        except:
            pass
        return False

    async def browser_navigate(self, session_id: str, url: str, solve_cloudflare: bool = True) -> dict[str, Any]:
        """Navigate to a URL in the browser session. Automatically handles Cloudflare challenges for stealthy sessions.
        
        :param session_id: ID of the session to use
        :param url: URL to navigate to
        :param solve_cloudflare: Wait for Cloudflare challenge to resolve (default: True)
        :return: Dict with final URL and title
        """
        page = await self._get_page(session_id)
        await page.goto(url, wait_until="networkidle")
        
        if solve_cloudflare:
            await self._wait_for_cloudflare(page)
        
        return {
            "url": page.url,
            "title": await page.title(),
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
