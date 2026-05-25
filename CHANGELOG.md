# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-05-25

### Added
- **Cloudflare Bypass for Interactive Sessions**: New `open_session_with_bypass` and `close_session_with_bypass` tools
  - Automatically solves Cloudflare Turnstile challenges (both non-interactive and interactive types)
  - Replicates Scrapling's internal `_cloudflare_solver` logic for async browser sessions
  - Includes anti-detection features: canvas noise injection, WebRTC blocking, WebGL support
  - Enables full interactive automation on Cloudflare-protected sites
- Cloudflare challenge detection supporting: non-interactive, managed, interactive, and embedded types
- Turnstile iframe detection and automatic checkbox clicking with randomized coordinates

### Fixed
- Async/await handling in Cloudflare solver (`is_visible()` now properly awaited)
- Frame element interaction for Turnstile challenges

### Changed
- Updated README with Cloudflare Bypass section and usage examples
- Test results: 28/29 tools working (97% success rate)

## [0.2.0] - 2026-05-25

### Changed
- **Major refactor**: Now extends the official Scrapling MCP server instead of reimplementing tools
- All official tools (get, fetch, stealthy_fetch, bulk variants, sessions, screenshot) now delegate to `ScraplingMCPServer` from `scrapling.core.ai`
- Inherits all official features: prompt injection protection, SSRF safe redirects, cookies, auth, retries, google_search, real_chrome, cdp_url, timezone, locale, max_pages, etc.
- Screenshot now returns native `ImageContent` (model sees the image directly, not base64 in JSON)
- Reduced from 31 tools to 27 (removed duplicate extraction tools - official tools already extract content)

### Added
- Interactive browser tools that work with official sessions:
  - `browser_navigate`, `browser_navigate_back`
  - `browser_click`, `browser_type`, `browser_press_key`
  - `browser_hover`, `browser_select_option`
  - `browser_evaluate` (JavaScript execution)
  - `browser_wait`, `browser_snapshot`
- Parsing tools for working with loaded pages:
  - `parse_raw_html`, `css`, `xpath`, `find`
  - `find_text`, `find_regex`, `similar`

### Removed
- Custom fetching tools (get, fetch, stealthy_fetch, bulk_get) - now uses official implementations
- Custom extraction tools (get_text, get_html, get_markdown, get_links, get_tables, get_attributes) - official tools already extract content
- Custom browser.py session manager - now uses official `_sessions` from ScraplingMCPServer

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
