"""Interactive browser tools with Cloudflare bypass support."""

import asyncio
import re
from random import randint
from typing import Any, Dict, Optional
from scrapling.core.ai import ScraplingMCPServer
from scrapling.fetchers import AsyncStealthySession
from scrapling.parser import Selector

# Cloudflare challenge URL pattern
__CF_PATTERN__ = re.compile(r"^https?://challenges\.cloudflare\.com/cdn-cgi/challenge-platform/.*")


def _detect_cloudflare(page_content: str) -> str | None:
    """
    Detect the type of Cloudflare challenge present in the provided page content.
    """
    challenge_types = (
        "non-interactive",
        "managed",
        "interactive",
    )
    for ctype in challenge_types:
        if f"cType: '{ctype}'" in page_content:
            return ctype

    # Check if turnstile captcha is embedded inside the page
    selector = Selector(content=page_content)
    if selector.css('script[src*="challenges.cloudflare.com/turnstile/v"]'):
        return "embedded"

    return None


async def _get_page_content(page: Any) -> str:
    """Get page content asynchronously."""
    return await page.content()


async def _wait_for_networkidle(page: Any, timeout: int = 5000):
    """Wait for network to be idle."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass


async def _wait_for_page_stability(page: Any, load_dom: bool = True, network_idle: bool = False):
    """Wait for page stability."""
    if load_dom:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
    
    if network_idle:
        await _wait_for_networkidle(page, timeout=5000)


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
    
    async def cloudflare_solver(self, page: Any) -> None:
        """
        Solve the cloudflare challenge displayed on the playwright page.
        Replicates Scrapling's _cloudflare_solver for async use.
        """
        print(f"[DEBUG] Starting Cloudflare solver")
        await _wait_for_networkidle(page, timeout=5000)
        page_content = await _get_page_content(page)
        challenge_type = _detect_cloudflare(page_content)
        print(f"[DEBUG] Detected challenge type: {challenge_type}")
        
        if not challenge_type:
            print(f"[DEBUG] No Cloudflare challenge detected")
            return None
        
        if challenge_type == "non-interactive":
            # Non-interactive challenge: just wait
            print(f"[DEBUG] Non-interactive challenge, waiting...")
            while "<title>Just a moment...</title>" in (await _get_page_content(page)):
                await page.wait_for_timeout(1000)
                await page.wait_for_load_state()
            print(f"[DEBUG] Non-interactive challenge solved")
            return None
        
        else:
            # Interactive challenge: need to click the checkbox
            print(f"[DEBUG] Interactive challenge detected: {challenge_type}")
            box_selector = "#cf_turnstile div, #cf-turnstile div, .turnstile>div>div"
            
            if challenge_type != "embedded":
                box_selector = ".main-content p+div>div>div"
                while "Verifying you are human." in (await _get_page_content(page)):
                    await page.wait_for_timeout(500)
            
            outer_box = {}
            iframe = page.frame(url=__CF_PATTERN__)
            print(f"[DEBUG] Found iframe: {iframe is not None}")
            
            if iframe is not None:
                await _wait_for_page_stability(iframe, True, False)
                
                frame_el = await iframe.frame_element()
                if challenge_type != "embedded":
                    while not await frame_el.is_visible():
                        await page.wait_for_timeout(500)
                
                outer_box = await frame_el.bounding_box()
                print(f"[DEBUG] Got bounding box from iframe: {outer_box}")
            
            if not iframe or not outer_box:
                if "<title>Just a moment...</title>" not in (await _get_page_content(page)):
                    print(f"[DEBUG] Challenge disappeared before clicking")
                    return None
                
                outer_box = await page.locator(box_selector).last.bounding_box()
                print(f"[DEBUG] Got bounding box from locator: {outer_box}")
            
            # Calculate the Captcha coordinates
            captcha_x = outer_box["x"] + randint(26, 28)
            captcha_y = outer_box["y"] + randint(25, 27)
            print(f"[DEBUG] Clicking at coordinates: ({captcha_x}, {captcha_y})")
            
            # Click the captcha
            await page.mouse.click(captcha_x, captcha_y, delay=randint(100, 200), button="left")
            await _wait_for_networkidle(page)
            
            if challenge_type != "embedded":
                attempts = 0
                while "<title>Just a moment...</title>" in (await _get_page_content(page)):
                    if attempts >= 100:
                        print(f"[DEBUG] Timeout waiting for challenge to disappear")
                        break
                    await page.wait_for_timeout(100)
                    attempts += 1
            
            await _wait_for_page_stability(page, True, False)
            
            if "<title>Just a moment...</title>" not in (await _get_page_content(page)):
                print(f"[DEBUG] Challenge solved successfully")
                return None
            else:
                # Recursive call if still present
                print(f"[DEBUG] Challenge still present, retrying...")
                return await self.cloudflare_solver(page)
    
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
                    await wrapper.cloudflare_solver(page)
                    cloudflare_solved = True
                    
                    # Wait for stability after solving
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
