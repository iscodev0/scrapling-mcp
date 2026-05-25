from __future__ import annotations

import re
from typing import Any

from scrapling.parser import Selector

from scrapling_mcp.browser import manager


def _get_page(css_selector: str | None = None) -> Selector:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")
    if css_selector:
        elements = page.css(css_selector)
        if not elements:
            raise ValueError(f"No elements found for selector: {css_selector}")
        return elements
    return page


async def parse_html(html: str) -> dict[str, Any]:
    page = Selector(html)
    manager.last_page = page
    return {
        "status": "parsed",
        "content_length": len(html),
    }


async def css_select(
    selector: str,
    limit: int = 0,
) -> list[dict[str, Any]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

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


async def xpath_select(
    xpath: str,
    limit: int = 0,
) -> list[dict[str, Any]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    elements = page.xpath(xpath)
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


async def find_elements(
    tag: str | None = None,
    attributes: dict[str, str] | None = None,
    text_regex: str | None = None,
    limit: int = 0,
) -> list[dict[str, Any]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    kwargs: dict[str, Any] = {}
    if attributes:
        kwargs.update(attributes)

    if text_regex:
        elements = page.find_all(tag or "*", re.compile(text_regex))
    elif tag:
        elements = page.find_all(tag, **kwargs) if kwargs else page.find_all(tag)
    else:
        elements = page.find_all(**kwargs) if kwargs else page.find_all()

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


async def find_by_text(
    text: str,
    tag: str | None = None,
    first_match: bool = True,
) -> list[dict[str, Any]] | dict[str, Any]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

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


async def find_by_regex(
    pattern: str,
    first_match: bool = False,
) -> list[dict[str, Any]] | dict[str, Any]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

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


async def find_similar(
    css_selector: str,
) -> list[dict[str, Any]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    target = page.css(css_selector)
    if not target:
        raise ValueError(f"No element found for selector: {css_selector}")

    similar = target[0].find_similar()
    return [
        {
            "tag": el.tag,
            "text": el.text or "",
            "html": el.html_content[:500] if el.html_content else "",
            "attrib": dict(el.attrib) if el.attrib else {},
        }
        for el in similar
    ]
