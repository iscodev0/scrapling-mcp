from __future__ import annotations

import asyncio
import base64
from typing import Any

from scrapling_mcp.browser import BrowserSession, SessionType, manager


async def open_session(
    session_type: str = "dynamic",
    session_id: str | None = None,
    headless: bool = True,
) -> dict[str, str]:
    from playwright.async_api import async_playwright

    sid = session_id or manager.generate_session_id()
    if manager.get_session(sid):
        raise ValueError(f"Session '{sid}' already exists.")

    stype = SessionType(session_type)

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()

    session = BrowserSession(
        session_id=sid,
        session_type=stype,
        page=page,
        browser=browser,
        context=context,
    )
    manager.add_session(session)

    return {"session_id": sid, "session_type": stype.value, "status": "opened"}


async def close_session(session_id: str) -> dict[str, str]:
    session = manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found.")

    await manager._close_session(session)
    manager.remove_session(session_id)
    return {"session_id": session_id, "status": "closed"}


async def list_sessions() -> list[dict[str, Any]]:
    return manager.list_sessions()


async def navigate(
    url: str,
    session_id: str | None = None,
    wait_until: str = "networkidle",
    timeout: int = 30000,
) -> dict[str, Any]:
    session = _get_or_create_default_session(session_id)
    page = session.page

    await page.goto(url, wait_until=wait_until, timeout=timeout)
    session.current_url = url
    manager.last_url = url

    title = await page.title()
    return {"url": url, "title": title, "status": "navigated"}


async def navigate_back(session_id: str | None = None) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)
    await session.page.go_back()
    url = session.page.url
    session.current_url = url
    return {"url": url, "status": "navigated_back"}


async def click(
    selector: str,
    session_id: str | None = None,
    timeout: int = 5000,
) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)
    await session.page.click(selector, timeout=timeout)
    return {"selector": selector, "status": "clicked"}


async def type_text(
    selector: str,
    text: str,
    session_id: str | None = None,
    delay: int = 0,
) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)
    await session.page.fill(selector, text, delay=delay)
    return {"selector": selector, "status": "typed", "length": str(len(text))}


async def press_key(
    key: str,
    session_id: str | None = None,
) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)
    await session.page.keyboard.press(key)
    return {"key": key, "status": "pressed"}


async def hover(
    selector: str,
    session_id: str | None = None,
) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)
    await session.page.hover(selector)
    return {"selector": selector, "status": "hovered"}


async def select_option(
    selector: str,
    value: str,
    session_id: str | None = None,
) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)
    await session.page.select_option(selector, value)
    return {"selector": selector, "value": value, "status": "selected"}


async def evaluate_js(
    expression: str,
    session_id: str | None = None,
) -> Any:
    session = _get_or_create_default_session(session_id)
    result = await session.page.evaluate(expression)
    return result


async def take_screenshot(
    session_id: str | None = None,
    full_page: bool = False,
    image_type: str = "png",
    quality: int = 80,
) -> dict[str, Any]:
    session = _get_or_create_default_session(session_id)

    kwargs: dict[str, Any] = {"full_page": full_page, "type": image_type}
    if image_type == "jpeg":
        kwargs["quality"] = quality

    screenshot_bytes = await session.page.screenshot(**kwargs)
    b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

    return {
        "type": "image",
        "data": b64,
        "mime_type": f"image/{image_type}",
        "full_page": full_page,
    }


async def wait_for(
    selector: str | None = None,
    text: str | None = None,
    timeout: int = 30000,
    session_id: str | None = None,
) -> dict[str, str]:
    session = _get_or_create_default_session(session_id)

    if selector:
        await session.page.wait_for_selector(selector, timeout=timeout)
        return {"selector": selector, "status": "found"}
    elif text:
        await session.page.wait_for_function(
            f"document.body.innerText.includes('{text}')",
            timeout=timeout,
        )
        return {"text": text, "status": "found"}
    else:
        await asyncio.sleep(timeout / 1000)
        return {"status": "waited", "ms": str(timeout)}


async def get_page_snapshot(session_id: str | None = None) -> dict[str, Any]:
    session = _get_or_create_default_session(session_id)
    page_obj = session.page

    from scrapling.parser import Selector

    html = await page_obj.content()
    parsed = Selector(html)
    manager.last_page = parsed
    manager.last_url = page_obj.url

    title = await page_obj.title()
    url = page_obj.url

    text = parsed.get_all_text(ignore_tags=("script", "style")) if hasattr(parsed, "get_all_text") else ""

    return {
        "url": url,
        "title": title,
        "text_content": text[:5000],
        "html_length": len(html),
    }


def _get_or_create_default_session(session_id: str | None) -> BrowserSession:
    if session_id:
        session = manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")
        return session

    sessions = manager.list_sessions()
    if sessions:
        return manager.get_session(sessions[0]["session_id"])

    raise ValueError("No browser session active. Use open_session first or pass a session_id.")
