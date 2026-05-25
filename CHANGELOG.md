# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-25

### Added
- Initial release of scrapling-mcp server
- 31 MCP tools organized in 4 groups:
  - **Fetching (4)**: `get`, `fetch`, `stealthy_fetch`, `bulk_get`
  - **Parsing (7)**: `css`, `xpath`, `find`, `find_text`, `find_regex`, `similar`, `parse_raw_html`
  - **Extraction (6)**: `get_text`, `get_html`, `get_markdown`, `get_links`, `get_tables`, `get_attributes`
  - **Interaction (14)**: `browser_open_session`, `browser_close_session`, `browser_list_sessions`, `browser_navigate`, `browser_navigate_back`, `browser_click`, `browser_type`, `browser_press_key`, `browser_hover`, `browser_select_option`, `browser_evaluate`, `browser_screenshot`, `browser_wait`, `browser_snapshot`
- Support for stdio and HTTP transports
- Anti-bot bypass with Cloudflare Turnstile/Interstitial support
- Persistent browser session management
- CSS pre-filtering for token-efficient AI interactions
- Adaptive element tracking using Scrapling's intelligent algorithms
- CLI tool `scrapling-mcp` for easy deployment
- Integration with opencode, Claude Desktop, Cursor, and other MCP clients
