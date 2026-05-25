from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from scrapling.fetchers import (
    AsyncFetcher,
    DynamicFetcher,
    Fetcher,
    StealthyFetcher,
)
from scrapling.parser import Selector


class SessionType(str, Enum):
    DYNAMIC = "dynamic"
    STEALTHY = "stealthy"


@dataclass
class BrowserSession:
    session_id: str
    session_type: SessionType
    page: Any = None
    browser: Any = None
    context: Any = None
    current_url: str | None = None
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class BrowserManager:
    def __init__(self) -> None:
        self._sessions: dict[str, BrowserSession] = {}
        self._last_page: Selector | None = None
        self._last_url: str | None = None

    @property
    def last_page(self) -> Selector | None:
        return self._last_page

    @last_page.setter
    def last_page(self, value: Selector | None) -> None:
        self._last_page = value

    @property
    def last_url(self) -> str | None:
        return self._last_url

    @last_url.setter
    def last_url(self, value: str | None) -> None:
        self._last_url = value

    def get_session(self, session_id: str) -> BrowserSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "session_type": s.session_type.value,
                "current_url": s.current_url,
            }
            for s in self._sessions.values()
        ]

    def add_session(self, session: BrowserSession) -> None:
        self._sessions[session.session_id] = session

    def remove_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def generate_session_id(self) -> str:
        return uuid.uuid4().hex[:12]

    async def close_all(self) -> None:
        for session in list(self._sessions.values()):
            await self._close_session(session)
        self._sessions.clear()

    async def _close_session(self, session: BrowserSession) -> None:
        try:
            if session.page:
                await session.page.close()
            if session.context:
                await session.context.close()
            if session.browser:
                await session.browser.close()
        except Exception:
            pass


manager = BrowserManager()
