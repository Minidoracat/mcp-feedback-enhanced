# Changelog (English)

This document records all version updates for **MCP Feedback Enhanced**.

## [v2.8.1] - Unreleased - Desktop Fallback Follow-ups

### 🌟 Highlights
- stderr notices are now protected writes and never fall back to stdout (the MCP protocol channel) when `sys.stderr` is None.
- The desktop shell only counts as failed on a non-zero exit, so closing the window yourself no longer demotes the process to web mode; the failure reason is printed for the user.

### 🐛 Bug Fixes
- **Fallback notices now use a protected stderr write**: the two `sys.stderr.write` calls added in v2.8.0 were the first unguarded stderr writes on the request path; when the host has closed the stderr pipe (EPIPE) they turned the whole tool call into an exception, and `MCP_DESKTOP_MODE` was never cleared so the next call repeated it. They now go through `user_notice`, which fails silently like `debug_log`, and the desktop launch failure reason (exit code, stderr tail) is printed for the user — a Defender quarantine, a glibc mismatch and a Gatekeeper block each need a different remedy, so the reason is what makes a report actionable.
- **Only a non-zero exit counts as a launch failure**: v2.8.0 treated any exit during the observation window as failure, so a user closing the window within two seconds (exit 0) was demoted to web mode, contradicting the v2.7.2 "window closed" semantics. Exit 0 keeps the existing behaviour.
- **No stdout fallback when `sys.stderr` is None**: `print(file=sys.stderr)` falls back to `sys.stdout` under pythonw or when the host has closed stderr — that is the MCP protocol channel, and a single notice line breaks client parsing. `debug_log` and `user_notice` now share `_write_stderr`, which captures the stream first and returns when it is None.
- **Bounded stderr tail read**: the native process may hand its stderr write end to WebView descendants, and `read()` would wait for all of them to close; it now uses `communicate(timeout=1)` and reports only the exit code on timeout.

### 🔧 Other Changes
- README (three languages): the "Install as app" paragraph claimed "each call still opens a system browser tab", which is wrong while the tab keeps its connection (it is reused); reworded to "once the app window is closed the next call opens a normal browser tab"; "exits right after launch" is now "exits with an error right after launch".

### ✅ Tests
- `test_desktop_fallback.py` — stderr assertions now run with `MCP_DEBUG=false` (conftest enables debug by default, so the previous tests still passed if the URL regressed to debug-only output); the early-exit tests use a fake binary in a temp directory instead of the committed binary; new cases: a descendant holding stderr does not hang, exit 0 is not a failure, and the two launcher copies are byte-identical (`build_desktop.py` copying had let them drift once).
- `test_user_notice.py` — stdout must stay empty when `sys.stderr` is None (both `debug_log` and `user_notice`), `user_notice` ignores `MCP_DEBUG`, and a closed stderr does not raise.

---

## [v2.8.0] - 2026-09-07 - Desktop Application Enters Maintenance-Only

### 🌟 Highlights
- The desktop application (Tauri shell) is **maintenance-only** from this release: no new features, only security fixes and "cannot launch at all" compatibility fixes, scheduled for removal in v3. The binaries still ship with this release; to keep using it, pin the version in your IDE's MCP configuration (see "Desktop application maintenance status" in the README).
- When the desktop shell cannot start (quarantined by antivirus, glibc too old, blocked by Gatekeeper, exits right after launch) the server no longer waits silently until the timeout: the process falls back to the browser and prints the URL to stderr.

### 🐛 Bug Fixes
- **The desktop-mode browser fallback never worked**: on `launch_desktop_app` failure the code called `open_browser`, which skipped itself because of the very same `MCP_DESKTOP_MODE` variable, leaving the user with no UI at all until the timeout returned "no user response". The fallback now lives at the single dispatch point: desktop launch fails → drop `MCP_DESKTOP_MODE` for this process → use the existing `smart_open_browser` (active-tab detection and session-update notification included), so every later call goes straight to the web UI without retrying the desktop shell or opening another tab; restarting the MCP server re-reads the IDE configuration and retries the desktop shell.
- **A native process that exits right after launch now counts as a launch failure**: both Python launchers only did `Popen` and slept two seconds without checking the exit code, so a binary quarantined by Defender or missing glibc was still reported as "started". Exiting within the observation window is now a failure (with exit code and stderr tail) handed to the fallback above.
- **Browser launch failure is no longer silent**: when `webbrowser.open` returns False (e.g. a headless SSH host) or all three WSL launch methods fail, the URL is printed to stderr unconditionally so the user can open it manually, instead of only appearing with `MCP_DEBUG=true`.

### 🔧 Other Changes
- `build-desktop.yml` trigger paths exclude `src-tauri/python/**`: pure-Python launcher changes no longer trigger the four-platform native rebuild and binary commit.
- The two launcher copies (`src/mcp_feedback_enhanced/desktop_app/` and `src-tauri/python/`) are now identical, so `build_desktop.py` no longer reverts the shipped copy to the older code when it copies.
- README (three languages) gains a "Desktop application maintenance status" section with migration options; SECURITY.md adds the desktop component scope and splits the support table into "latest 2.x" vs "pinned older releases receive no back-ports".
- This release does **not** touch Rust, the native binaries, the desktop WebView Origin allow-list on `/ws`, or the renovate configuration.

### ✅ Tests
- `test_desktop_fallback.py` — with the desktop module missing the URL really reaches the browser and the process leaves desktop mode; a second call reuses the existing tab instead of retrying the desktop shell; a healthy desktop shell never touches the browser; a native process exiting right after launch is a failure; a browser that cannot be opened prints the URL to stderr. The tests only intercept the lowest-level `webbrowser.open` and keep the real desktop-mode guard; four of the five were confirmed failing before the fix.

---

## [v2.7.2] - 2026-09-07 - Explicit Wrap-up When Nobody Answers

### 🌟 Highlights
- On timeout or when the user closes the UI, the tool now returns an explicit "no user response — finish the task" instruction, and the tool description's usage rules allow stopping in that case, so clients no longer treat it as a generic error and retry forever (#125).
- Closing the feedback tab/window ends the wait after a 75-second grace period instead of blocking until the timeout (10 minutes by default) (#162).

### 🐛 Bug Fixes
- **Timeout now returns a stop instruction** ([#125](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/125)): the old code handed `TimeoutError` to `ErrorHandler`, which told the model "Operation timeout / Increase timeout settings / Retry the operation later" — and a client that follows that advice calls the tool again, looping forever while the user is away. Timeouts (and the UI-closed case below) now return "No user response (reason). Treat the user as away: finish the task now and do NOT call interactive_feedback again", in Chinese and English; the tool description's USAGE RULES now list "no user response" as a valid stopping condition so the description and the reply no longer contradict each other. Only the wait itself takes this path — a `TimeoutError` raised after feedback was received (saving to disk, image processing; `OSError` ETIMEDOUT included) is still treated as an error and never turns real feedback into "no response".
- **Closing the UI ends the wait** ([#162](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/162)): the frontend only cleaned up locally on close, so the backend never knew and `wait_for_feedback` sat there until the timeout. A 75-second grace timer now starts when the session's registered WebSocket disconnects and is cancelled by any reconnect (F5, a brief drop, another tab); only an unanswered grace period counts as "user closed the UI". Why 75 s: the backend registers only the newest connection, and an older tab is not detected as stale until its next application-level heartbeat (60 s), so the grace must exceed "one heartbeat period + the first reconnect" or the "open two tabs, close the newer one" case would declare the user gone. That is the only path it guarantees, on a healthy network; if the first reconnect fails and the full backoff sequence runs (1+2+4+8+16 s + jitter, another 31-36 s) the grace is exceeded and the session wraps up as disconnected. Feedback submission and giving up are linearized under one lock: `Timer.cancel()` cannot stop a callback that has already started, so the callback invalidates itself by identity check; submission is an atomic write, so whatever the waiter reads is complete feedback (never text without the images still being processed), and feedback that arrives always wins. Sessions that never had a frontend connection (e.g. no browser opened) keep the original timeout behaviour.
- The frontend's session-timeout notification (`user_timeout`) now records its reason first, so the text returned to the AI is no longer the default "waiting for feedback".

### ⚠️ Behaviour Change
- Any WebSocket interruption longer than 75 s — laptop sleep, the browser discarding a background tab, an SSH tunnel dropping — now ends the wait with "user closed the feedback UI" instead of running to the timeout. This is deliberate: closing the window and leaving the AI hanging for ten minutes is far more common and more annoying than the occasional early wrap-up.

### ✅ Tests
- `test_feedback_timeout.py` — the timeout reply must carry the stop instruction and must not suggest retrying; a `TimeoutError` after feedback arrived must not be reported as no response; the tool description must allow stopping on no response; disconnect grace: ends the wait within the grace window (not at the timeout), a reconnect within the window does not, no timer starts once feedback exists, feedback arriving after the callback wrote TIMEOUT still wins, and a callback firing mid-submission never yields partial feedback; the `/ws` wiring (registered-socket disconnect starts the grace, reconnect cancels it) is covered through `TestClient.websocket_connect`.
- Verified with a real MCP stdio round-trip plus Chromium: open UI → F5 → still waiting → close tab → stop instruction after the grace period; with no frontend at all, the timeout returns the same instruction.

---

## [v2.7.1] - 2026-09-06 - MCP_LANGUAGE Precedence & Linux Desktop Compatibility

### 🌟 Highlights
- `MCP_LANGUAGE` now truly forces the UI language — it is no longer overridden by a language previously saved from the UI (#189).
- The Linux desktop binary now runs on Ubuntu 22.04 / Debian 12 and newer (glibc requirement lowered from 2.39 to 2.34, #165).

### 🐛 Bug Fixes
- **`MCP_LANGUAGE` now has the highest priority** ([#189](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/189)): the README described it as "force UI language", yet the detection order put the language saved from the UI ahead of it, so `MCP_LANGUAGE=zh-CN` could still render Traditional Chinese. The order is swapped; with the variable set, the in-UI language picker only applies to the current session.
- **Linux desktop binary is now built on ubuntu-22.04** ([#165](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/165)): the ubuntu-latest build required `GLIBC_2.39` and only ran on Ubuntu 24.04+; the rebuilt binary tops out at `GLIBC_2.34`.
- **Fixed the desktop-binary commit step for single-platform builds**: `download-artifact` does not create a per-artifact subdirectory when only one artifact exists, so the directory-based copy loop reported 0/4 and skipped the commit. Binaries are now uploaded and located by their final file name.

### 🔧 Other Changes
- Fixed the renovate config warning (`vulnerabilityAlerts.prPriority` is not allowed; expressed via an `isVulnerabilityAlert` packageRule instead).
- Raised dependency lower bounds in one go to the last vulnerability-fix versions recorded by OSV (aiohttp 3.14.3, starlette 1.3.1, jinja2 3.1.6, tauri 2.11.1, tokio 1.44.2, …); resolved versions are unchanged. Renovate now uses `rangeStrategy=widen`, so in-range updates no longer bump the lower bound on every patch.

---

## [v2.7.0] - 2026-09-06 - Upgrade to fastmcp 4 / mcp 2

### 🌟 Highlights
- Upgraded to fastmcp 4.x and MCP Python SDK 2.x; the server still serves legacy-protocol clients, and tool contracts and return shapes are unchanged.
- Fixed a boundary condition in `ResourceManager` temp-file cleanup that caused a flaky test.

### 🔧 Other Changes
- **Upgraded `fastmcp` to 4.x and `mcp` to 2.x** (supersedes renovate [#239](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/239) and [#240](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/240)): mcp 1.x and fastmcp 3.x are now in security-fix-only maintenance mode. fastmcp 4 depends on `mcp>=2,<3`, so the two must move together — merging only one leaves the dependency set unresolvable and the package uninstallable (same failure class as #213/#217/#221/#228). The only server-side change is constructing `ImageContent` with mcp 2's canonical field name `mime_type`; the wire format is still `mimeType`. Verified `list_tools`/`get_system_info` over stdio, and the integration tests using a legacy-protocol (2024-11-05) client all pass.
- **Fixed the age boundary in `ResourceManager.cleanup_temp_files`**: `file_age > max_age` became `>=`. `cleanup_all` passes `max_age=0` to mean "remove everything", but a just-created file has an age of exactly 0 under Windows timestamp granularity and was skipped.

### ✅ Tests
- `test_image_content.py` — no longer tied to mcp 1's internal module name or the pre-snake_case `model_dump()` fields; verifies the wire contract via `type(...) is ImageContent` and `model_dump(by_alias=True)`.

---

## [v2.6.2] - 2026-08-25 - Timeout Clamping & Tool Contract

### 🐛 Bug Fixes
- **Clamped `interactive_feedback` timeout** ([#212](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/212)): clients sometimes pass an unusably small value — the report shows Cursor passing `timeout=1`, so the feedback UI expired before it could be used. The server now clamps to 60–86400 seconds. Clamping was chosen over pydantic `ge`/`le` validation because a validation failure aborts the whole tool call; for a human-in-the-loop tool, continuing with a safe value is more useful than failing.
- **Fixed the early-exit margin in `wait_for_feedback`**: the old logic used `max(timeout - 1, 5)` for `timeout <= 30`, which *extended* a 1-second timeout to 5 seconds — the opposite of finishing early to avoid racing the MCP-layer timeout.

### 🔧 Other Changes
- **Declared a precise tool return type** (`list[TextContent | ImageContent]` instead of bare `list`), related to [#234](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/234). A bare `list` gave FastMCP nothing to work with, so it generated a wrap-result `outputSchema` (`{"result": {"type": "array"}}` plus `x-fastmcp-wrap-result`) and additionally wrapped content blocks into `structuredContent`. With the precise annotation FastMCP recognises content blocks and that schema is gone.
  - This does **not** mean the violation in #234 was reproduced. Under FastMCP 3.4.7, both before and after this change, `CallToolResult` from `interactive_feedback` and `get_system_info` contained the schema-required `content` field. See the issue for the full investigation.

### ✅ Tests
- `test_feedback_timeout.py` — clamp bounds, bad-type tolerance, and that the margin never extends the wait
- `test_tool_contract.py` — guards the return annotation against regressing to a bare `list`

---

## [v2.6.1] - 2026-08-25 - Security Fix & Maintenance Resumed

### 🌟 Version Highlights
Removes the known command execution risk, fixes Cross-Site WebSocket Hijacking, and repairs
the compatibility break that made fresh installs completely unusable. Maintenance has resumed,
with scope currently focused on security and install-breaking compatibility issues.

### 🔒 Security
- **Command execution removed** ([#219](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/219)): earlier versions accepted a `run_command` message over the **unauthenticated** WebSocket endpoint `/ws` and executed it. The guard was a shell-metacharacter blocklist, but since execution used `shell=False`, metacharacters were never the risk — `cat`, `curl`, `wget`, `python`, and `powershell` passed straight through. The auto-command feature was also **enabled by default**.
  - The feature was **removed entirely** (backend handler, session methods, frontend UI, settings, i18n strings) rather than hardened. A blocklist cannot safely permit arbitrary executables.
  - Added `tests/unit/test_no_command_execution.py` to prevent reintroduction.
  - Affected versions: **2.6.0 and all earlier**. Please upgrade.
- **Cross-Site WebSocket Hijacking (CSWSH) fixed**: reported privately as `GHSA-cmr5-gpm3-79vf` (critical, CVSS 9.6) and `GHSA-2wx7-r4rh-f663` (high). Browsers are **not** restricted by the same-origin policy when opening a WebSocket, so a malicious page could make the victim's browser connect to `ws://127.0.0.1:<port>/ws` and send messages — `/ws` accepted any `Origin` and called `accept()` without validation. Combined with `run_command` above, this escalated to remote code execution; the loopback binding did not help, because the browser itself is local.
  - Fixed with two independent layers: (1) command execution removed entirely, eliminating the escalation path; (2) `/ws` now validates `Origin` **before** `accept()`, allowing only loopback origins on the server's own port, the bound host itself, and desktop WebView schemes. Non-browser clients without an `Origin` header (such as the desktop app) are still permitted, since a cross-origin page cannot suppress the header.
  - Cross-origin attempts are rejected with HTTP 403 before the handshake completes. `tests/unit/test_websocket_origin.py` uses the exact origins from the reported proofs of concept.
  - Thanks to both reporters for the detailed analysis and working PoCs.

### 🐛 Bug Fixes
- **Fixed Web UI returning 500** ([#213](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/213), [#217](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/217), [#221](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/221), [#228](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/228)): newer Starlette changed the `TemplateResponse` signature, so the old call raised `TypeError: unhashable type: 'dict'` and no page would load for anyone installing via `uvx @latest`. Credit to [#220](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/220) (also reported in [#214](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/214), [#215](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/215), [#216](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/216)).
- **Fixed missing `session_id` in template context**: `feedback.html` needs it to initialize the frontend, but it was never passed.
- **Fixed image serialization** ([#154](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/154), [#168](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/168), [#180](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/180) and related): switched to standard `mcp.types.ImageContent`. The old implementation returned `fastmcp.utilities.types.Image`, which fails on newer FastMCP with `Output validation error: outputSchema defined but no structured output returned`. Verified via a real MCP round-trip for PNG/JPEG/GIF/WebP. Credit to [#171](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/171).

### 🔧 Other Changes
- **Dependency upper bounds added** so an upstream breaking change cannot silently break installs again. `starlette` is now an explicit direct dependency.
- **Documentation corrected**: removed the "dramatically reducing platform costs" claim (Cursor moved to token-based pricing, so the premise no longer holds); `MCP_WEB_HOST=0.0.0.0` is no longer recommended and now carries a security warning pointing to SSH port forwarding.
- Added [SECURITY.md](https://github.com/Minidoracat/mcp-feedback-enhanced/blob/main/SECURITY.md) covering supported versions, known risks, and reporting.
- Fixed `.gitignore` silently excluding the entire `tests/` suite via a repo-wide `test_*.py` rule.

### ⚠️ Known Unfixed Issues
Pre-existing limitations, outside the current maintenance scope:
- Web UI and WebSocket have **no authentication** (Origin validation stops malicious web pages, but not local processes)
- Pre-existing test failures around session status transitions, i18n environment detection, and cleanup timers

---

## [v2.5.6] - 2025-06-21 - Settings Save Mechanism Optimization & Interface Enhancement

### 🌟 Version Highlights
Refactored settings save mechanism to resolve language switching save issues, and added visual icons to settings interface for enhanced user experience.

### 🚀 Improvements
- 🔨 **Settings Save Mechanism Refactoring**: Completely removed localStorage dependency, switched to unified FastAPI backend save mechanism
  - Resolved settings not saving correctly during language switching
  - Removed debounce mechanism to ensure immediate settings save
  - Enhanced reliability and consistency of settings save
- ✨ **Settings Interface Enhancement**: Added corresponding icons to functional sections within settings tabs
  - Improved interface visual effects and user experience
  - More intuitive feature identification

### 🛠️ Technical Improvements
- 📊 **Unified Storage Architecture**: All settings now use JSON file storage for cross-environment consistency
- 🔧 **Code Simplification**: Removed complex localStorage-related code, reducing maintenance costs

---

## [v2.5.5] - 2025-06-21 - SSH Remote Development Support & Stability Enhancement

### 🌟 Version Highlights
Added SSH remote development environment support, resolving Web UI access issues in remote development scenarios. Enhanced macOS compilation support and desktop application stability for improved developer experience.

### ✨ New Features
- 🌐 **SSH Remote Development Support**: Added `MCP_WEB_HOST` environment variable for configuring web server host binding
  - Defaults to `127.0.0.1` for security
  - Can be set to `0.0.0.0` to allow remote access
  - Resolves access issues in remote development environments like Cursor SSH Remote
- 🍎 **Enhanced macOS Compilation Support**: Added `.cargo/config.toml` configuration file
  - Supports Intel (x86_64) and Apple Silicon (aarch64) architectures
  - Resolves macOS PyO3 undefined dynamic_lookup compilation issues
  - Follows PyO3 official recommended best practices

### 🚀 Improvements
- 📝 **Tool Documentation Optimization**: Moved LLM instructions to tool docstring for improved token efficiency
- 🎨 **Simplified User Configuration**: Removed complex Cursor rules configuration
- 📊 **Enhanced AI Work Summary Markdown**: Improved Markdown rendering effects and compatibility
- 🔄 **Session History Process Optimization**: Enhanced session saving and management mechanisms

### 🐛 Bug Fixes
- 🖥️ **Desktop Application MCP Protocol Fix**: Fixed MCP protocol communication pollution issues in desktop mode
- 📦 **Packaging Process Fix**: Fixed multi-platform desktop application packaging and publishing issues
- 🔧 **Release Process Optimization**: Improved stability of automated release workflows
- 🔥 **Removed ESC Shortcut**: Removed ESC shortcut functionality that could cause accidental closure

### 🛠️ Technical Improvements
- 🏗️ **Enhanced Build System**: Improved cross-platform compilation configuration and dependency management
- 📚 **Documentation Automation**: Enhanced tool self-documentation following FastMCP best practices
- 🔍 **Enhanced Debugging Features**: Added more detailed debugging information and error handling

### 📋 Usage Instructions
- **SSH Remote Development**: Set `"MCP_WEB_HOST": "0.0.0.0"` in MCP configuration to allow remote access
- **Local Development**: Keep default `"MCP_WEB_HOST": "127.0.0.1"` for security
- **macOS Development**: New compilation configuration will take effect automatically without additional setup

---

## [v2.5.0] - 2025-06-15 - Desktop Application & Performance Optimization

### 🌟 Version Highlights
Introducing cross-platform desktop application supporting Windows, macOS, and Linux. Significant performance improvements with debounce/throttle mechanisms and enhanced system stability.

### ✨ New Features
- 🖥️ **Desktop Application**: Native cross-platform desktop app based on Tauri framework, supporting Windows x64, macOS (Intel/Apple Silicon), Linux x64
- 📊 **Server-side Session History Storage**: Session records migrated from localStorage to server-side local file storage for improved data consistency and reliability
- 🔧 **Multi-platform Build Support**: Complete CI/CD pipeline supporting automated multi-platform desktop application builds
- 📝 **Desktop Mode Configuration**: Added `MCP_DESKTOP_MODE` environment variable for desktop/web mode switching
- 📋 **AI Work Summary Markdown Display**: Support for Markdown syntax rendering including headers, bold text, code blocks, lists, links and other formats

### 🚀 Improvements
- ⚡ **Significant Performance Enhancement**: Introduced debounce/throttle mechanisms to reduce unnecessary rendering and network requests
- 🌐 **Network Connection Stability**: Improved WebSocket reconnection mechanism with network status detection and intelligent reconnection
- 🎨 **UI Rendering Optimization**: Optimized rendering performance for session management, statistics, and status indicators
- 📱 **Responsive Improvements**: Adjusted heartbeat frequency and timeout thresholds to reduce system load
- 🔄 **Enhanced Modularity**: Optimized JavaScript module structure with better logging management

### 🐛 Bug Fixes
- 🌐 **Network Reconnection Improvements**: Optimized reconnection algorithm with exponential backoff strategy and random jitter
- 🖥️ **Desktop Mode Adaptation**: Fixed browser auto-launch issues in desktop mode
- 📊 **Rendering Performance Fixes**: Resolved duplicate rendering and unnecessary state update issues

### 🛠️ Technical Improvements
- 🏗️ **Build Process Optimization**: Added Makefile desktop application build commands supporting debug/release modes
- 📦 **Dependency Management**: Integrated Rust toolchain supporting cross-platform compilation and packaging
- 🔍 **Enhanced Development Tools**: Added environment checks, build validation, and cleanup tools
- 📚 **Documentation Enhancement**: Added desktop application build guide and workflow documentation
- 🔒 **Security Enhancement**: Introduced DOMPurify for XSS protection ensuring content security

### 📋 Usage Instructions
- **Desktop Mode**: Set `"MCP_DESKTOP_MODE": "true"` in MCP configuration (refer to `examples/mcp-config-desktop.json`)
- **Web Mode**: Set `"MCP_DESKTOP_MODE": "false"` in MCP configuration (default, refer to `examples/mcp-config-web.json`)
- **Test Desktop Mode**: `uvx mcp-feedback-enhanced@latest test --desktop`
- **Build Desktop Application**: `make build-desktop-release`

---

## [v2.4.3] - 2025-06-14 - Session Management Refactoring & Audio Notifications

### 🌟 Version Highlights
Migrated session management from sidebar to dedicated tab, resolving browser compatibility issues. Added audio notification system with custom audio support.

### ✨ New Features
- 🔊 **Audio Notification System**: Play audio alerts for session updates, supports built-in and custom audio uploads
- 📚 **Session History Management**: Local session record storage with export and cleanup functionality
- 💾 **Input Height Memory**: Automatically save and restore textarea input height settings
- 📋 **One-Click Copy**: Project path and session ID support click-to-copy

### 🚀 Improvements
- 📋 **Session Management Refactoring**: Migrated from sidebar to "Session Management" tab, fixing button click issues in small windows
- 🎨 **Interface Layout Optimization**: AI summary auto-expansion, submit button repositioning, removed redundant descriptions
- 🌐 **Multilingual Enhancement**: Added tooltip and button multilingual support

### 🐛 Bug Fixes
- Fixed current session details button unresponsive issue
- Fixed session details modal close delay issue
- Fixed audio notification language initialization issue
- Corrected auto-submit processing logic

---

## [v2.4.2] - Web-Only Architecture Refactoring & Smart Feature Enhancement

### 🌟 Version Highlights
This version underwent major architectural refactoring, **completely removing PyQt6 GUI dependencies** and transitioning to a pure Web UI architecture, dramatically simplifying deployment and maintenance. Additionally, multiple smart features were added, including prompt management, auto-submit, session management, and more, comprehensively enhancing user experience and work efficiency.

### 🔄 Major Architectural Changes
- 🏗️ **Complete PyQt6 GUI Removal**: Thoroughly removed desktop application dependencies, simplifying installation and deployment processes
- 🌐 **Pure Web UI Architecture**: Unified use of Web interface, supporting all platforms and environments
- 📦 **Dramatically Simplified Dependencies**: Removed PyQt6, related GUI libraries and other heavy dependencies, significantly reducing installation package size
- 🚀 **Simpler Deployment**: No need to consider GUI environment configuration, suitable for all development environments

### ✨ Brand New Features
- 📝 **Smart Prompt Management System**:
  - CRUD operations for common prompts (Create, Edit, Delete, Use)
  - Usage frequency statistics and intelligent sorting
  - Quick selection and one-click application functionality
  - Support for auto-submit marking and priority display
- ⏰ **Auto-Timed Submit Feature**:
  - Configurable countdown timer from 1-86400 seconds
  - Visual countdown display and status indicators
  - Deep integration with prompt management system
  - Support for pause, resume, and cancel operations
- 📊 **Session Management & Tracking**:
  - Real-time current session status display
  - Session history records and statistical analysis
  - Today's session count and average duration statistics
  - Session detail viewing and management functions
- 🔗 **Connection Monitoring System**:
  - Real-time WebSocket connection status monitoring
  - Latency measurement and connection quality indicators
  - Auto-reconnection mechanism and error handling
  - Detailed connection statistical information
- ⌨️ **Enhanced Shortcuts**: Added Ctrl+I quick focus input box feature (Thanks @penn201500)

### 🚀 Feature Improvements
- 🎨 **Comprehensive UI/UX Optimization**:
  - Added left session management panel with collapse/expand support
  - Top connection status bar with real-time system status display
  - Responsive design adapting to different screen sizes
  - Unified design language and visual style
- 🌐 **Enhanced Multi-language System**:
  - Optimized language switching mechanism with instant switching support
  - Added extensive translation text, improving localization coverage
  - Improved language selector UI with dropdown design
  - Fixed display issues during language switching
- 🖼️ **Image Settings Integration**:
  - Moved image settings from workspace to settings tab
  - Unified settings management interface
  - Improved organization and layout of setting items
- 📱 **Interface Layout Optimization**:
  - Adjusted layout to accommodate multi-language display requirements
  - Optimized button styles and spacing
  - Improved visual design of form elements
  - Enhanced accessibility and usability

### 🐛 Bug Fixes
- 🔧 **Session Management Fixes**:
  - Fixed session statistics information not updating correctly
  - Fixed session count calculation errors
  - Improved session state tracking mechanism
- 🎯 **Prompt Feature Fixes**:
  - Fixed common prompt management unable to correctly set auto-submit
  - Improved prompt selection and application logic
- 🌐 **Localization Switch Fixes**:
  - Fixed partial text not updating during language switching
  - Improved multi-language text loading mechanism
- 🏗️ **Architecture Stability Fixes**:
  - Fixed session management initialization issues
  - Improved error handling and resource cleanup
  - Optimized module loading order and dependencies

### 🛠️ Technical Improvements
- 📦 **Modular Architecture**:
  - Complete JavaScript code modular refactoring
  - Adopted ES6+ syntax and modern development patterns
  - Clear module separation and responsibility division
- 📊 **Performance Enhancement**:
  - Optimized WebSocket communication efficiency
  - Improved frontend resource loading speed
  - Reduced memory usage and CPU load

### 📚 Documentation Updates
- 📖 **Architecture Documentation Update**: Updated system architecture description to reflect Web-Only design
- 🔧 **Installation Guide Simplification**: Removed GUI-related installation steps and dependency descriptions
- 🖼️ **Screenshot Updates**: Updated all interface screenshots to showcase new Web UI design
- 📋 **Enhanced API Documentation**: Added API descriptions for new features like prompt management and auto-submit

---

## [v2.3.0] - System Stability & Resource Management Enhancement

### 🌟 Highlights
This version focuses on improving system stability and user experience, particularly solving the browser launch issue in Cursor SSH Remote environments.

### ✨ New Features
- 🌐 **SSH Remote Environment Support**: Solved Cursor SSH Remote browser launch issues with clear usage guidance
- 🛡️ **Error Message Improvements**: Provides more user-friendly error messages and solution suggestions when errors occur
- 🧹 **Auto-cleanup Features**: Automatically cleans temporary files and expired sessions to keep the system tidy
- 📊 **Memory Monitoring**: Monitors memory usage to prevent system resource shortage

### 🚀 Improvements
- 💾 **Resource Management Optimization**: Better system resource management for improved performance
- 🔧 **Enhanced Error Handling**: Provides clearer explanations and solutions when problems occur
- 🌐 **Connection Stability**: Improved Web UI connection stability
- 🖼️ **Image Upload Optimization**: Enhanced stability of image upload functionality
- 🎯 **Auto-focus Input Box**: Automatically focus on feedback input box when window opens, improving user experience (Thanks @penn201500)

### 🐛 Bug Fixes
- 🌐 **Connection Issues**: Fixed WebSocket connection related problems
- 🔄 **Session Management**: Fixed session state tracking issues
- 🖼️ **Image Processing**: Fixed event handling issues during image upload

---

## [v2.2.5] - WSL Environment Support & Cross-Platform Enhancement

### ✨ New Features
- 🐧 **WSL Environment Detection**: Automatically identifies WSL environments and provides specialized support logic
- 🌐 **Smart Browser Launching**: Automatically invokes Windows browser in WSL environments with multiple launch methods
- 🔧 **Cross-Platform Testing Enhancement**: Test functionality integrates WSL detection for improved test coverage

### 🚀 Improvements
- 🎯 **Environment Detection Optimization**: Improved remote environment detection logic, WSL no longer misidentified as remote environment
- 📊 **System Information Enhancement**: System information tool now displays WSL environment status
- 🧪 **Testing Experience Improvement**: Test mode automatically attempts browser launching for better testing experience

---

## [v2.2.4] - GUI Experience Optimization & Bug Fixes

### 🐛 Bug Fixes
- 🖼️ **Image Duplicate Paste Fix**: Fixed the issue where Ctrl+V image pasting in GUI would create duplicate images
- 🌐 **Localization Switch Fix**: Fixed image settings area text not translating correctly when switching languages
- 📝 **Font Readability Improvement**: Adjusted font sizes in image settings area for better readability

---

## [v2.2.3] - Timeout Control & Image Settings Enhancement

### ✨ New Features
- ⏰ **User Timeout Control**: Added customizable timeout settings with flexible range from 30 seconds to 2 hours
- ⏱️ **Countdown Timer**: Real-time countdown timer display at the top of the interface for visual time reminders
- 🖼️ **Image Size Limits**: Added image upload size limit settings (unlimited/1MB/3MB/5MB)
- 🔧 **Base64 Compatibility Mode**: Added Base64 detail mode to improve image recognition compatibility with AI models
- 🧹 **UV Cache Management Tool**: Added `cleanup_cache.py` script to help manage and clean UV cache space

### 🚀 Improvements
- 📚 **Documentation Structure Optimization**: Reorganized documentation directory structure, moved images to `docs/{language}/images/` paths
- 📖 **Cache Management Guide**: Added detailed UV Cache management guide with automated cleanup solutions
- 🎯 **Smart Compatibility Hints**: Automatically display Base64 compatibility mode suggestions when image upload fails

### 🐛 Bug Fixes
- 🛡️ **Timeout Handling Optimization**: Improved coordination between user-defined timeout and MCP system timeout
- 🖥️ **Interface Auto-close**: Fixed interface auto-close and resource cleanup logic after timeout
- 📱 **Responsive Layout**: Optimized timeout control component display on small screen devices

---

## [v2.2.2] - Timeout Auto-cleanup Fix

### 🐛 Bug Fixes
- 🔄 **Timeout Auto-cleanup**: Fixed GUI/Web UI not automatically closing after MCP session timeout (default 600 seconds)
- 🛡️ **Resource Management Optimization**: Improved timeout handling mechanism to ensure proper cleanup and closure of all UI resources on timeout
- ⚡ **Enhanced Timeout Detection**: Strengthened timeout detection logic to correctly handle timeout events in various scenarios

---

## [v2.2.1] - Window Optimization & Unified Settings Interface

### 🚀 Improvements
- 🖥️ **Window Size Constraint Removal**: Removed GUI main window minimum size limit from 1000×800 to 400×300
- 💾 **Real-time Window State Saving**: Implemented real-time saving mechanism for window size and position changes
- ⚙️ **Unified Settings Interface Optimization**: Improved GUI settings page configuration saving logic to avoid setting conflicts

### 🐛 Bug Fixes
- 🔧 **Window Size Constraint**: Fixed GUI window unable to resize to small dimensions issue
- 🛡️ **Setting Conflicts**: Fixed potential configuration conflicts during settings save operations

---

## [v2.2.0] - Layout & Settings UI Enhancements

### ✨ New Features
- 🎨 **Horizontal Layout Mode**: GUI & Web UI combined mode adds left-right layout option for summary and feedback

### 🚀 Improvements
- 🎨 **Improved Settings Interface**: Optimized the settings page for both GUI and Web UI
- ⌨️ **GUI Shortcut Enhancement**: Submit feedback shortcut now fully supports numeric keypad Enter key

### 🐛 Bug Fixes
- 🔧 **Image Duplication Fix**: Resolved Web UI image pasting duplication issue

---

## [v2.1.1] - Window Positioning Optimization

### ✨ New Features
- 🖥️ **Smart Window Positioning**: Added "Always show window at primary screen center" setting option
- 🌐 **Multi-Monitor Support**: Perfect solution for complex multi-monitor setups like T-shaped screen arrangements
- 💾 **Position Memory**: Auto-save and restore window position with intelligent visibility detection

---

## [v2.1.0] - Complete Refactored Version

### 🎨 Major Refactoring
- 🏗️ **Complete Refactoring**: GUI and Web UI adopt modular architecture
- 📁 **Centralized Management**: Reorganized folder structure, improved maintainability
- 🖥️ **Interface Optimization**: Modern design and improved user experience

### ✨ New Features
- 🍎 **macOS Interface Optimization**: Specialized improvements for macOS user experience
- ⚙️ **Feature Enhancement**: New settings options and auto-close page functionality
- ℹ️ **About Page**: Added about page with version info, project links, and acknowledgments

---

## [v2.0.14] - Shortcut & Image Feature Enhancement

### 🚀 Improvements
- ⌨️ **Enhanced Shortcuts**: Ctrl+Enter supports numeric keypad
- 🖼️ **Smart Image Pasting**: Ctrl+V directly pastes clipboard images

---

## [v2.0.9] - Multi-language Architecture Refactor

### 🔄 Refactoring
- 🌏 **Multi-language Architecture Refactor**: Support for dynamic loading
- 📁 **Modularized Language Files**: Modular organization of language files

---

## [v2.0.3] - Encoding Issues Fix

### 🐛 Critical Fixes
- 🛡️ **Complete Chinese Character Encoding Fix**: Resolved all Chinese display related issues
- 🔧 **JSON Parsing Error Fix**: Fixed data parsing errors

---

## [v2.0.0] - Web UI Support

### 🌟 Major Features
- ✅ **Added Web UI Support**: Support for remote environments
- ✅ **Auto Environment Detection**: Automatically choose appropriate interface
- ✅ **WebSocket Real-time Communication**: Real-time bidirectional communication

---

## Legend

| Icon | Meaning |
|------|---------|
| 🌟 | Version Highlights |
| ✨ | New Features |
| 🚀 | Improvements |
| 🐛 | Bug Fixes |
| 🔄 | Refactoring Changes |
| 🎨 | UI Optimization |
| ⚙️ | Settings Related |
| 🖥️ | Window Related |
| 🌐 | Multi-language/Network Related |
| 📁 | File Structure |
| ⌨️ | Shortcuts |
| 🖼️ | Image Features |
| 📝 | Prompt Management |
| ⏰ | Auto-Submit |
| 📊 | Session Management |
| 🔗 | Connection Monitoring |
| 🏗️ | Architecture Changes |
| 🛠️ | Technical Improvements |
| 📚 | Documentation Updates |

---

**Full Project Info:** [GitHub - mcp-feedback-enhanced](https://github.com/Minidoracat/mcp-feedback-enhanced)
