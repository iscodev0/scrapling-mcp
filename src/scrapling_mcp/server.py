from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from scrapling.core.ai import ScraplingMCPServer

from scrapling_mcp.tools.interaction import InteractionTools
from scrapling_mcp.tools.parsing import ParsingTools

mcp = FastMCP(
    "ScraplingMCP",
    instructions=(
        "Scrapling MCP Server (Extended) provides web scraping and browser automation tools. "
        "This extends the official Scrapling MCP with interactive browser tools (click, type, navigate, evaluate JS). "
        "Use fetch tools to load pages, parsing tools to find elements, "
        "and interaction tools for browser automation. "
        "Use CSS selectors to narrow down content and save tokens."
    ),
)

# Inicializar el servidor oficial de Scrapling
_official_server = ScraplingMCPServer()

# Registrar todas las herramientas oficiales del MCP de Scrapling
# HTTP tools
mcp.add_tool(_official_server.get, title="get", description=_official_server.get.__doc__, structured_output=True)
mcp.add_tool(_official_server.bulk_get, title="bulk_get", description=_official_server.bulk_get.__doc__, structured_output=True)

# Dynamic browser tools
mcp.add_tool(_official_server.fetch, title="fetch", description=_official_server.fetch.__doc__, structured_output=True)
mcp.add_tool(_official_server.bulk_fetch, title="bulk_fetch", description=_official_server.bulk_fetch.__doc__, structured_output=True)

# Stealthy browser tools
mcp.add_tool(_official_server.stealthy_fetch, title="stealthy_fetch", description=_official_server.stealthy_fetch.__doc__, structured_output=True)
mcp.add_tool(_official_server.bulk_stealthy_fetch, title="bulk_stealthy_fetch", description=_official_server.bulk_stealthy_fetch.__doc__, structured_output=True)

# Session management tools
mcp.add_tool(_official_server.open_session, title="open_session", structured_output=True)
mcp.add_tool(_official_server.close_session, title="close_session", structured_output=True)
mcp.add_tool(_official_server.list_sessions, title="list_sessions", structured_output=True)

# Screenshot tool (oficial, devuelve ImageContent nativo)
mcp.add_tool(_official_server.screenshot, title="screenshot", description=_official_server.screenshot.__doc__)

# Inicializar herramientas interactivas y de parsing
_interaction_tools = InteractionTools(_official_server)
_parsing_tools = ParsingTools(_official_server)

# ── Interactive Browser Tools (EXTENDED - not in official Scrapling MCP) ────

mcp.add_tool(
    _interaction_tools.browser_navigate,
    title="browser_navigate",
    description=_interaction_tools.browser_navigate.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_navigate_back,
    title="browser_navigate_back",
    description=_interaction_tools.browser_navigate_back.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_click,
    title="browser_click",
    description=_interaction_tools.browser_click.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_type,
    title="browser_type",
    description=_interaction_tools.browser_type.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_press_key,
    title="browser_press_key",
    description=_interaction_tools.browser_press_key.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_hover,
    title="browser_hover",
    description=_interaction_tools.browser_hover.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_select_option,
    title="browser_select_option",
    description=_interaction_tools.browser_select_option.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_evaluate,
    title="browser_evaluate",
    description=_interaction_tools.browser_evaluate.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_wait,
    title="browser_wait",
    description=_interaction_tools.browser_wait.__doc__,
)
mcp.add_tool(
    _interaction_tools.browser_snapshot,
    title="browser_snapshot",
    description=_interaction_tools.browser_snapshot.__doc__,
)

# ── Parsing Tools (EXTENDED - not in official Scrapling MCP) ────────────────

mcp.add_tool(
    _parsing_tools.parse_raw_html,
    title="parse_raw_html",
    description=_parsing_tools.parse_raw_html.__doc__,
)
mcp.add_tool(
    _parsing_tools.css,
    title="css",
    description=_parsing_tools.css.__doc__,
)
mcp.add_tool(
    _parsing_tools.xpath,
    title="xpath",
    description=_parsing_tools.xpath.__doc__,
)
mcp.add_tool(
    _parsing_tools.find,
    title="find",
    description=_parsing_tools.find.__doc__,
)
mcp.add_tool(
    _parsing_tools.find_text,
    title="find_text",
    description=_parsing_tools.find_text.__doc__,
)
mcp.add_tool(
    _parsing_tools.find_regex,
    title="find_regex",
    description=_parsing_tools.find_regex.__doc__,
)
mcp.add_tool(
    _parsing_tools.similar,
    title="similar",
    description=_parsing_tools.similar.__doc__,
)
