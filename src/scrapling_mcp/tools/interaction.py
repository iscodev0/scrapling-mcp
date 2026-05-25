from __future__ import annotations

import base64
from typing import Any, Optional

from scrapling.core.ai import ScraplingMCPServer
from scrapling.parser import Selector


class InteractionTools:
    def __init__(self, official_server: ScraplingMCPServer):
        self._server = official_server
        self._pages: dict[str, Any] = {}

    async def _get_page(self, session_id: str) -> Any:
        entry = self._server._get_session(session_id, expected_type=None)
        
        if session_id not in self._pages:
            async def capture_page(page: Any) -> None:
                self._pages[session_id] = page
            
            await entry.session.fetch(
                "about:blank",
                page_action=capture_page,
                timeout=5000,
            )
        
        page = self._pages.get(session_id)
        if page is None:
            raise ValueError(f"Failed to capture page for session '{session_id}'")
        
        return page

    async def browser_navigate(
        self,
        url: str,
        session_id: str,
        wait_until: str = "networkidle",
        timeout: int = 30000,
    ) -> dict[str, Any]:
        """Navigate to a URL in an existing browser session.
        Use this for interactive browsing workflows where you need to click, type, or interact with pages.
        
        :param url: The URL to navigate to.
        :param session_id: ID of an open browser session from open_session.
        :param wait_until: When to consider navigation complete. One of: "load", "domcontentloaded", "networkidle", "commit".
        :param timeout: Timeout in milliseconds for navigation.
        """
        page = await self._get_page(session_id)
        await page.goto(url, wait_until=wait_until, timeout=timeout)
        
        title = await page.title()
        current_url = page.url
        
        return {
            "url": current_url,
            "title": title,
            "status": "navigated",
        }

    async def browser_navigate_back(self, session_id: str) -> dict[str, str]:
        """Go back to the previous page in browser history.
        
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)
        await page.go_back()
        return {"url": page.url, "status": "navigated_back"}

    async def browser_click(
        self,
        selector: str,
        session_id: str,
        timeout: int = 5000,
    ) -> dict[str, str]:
        """Click an element in the browser. Use CSS selectors to target the element.
        
        :param selector: CSS selector for the element to click.
        :param session_id: ID of an open browser session from open_session.
        :param timeout: Timeout in milliseconds to wait for the element.
        """
        page = await self._get_page(session_id)
        await page.click(selector, timeout=timeout)
        return {"selector": selector, "status": "clicked"}

    async def browser_type(
        self,
        selector: str,
        text: str,
        session_id: str,
        delay: int = 0,
    ) -> dict[str, str]:
        """Type text into an input element in the browser. Clears existing content first.
        
        :param selector: CSS selector for the input element.
        :param text: Text to type into the element.
        :param session_id: ID of an open browser session from open_session.
        :param delay: Delay in milliseconds between keystrokes.
        """
        page = await self._get_page(session_id)
        await page.fill(selector, text, delay=delay)
        return {"selector": selector, "status": "typed", "length": str(len(text))}

    async def browser_press_key(self, key: str, session_id: str) -> dict[str, str]:
        """Press a keyboard key. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', 'Control+a'.
        
        :param key: Key to press (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown').
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)
        await page.keyboard.press(key)
        return {"key": key, "status": "pressed"}

    async def browser_hover(self, selector: str, session_id: str) -> dict[str, str]:
        """Hover over an element in the browser. Useful for triggering hover-based menus/tooltips.
        
        :param selector: CSS selector for the element to hover over.
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)
        await page.hover(selector)
        return {"selector": selector, "status": "hovered"}

    async def browser_select_option(
        self,
        selector: str,
        value: str,
        session_id: str,
    ) -> dict[str, str]:
        """Select an option from a dropdown/select element by its value attribute.
        
        :param selector: CSS selector for the select element.
        :param value: Value attribute of the option to select.
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)
        await page.select_option(selector, value)
        return {"selector": selector, "value": value, "status": "selected"}

    async def browser_evaluate(
        self,
        expression: str,
        session_id: str,
    ) -> Any:
        """Evaluate a JavaScript expression in the browser context. Returns the result.
        
        :param expression: JavaScript expression to evaluate.
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)
        result = await page.evaluate(expression)
        return result

    async def browser_wait(
        self,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        timeout: int = 30000,
        session_id: str = None,
    ) -> dict[str, str]:
        """Wait for an element (by CSS selector) or text to appear on the page.
        
        :param selector: CSS selector to wait for.
        :param text: Text to wait for in the page body.
        :param timeout: Timeout in milliseconds.
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)

        if selector:
            await page.wait_for_selector(selector, timeout=timeout)
            return {"selector": selector, "status": "found"}
        elif text:
            await page.wait_for_function(
                f"document.body.innerText.includes('{text}')",
                timeout=timeout,
            )
            return {"text": text, "status": "found"}
        else:
            import asyncio
            await asyncio.sleep(timeout / 1000)
            return {"status": "waited", "ms": str(timeout)}

    async def browser_snapshot(self, session_id: str) -> dict[str, Any]:
        """Get a structured snapshot of the current browser page: URL, title, text content.
        Also loads the page into the parser so you can use CSS/XPath/extraction tools on it.
        
        :param session_id: ID of an open browser session from open_session.
        """
        page = await self._get_page(session_id)
        
        html = await page.content()
        parsed = Selector(html)
        
        title = await page.title()
        url = page.url

        text = parsed.get_all_text(ignore_tags=("script", "style")) if hasattr(parsed, "get_all_text") else ""

        return {
            "url": url,
            "title": title,
            "text_content": text[:5000],
            "html_length": len(html),
        }
