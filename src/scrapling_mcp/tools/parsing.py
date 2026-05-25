from __future__ import annotations

import re
from typing import Any, Optional

from scrapling.core.ai import ScraplingMCPServer
from scrapling.parser import Selector


class ParsingTools:
    def __init__(self, official_server: ScraplingMCPServer):
        self._server = official_server
        self._last_page: Optional[Selector] = None

    def _get_page(self) -> Selector:
        if self._last_page is None:
            raise ValueError("No page loaded. Use parse_raw_html first or use a fetch tool.")
        return self._last_page

    async def parse_raw_html(self, html: str) -> dict[str, Any]:
        """Parse raw HTML content directly without fetching. Use this when you already have HTML to parse.
        After parsing, you can use css, xpath, find, and other parsing tools.
        
        :param html: Raw HTML string to parse.
        """
        self._last_page = Selector(html)
        return {
            "status": "parsed",
            "content_length": len(html),
        }

    async def css(self, selector: str, limit: int = 0) -> list[dict[str, Any]]:
        """Find elements using CSS selectors. The most powerful and precise selection method.
        Examples: '.product-title', 'div.price', 'a[href*="/product"]', 'ul > li:first-child'
        Set limit > 0 to restrict number of results.
        
        :param selector: CSS selector to find elements.
        :param limit: Maximum number of results to return. 0 means no limit.
        """
        page = self._get_page()
        elements = page.css(selector)
        if limit > 0:
            elements = elements[:limit]

        results = []
        for el in elements:
            results.append({
                "tag": el.tag,
                "text": el.text or "",
                "html": el.html_content[:500] if el.html_content else "",
                "attrib": dict(el.attrib) if el.attrib else {},
                "css_selector": el.generate_css_selector if hasattr(el, "generate_css_selector") else "",
            })
        return results

    async def xpath(self, query: str, limit: int = 0) -> list[dict[str, Any]]:
        """Find elements using XPath expressions.
        Examples: '//div[@class="product"]', '//a[contains(@href, "product")]', '//h1/text()'
        Set limit > 0 to restrict number of results.
        
        :param query: XPath expression to find elements.
        :param limit: Maximum number of results to return. 0 means no limit.
        """
        page = self._get_page()
        elements = page.xpath(query)
        if limit > 0:
            elements = elements[:limit]

        results = []
        for el in elements:
            results.append({
                "tag": el.tag,
                "text": el.text or "",
                "html": el.html_content[:500] if el.html_content else "",
                "attrib": dict(el.attrib) if el.attrib else {},
            })
        return results

    async def find(
        self,
        tag: Optional[str] = None,
        text_regex: Optional[str] = None,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Find elements by tag name and/or text content regex.
        BeautifulSoup-style selection. Good for simple element lookups.
        
        :param tag: HTML tag name to filter by (e.g., 'div', 'a', 'h1').
        :param text_regex: Regex pattern to match element text content.
        :param limit: Maximum number of results to return. 0 means no limit.
        """
        page = self._get_page()

        if text_regex:
            elements = page.find_all(tag or "*", re.compile(text_regex))
        elif tag:
            elements = page.find_all(tag)
        else:
            elements = page.find_all()

        if limit > 0:
            elements = elements[:limit]

        results = []
        for el in elements:
            results.append({
                "tag": el.tag,
                "text": el.text or "",
                "html": el.html_content[:500] if el.html_content else "",
                "attrib": dict(el.attrib) if el.attrib else {},
            })
        return results

    async def find_text(
        self,
        text: str,
        tag: Optional[str] = None,
        first_match: bool = True,
    ) -> Any:
        """Find elements by exact text content match. Optionally filter by tag name.
        
        :param text: Exact text to search for.
        :param tag: Optional HTML tag to filter results.
        :param first_match: If True, return only the first match. If False, return all matches.
        """
        page = self._get_page()

        kwargs: dict[str, Any] = {"first_match": first_match}
        if tag:
            kwargs["tag"] = tag

        result = page.find_by_text(text, **kwargs)

        if first_match and result is not None:
            return {
                "tag": result.tag,
                "text": result.text or "",
                "html": result.html_content[:500] if result.html_content else "",
                "attrib": dict(result.attrib) if result.attrib else {},
            }
        elif isinstance(result, list):
            return [
                {
                    "tag": el.tag,
                    "text": el.text or "",
                    "html": el.html_content[:500] if el.html_content else "",
                    "attrib": dict(el.attrib) if el.attrib else {},
                }
                for el in result
            ]
        return []

    async def find_regex(
        self,
        pattern: str,
        first_match: bool = False,
    ) -> Any:
        """Find elements whose text content matches a regex pattern.
        
        :param pattern: Regex pattern to match against element text.
        :param first_match: If True, return only the first match. If False, return all matches.
        """
        page = self._get_page()
        result = page.find_by_regex(pattern, first_match=first_match)

        if first_match and result is not None and not isinstance(result, list):
            return {
                "tag": result.tag,
                "text": result.text or "",
                "html": result.html_content[:500] if result.html_content else "",
            }
        elif isinstance(result, list):
            return [
                {
                    "tag": el.tag,
                    "text": el.text or "",
                    "html": el.html_content[:500] if el.html_content else "",
                }
                for el in result
            ]
        return []

    async def similar(self, css_selector: str) -> list[dict[str, Any]]:
        """Find elements similar to the one matching the CSS selector.
        Uses Scrapling's intelligent similarity algorithms to find structurally similar elements.
        Great for finding repeated patterns like product cards, list items, etc.
        
        :param css_selector: CSS selector of the reference element to find similar elements for.
        """
        page = self._get_page()
        target = page.css(css_selector)
        if not target:
            raise ValueError(f"No element found for selector: {css_selector}")

        similar_elements = target[0].find_similar()
        return [
            {
                "tag": el.tag,
                "text": el.text or "",
                "html": el.html_content[:500] if el.html_content else "",
                "attrib": dict(el.attrib) if el.attrib else {},
            }
            for el in similar_elements
        ]
