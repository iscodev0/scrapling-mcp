from __future__ import annotations

import asyncio
from typing import Any

from scrapling.fetchers import AsyncFetcher, DynamicFetcher, Fetcher, StealthyFetcher
from scrapling.parser import Selector

from scrapling_mcp.browser import manager


async def scrapling_get(
    url: str,
    impersonate: str = "chrome",
    stealthy_headers: bool = True,
    proxy: str | None = None,
    timeout: int = 30,
    http3: bool = False,
) -> dict[str, Any]:
    try:
        page = await asyncio.to_thread(
            Fetcher.get,
            url,
            impersonate=impersonate,
            stealthy_headers=stealthy_headers,
            proxy=proxy,
            timeout=timeout,
            http3=http3,
        )
        manager.last_page = page
        manager.last_url = url
        return {
            "status": page.status if hasattr(page, "status") else 200,
            "url": url,
            "content_length": len(page.html_content) if hasattr(page, "html_content") else 0,
        }
    except Exception as e:
        return {"error": str(e), "url": url}


async def scrapling_fetch(
    url: str,
    headless: bool = True,
    disable_resources: bool = False,
    block_ads: bool = True,
    network_idle: bool = True,
    timeout: int = 30000,
    wait_selector: str | None = None,
) -> dict[str, Any]:
    try:
        page = await asyncio.to_thread(
            DynamicFetcher.fetch,
            url,
            headless=headless,
            disable_resources=disable_resources,
            block_ads=block_ads,
            network_idle=network_idle,
            timeout=timeout,
        )
        manager.last_page = page
        manager.last_url = url
        return {
            "status": page.status if hasattr(page, "status") else 200,
            "url": url,
            "content_length": len(page.html_content) if hasattr(page, "html_content") else 0,
        }
    except Exception as e:
        return {"error": str(e), "url": url}


async def scrapling_stealthy_fetch(
    url: str,
    headless: bool = True,
    solve_cloudflare: bool = True,
    block_ads: bool = True,
    network_idle: bool = True,
    timeout: int = 30000,
    block_webrtc: bool = False,
    hide_canvas: bool = False,
) -> dict[str, Any]:
    try:
        page = await asyncio.to_thread(
            StealthyFetcher.fetch,
            url,
            headless=headless,
            solve_cloudflare=solve_cloudflare,
            block_ads=block_ads,
            network_idle=network_idle,
            timeout=timeout,
            block_webrtc=block_webrtc,
            hide_canvas=hide_canvas,
        )
        manager.last_page = page
        manager.last_url = url
        return {
            "status": page.status if hasattr(page, "status") else 200,
            "url": url,
            "content_length": len(page.html_content) if hasattr(page, "html_content") else 0,
        }
    except Exception as e:
        return {"error": str(e), "url": url}


async def scrapling_bulk_get(
    urls: list[str],
    impersonate: str = "chrome",
    stealthy_headers: bool = True,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    async def _fetch_one(url: str) -> dict[str, Any]:
        try:
            page = await AsyncFetcher.get(
                url,
                impersonate=impersonate,
                stealthy_headers=stealthy_headers,
                timeout=timeout,
            )
            return {
                "url": url,
                "status": page.status if hasattr(page, "status") else 200,
                "content_length": len(page.html_content) if hasattr(page, "html_content") else 0,
            }
        except Exception as e:
            return {"url": url, "error": str(e)}

    return await asyncio.gather(*[_fetch_one(u) for u in urls])
