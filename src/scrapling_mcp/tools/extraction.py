from __future__ import annotations

from typing import Any

from scrapling_mcp.browser import manager


async def extract_text(
    css_selector: str | None = None,
    ignore_tags: tuple[str, ...] = ("script", "style"),
) -> str:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    if css_selector:
        elements = page.css(css_selector)
        if not elements:
            return ""
        texts = []
        for el in elements:
            text = el.get_all_text(ignore_tags=ignore_tags) if hasattr(el, "get_all_text") else (el.text or "")
            texts.append(text)
        return "\n---\n".join(texts)

    return page.get_all_text(ignore_tags=ignore_tags) if hasattr(page, "get_all_text") else (page.text or "")


async def extract_html(
    css_selector: str | None = None,
) -> str:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    if css_selector:
        elements = page.css(css_selector)
        if not elements:
            return ""
        return "\n".join(el.html_content for el in elements if el.html_content)

    return page.html_content or ""


async def extract_markdown(
    css_selector: str | None = None,
    main_content_only: bool = True,
) -> str:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    target = page
    if css_selector:
        elements = page.css(css_selector)
        if not elements:
            return ""
        target = elements[0] if len(elements) == 1 else elements

    if main_content_only and hasattr(page, "find"):
        main = page.find("main") or page.find("article") or page.find('[role="main"]')
        if main and not css_selector:
            target = main

    html = target.html_content if hasattr(target, "html_content") else str(target)
    return _html_to_markdown(html)


async def extract_links(
    css_selector: str | None = None,
    absolute: bool = True,
) -> list[dict[str, str]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    selector = f"{css_selector} a" if css_selector else "a"
    elements = page.css(selector)

    base_url = manager.last_url or ""
    links = []
    for el in elements:
        href = el.attrib.get("href", "")
        text = el.text or ""
        if absolute and href and not href.startswith(("http", "//", "#", "mailto:")):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        links.append({"href": href, "text": text.strip()})

    return links


async def extract_table(
    css_selector: str = "table",
) -> list[list[dict[str, str]]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    tables = page.css(css_selector)
    if not tables:
        return []

    all_tables = []
    for table in tables:
        rows = []
        for tr in table.css("tr"):
            cells = []
            for td in tr.css("td, th"):
                cells.append({"text": (td.text or "").strip(), "tag": td.tag})
            if cells:
                rows.append(cells)
        all_tables.append(rows)

    return all_tables


async def extract_attributes(
    css_selector: str,
    attributes: list[str] | None = None,
) -> list[dict[str, str]]:
    page = manager.last_page
    if page is None:
        raise ValueError("No page loaded. Use a fetch tool first.")

    elements = page.css(css_selector)
    results = []
    for el in elements:
        if attributes:
            data = {attr: el.attrib.get(attr, "") for attr in attributes if attr in el.attrib}
        else:
            data = dict(el.attrib) if el.attrib else {}
        data["_tag"] = el.tag
        data["_text"] = (el.text or "").strip()
        results.append(data)

    return results


def _html_to_markdown(html: str) -> str:
    try:
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        return h.handle(html)
    except ImportError:
        import re
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"<p[^>]*>", "\n\n", text)
        text = re.sub(r"</p>", "", text)
        text = re.sub(r"<h(\d)[^>]*>(.*?)</h\1>", lambda m: f"\n{'#' * int(m.group(1))} {m.group(2)}\n", text)
        text = re.sub(r"<li[^>]*>", "\n- ", text)
        text = re.sub(r"<a[^>]*href=\"([^\"]*)\"[^>]*>(.*?)</a>", r"[\2](\1)", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
