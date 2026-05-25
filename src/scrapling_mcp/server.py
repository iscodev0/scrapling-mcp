from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from scrapling_mcp.tools.extraction import (
    extract_attributes,
    extract_html,
    extract_links,
    extract_markdown,
    extract_table,
    extract_text,
)
from scrapling_mcp.tools.fetching import (
    scrapling_bulk_get,
    scrapling_fetch,
    scrapling_get,
    scrapling_stealthy_fetch,
)
from scrapling_mcp.tools.interaction import (
    click,
    close_session,
    evaluate_js,
    get_page_snapshot,
    hover,
    list_sessions,
    navigate,
    navigate_back,
    open_session,
    press_key,
    select_option,
    take_screenshot,
    type_text,
    wait_for,
)
from scrapling_mcp.tools.parsing import (
    css_select,
    find_by_regex,
    find_by_text,
    find_elements,
    find_similar,
    parse_html,
    xpath_select,
)

mcp = FastMCP(
    "ScraplingMCP",
    instructions=(
        "Scrapling MCP Server provides web scraping and browser automation tools. "
        "Use fetch tools to load pages, parsing tools to find elements, "
        "extraction tools to get content, and interaction tools for browser automation. "
        "Always fetch a page before parsing or extracting. "
        "Use CSS selectors to narrow down content and save tokens."
    ),
)


# ── Fetching Tools ──────────────────────────────────────────────────────────


@mcp.tool()
async def get(
    url: str,
    impersonate: str = "chrome",
    stealthy_headers: bool = True,
    proxy: str | None = None,
    timeout: int = 30,
    http3: bool = False,
) -> dict[str, Any]:
    """Fast HTTP GET request with browser fingerprint impersonation, TLS fingerprinting, and HTTP/3 support.
    Best for: static websites, APIs, simple pages that don't need JavaScript rendering.
    After calling this, use parsing/extraction tools to get the content you need."""
    return await scrapling_get(url, impersonate, stealthy_headers, proxy, timeout, http3)


@mcp.tool()
async def fetch(
    url: str,
    headless: bool = True,
    disable_resources: bool = False,
    block_ads: bool = True,
    network_idle: bool = True,
    timeout: int = 30000,
) -> dict[str, Any]:
    """Fetch a dynamic web page using a Chromium browser via Playwright.
    Best for: SPAs, JavaScript-rendered content, dynamic websites.
    Supports ad blocking and resource disabling for faster loads."""
    return await scrapling_fetch(url, headless, disable_resources, block_ads, network_idle, timeout)


@mcp.tool()
async def stealthy_fetch(
    url: str,
    headless: bool = True,
    solve_cloudflare: bool = True,
    block_ads: bool = True,
    network_idle: bool = True,
    timeout: int = 30000,
    block_webrtc: bool = False,
    hide_canvas: bool = False,
) -> dict[str, Any]:
    """Fetch a web page using a stealth browser that bypasses Cloudflare Turnstile/Interstitial and anti-bot systems.
    Best for: protected websites, Cloudflare-protected pages, sites with bot detection.
    Includes WebRTC leak prevention and canvas fingerprint hiding."""
    return await scrapling_stealthy_fetch(
        url, headless, solve_cloudflare, block_ads, network_idle, timeout, block_webrtc, hide_canvas
    )


@mcp.tool()
async def bulk_get(
    urls: list[str],
    impersonate: str = "chrome",
    stealthy_headers: bool = True,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """Fetch multiple URLs concurrently using async HTTP requests.
    Best for: scraping multiple pages at once, batch data collection.
    Returns results for all URLs in parallel."""
    return await scrapling_bulk_get(urls, impersonate, stealthy_headers, timeout)


# ── Parsing Tools ───────────────────────────────────────────────────────────


@mcp.tool()
async def parse_raw_html(html: str) -> dict[str, Any]:
    """Parse raw HTML content directly without fetching. Use this when you already have HTML to parse."""
    return await parse_html(html)


@mcp.tool()
async def css(selector: str, limit: int = 0) -> list[dict[str, Any]]:
    """Find elements using CSS selectors. The most powerful and precise selection method.
    Examples: '.product-title', 'div.price', 'a[href*="/product"]', 'ul > li:first-child'
    Set limit > 0 to restrict number of results."""
    return await css_select(selector, limit)


@mcp.tool()
async def xpath(query: str, limit: int = 0) -> list[dict[str, Any]]:
    """Find elements using XPath expressions.
    Examples: '//div[@class="product"]', '//a[contains(@href, "product")]', '//h1/text()'
    Set limit > 0 to restrict number of results."""
    return await xpath_select(query, limit)


@mcp.tool()
async def find(
    tag: str | None = None,
    text_regex: str | None = None,
    limit: int = 0,
) -> list[dict[str, Any]]:
    """Find elements by tag name and/or text content regex.
    BeautifulSoup-style selection. Good for simple element lookups."""
    return await find_elements(tag=tag, text_regex=text_regex, limit=limit)


@mcp.tool()
async def find_text(text: str, tag: str | None = None, first_match: bool = True) -> Any:
    """Find elements by exact text content match. Optionally filter by tag name."""
    return await find_by_text(text, tag, first_match)


@mcp.tool()
async def find_regex(pattern: str, first_match: bool = False) -> Any:
    """Find elements whose text content matches a regex pattern."""
    return await find_by_regex(pattern, first_match)


@mcp.tool()
async def similar(css_selector: str) -> list[dict[str, Any]]:
    """Find elements similar to the one matching the CSS selector.
    Uses Scrapling's intelligent similarity algorithms to find structurally similar elements.
    Great for finding repeated patterns like product cards, list items, etc."""
    return await find_similar(css_selector)


# ── Extraction Tools ────────────────────────────────────────────────────────


@mcp.tool()
async def get_text(
    css_selector: str | None = None,
    ignore_tags: str = "script,style",
) -> str:
    """Extract text content from the loaded page. Optionally filter by CSS selector.
    Automatically ignores script and style tags for clean text output."""
    tags = tuple(t.strip() for t in ignore_tags.split(","))
    return await extract_text(css_selector, tags)


@mcp.tool()
async def get_html(css_selector: str | None = None) -> str:
    """Extract raw HTML content from the loaded page or specific elements via CSS selector."""
    return await extract_html(css_selector)


@mcp.tool()
async def get_markdown(
    css_selector: str | None = None,
    main_content_only: bool = True,
) -> str:
    """Extract content as Markdown. The most readable output format for AI consumption.
    When main_content_only=True, tries to find <main>, <article>, or [role='main'] first.
    Use CSS selector to target specific content areas."""
    return await extract_markdown(css_selector, main_content_only)


@mcp.tool()
async def get_links(
    css_selector: str | None = None,
    absolute: bool = True,
) -> list[dict[str, str]]:
    """Extract all links from the page. Optionally filter by CSS selector scope.
    Returns href and text for each link. Converts relative URLs to absolute when possible."""
    return await extract_links(css_selector, absolute)


@mcp.tool()
async def get_tables(css_selector: str = "table") -> list[list[dict[str, str]]]:
    """Extract HTML tables as structured data. Returns rows of cells with text and tag info."""
    return await extract_table(css_selector)


@mcp.tool()
async def get_attributes(
    css_selector: str,
    attributes: list[str] | None = None,
) -> list[dict[str, str]]:
    """Extract specific attributes from elements matching a CSS selector.
    If attributes is None, returns all attributes. Always includes _tag and _text."""
    return await extract_attributes(css_selector, attributes)


# ── Interaction Tools ───────────────────────────────────────────────────────


@mcp.tool()
async def browser_open_session(
    session_type: str = "dynamic",
    session_id: str | None = None,
    headless: bool = True,
) -> dict[str, str]:
    """Open a persistent browser session for interactive automation.
    session_type: 'dynamic' (Chromium) or 'stealthy' (anti-bot).
    The session stays open for multiple interactions. Always close when done."""
    return await open_session(session_type, session_id, headless)


@mcp.tool()
async def browser_close_session(session_id: str) -> dict[str, str]:
    """Close a persistent browser session and free its resources."""
    return await close_session(session_id)


@mcp.tool()
async def browser_list_sessions() -> list[dict[str, Any]]:
    """List all active browser sessions with their details."""
    return await list_sessions()


@mcp.tool()
async def browser_navigate(
    url: str,
    session_id: str | None = None,
    wait_until: str = "networkidle",
    timeout: int = 30000,
) -> dict[str, Any]:
    """Navigate to a URL in the browser session. Use for interactive browsing workflows."""
    return await navigate(url, session_id, wait_until, timeout)


@mcp.tool()
async def browser_navigate_back(session_id: str | None = None) -> dict[str, str]:
    """Go back to the previous page in browser history."""
    return await navigate_back(session_id)


@mcp.tool()
async def browser_click(
    selector: str,
    session_id: str | None = None,
    timeout: int = 5000,
) -> dict[str, str]:
    """Click an element in the browser. Use CSS selectors to target the element."""
    return await click(selector, session_id, timeout)


@mcp.tool()
async def browser_type(
    selector: str,
    text: str,
    session_id: str | None = None,
    delay: int = 0,
) -> dict[str, str]:
    """Type text into an input element in the browser. Clears existing content first."""
    return await type_text(selector, text, session_id, delay)


@mcp.tool()
async def browser_press_key(key: str, session_id: str | None = None) -> dict[str, str]:
    """Press a keyboard key. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', 'Control+a'."""
    return await press_key(key, session_id)


@mcp.tool()
async def browser_hover(selector: str, session_id: str | None = None) -> dict[str, str]:
    """Hover over an element in the browser. Useful for triggering hover-based menus/tooltips."""
    return await hover(selector, session_id)


@mcp.tool()
async def browser_select_option(
    selector: str,
    value: str,
    session_id: str | None = None,
) -> dict[str, str]:
    """Select an option from a dropdown/select element by its value attribute."""
    return await select_option(selector, value, session_id)


@mcp.tool()
async def browser_evaluate(
    expression: str,
    session_id: str | None = None,
) -> Any:
    """Evaluate a JavaScript expression in the browser context. Returns the result."""
    return await evaluate_js(expression, session_id)


@mcp.tool()
async def browser_screenshot(
    session_id: str | None = None,
    full_page: bool = False,
    image_type: str = "png",
    quality: int = 80,
) -> dict[str, Any]:
    """Take a screenshot of the current browser page. Returns base64-encoded image data."""
    return await take_screenshot(session_id, full_page, image_type, quality)


@mcp.tool()
async def browser_wait(
    selector: str | None = None,
    text: str | None = None,
    timeout: int = 30000,
    session_id: str | None = None,
) -> dict[str, str]:
    """Wait for an element (by CSS selector) or text to appear on the page."""
    return await wait_for(selector, text, timeout, session_id)


@mcp.tool()
async def browser_snapshot(session_id: str | None = None) -> dict[str, Any]:
    """Get a structured snapshot of the current browser page: URL, title, text content.
    Also loads the page into the parser so you can use CSS/XPath/extraction tools on it."""
    return await get_page_snapshot(session_id)
