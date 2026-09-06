# Changelog (English)

This document records all version updates for **MCP Feedback Enhanced**.

## [Unreleased] - Upgrade to fastmcp 4 / mcp 2

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
