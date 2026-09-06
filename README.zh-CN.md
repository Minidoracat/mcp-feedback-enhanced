# MCP Feedback Enhanced（交互反馈 MCP）

**🌐 语言切换 / Language:** [English](README.md) | [繁體中文](README.zh-TW.md) | **简体中文**

**原作者：** [Fábio Ferreira](https://x.com/fabiomlferreira) | [原始项目](https://github.com/noopstudios/interactive-feedback-mcp) ⭐
**分支版本：** [Minidoracat](https://github.com/Minidoracat)
**UI 设计参考：** [sanshao85/mcp-feedback-collector](https://github.com/sanshao85/mcp-feedback-collector)

> ## 📢 维护状态（2026-08）
>
> 项目已恢复维护。**请升级到 v2.6.1** — 它修掉了一个命令执行漏洞：
>
> ```bash
> uvx mcp-feedback-enhanced@latest
> ```
>
> **v2.6.1 的重要变更：**
> - 🔒 **移除命令执行功能**：修复 [#219](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/219)（未认证 WebSocket 可执行任意程序）。原本的 blocklist 只挡 shell metacharacter，但因为使用 `shell=False`，metacharacter 本来就不是风险点——`cat`、`curl`、`wget`、`python` 等可直接执行；且自动执行命令**默认为启用**。此功能已完全移除，不会再提供。详见 [SECURITY.md](SECURITY.md)。
> - 🔒 **修复 Cross-Site WebSocket Hijacking**（私下报告的 `GHSA-cmr5-gpm3-79vf`、`GHSA-2wx7-r4rh-f663`）：浏览器开启 WebSocket 不受 same-origin policy 限制，恶意网页可让你的浏览器连上本机 `/ws`。现已在 `accept()` 前验证 Origin，跨站连接一律以 403 拒绝。
> - 🐛 修复新版 Starlette 造成 Web UI 直接 500 的问题（[#213](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/213)、[#217](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/217)、[#221](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/221)、[#228](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/228)）。
> - 🐛 修复图片序列化错误（[#154](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/154) 等），改用标准 `mcp.types.ImageContent`。
>
> **目前维护范围：** 安全问题、以及「装了就坏」的兼容性问题（依赖更新、上游破坏性变更）。
> 其余范围会依社区反馈调整，详见置顶 discussion。
>
> **一件必须讲清楚的事：** 本项目原始卖点是「在 Cursor 按次计费制下合并多轮交互以节省额度」。
> Cursor 已于 2025 年 6 月改为依 token 用量计费，**这个前提已不成立**
> （见 [#115](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/115)、[#200](https://github.com/Minidoracat/mcp-feedback-enhanced/issues/200)）。
> 现在的定位是「在长任务中插入人工检查点」，不再是省额度工具。
>
> 另外，MCP 协议与各客户端现已原生支持 **Elicitation**（服务器主动请求用户输入）
> 与 **MCP Apps**（工具返回交互式 UI）。如果原生能力已满足你的需求，直接用原生的即可 —
> 若有原生做不到的情境，欢迎到 discussion 告诉我，那会决定接下来修什么。

## 🎯 核心概念

这是一个 [MCP 服务器](https://modelcontextprotocol.io/)，建立**反馈导向的开发工作流程**，提供**Web UI 和桌面应用程序**双重选择，完美适配本地、**SSH 远程开发环境**与 **WSL (Windows Subsystem for Linux) 环境**。通过引导 AI 与用户确认而非进行推测性操作，在长任务中插入人工检查点，降低 AI 跑偏与返工。

**🌐 双重界面架构优势：**
- 🌐 **Web UI 界面**：无需 GUI 依赖，适合本地、远程和 WSL 环境（主要维护的界面）
- 🖥️ **桌面应用程序**：加载同一个 Web UI 的 Tauri 壳，支持 Windows、macOS、Linux（**v2.8.0 起仅维护、不再新增功能，预计 v3 移除**，见下方「桌面应用程序维护状态」）
- 📦 **统一功能**：两种界面提供完全相同的功能体验

**支持平台：** [Cursor](https://www.cursor.com) | [Cline](https://cline.bot) | [Windsurf](https://windsurf.com) | [Augment](https://www.augmentcode.com) | [Trae](https://www.trae.ai)

### 🔄 工作流程
1. **AI 调用** → `mcp-feedback-enhanced` 工具
2. **界面启动** → 自动打开桌面应用程序或浏览器界面（根据配置）
3. **智能交互** → 提示词选择、文字输入、图片上传、自动提交
4. **即时反馈** → WebSocket 连接即时传递信息给 AI
5. **会话追踪** → 自动记录会话历史与统计
6. **流程继续** → AI 根据反馈调整行为或结束任务

## 🌟 主要功能

### 🖥️ 双重界面支持
- **桌面应用程序**：基于 Tauri 的跨平台原生应用，支持 Windows、macOS、Linux
- **Web UI 界面**：轻量级浏览器界面，适合远程和 WSL 环境
- **环境自动检测**：智能识别 SSH Remote、WSL 等特殊环境
- **统一功能体验**：两种界面提供完全相同的功能

### 📝 智能工作流程
- **提示词管理**：常用提示词的 CRUD 操作、使用统计、智能排序
- **自动定时提交**：1-86400 秒弹性计时器，支持暂停、恢复、取消，新增暂停/开始按钮控制
- **会话管理追踪**：本地文件存储、隐私控制、历史导出（支持 JSON、CSV、Markdown 格式）、即时统计、弹性超时设定
- **连接监控**：WebSocket 状态监控、自动重连、品质指示
- **AI 工作摘要 Markdown 显示**：支持丰富的 Markdown 语法渲染，包含标题、粗体、代码区块、列表、链接等格式，提升内容可读性

### 🎨 现代化体验
- **响应式设计**：适配不同屏幕尺寸，模块化 JavaScript 架构
- **音效通知**：内建多种音效、支持自定义音效上传、音量控制
- **系统通知**（v2.6.0）：重要事件（如自动提交、会话超时等）的系统级即时提醒
- **智能记忆**：输入框高度记忆、一键复制、设置持久化
- **多语言支持**：简体中文、英文、繁体中文，即时切换

### 🖼️ 图片与媒体
- **全格式支持**：PNG、JPG、JPEG、GIF、BMP、WebP
- **便捷上传**：拖拽文件、剪贴板粘贴（Ctrl+V）
- **无限制处理**：支持任意大小图片，自动智能处理

## 🌐 界面预览

### Web UI 界面（v2.5.0 - 支持桌面应用程序）

<div align="center">
  <img src="docs/zh-CN/images/web1.png" width="400" alt="Web UI 主界面 - 提示词管理与自动提交" />
</div>

<details>
<summary>📱 点击查看完整界面截图</summary>

<div align="center">
  <img src="docs/zh-CN/images/web2.jpeg" width="800" alt="Web UI 完整界面 - 会话管理与设置" />
</div>

</details>

*Web UI 界面 - 支持桌面应用程序和 Web 界面，提供提示词管理、自动提交、会话追踪等智能功能*

### 桌面应用程序界面（v2.5.0 新功能）

<div align="center">
  <img src="docs/zh-CN/images/desktop1.png" width="600" alt="桌面应用程序 - 原生跨平台桌面体验" />
</div>

*桌面应用程序 - 基于 Tauri 框架的原生跨平台桌面应用，支持 Windows、macOS、Linux，提供与 Web UI 完全相同的功能*

**快捷键支持**
- `Ctrl+Enter`（Windows/Linux）/ `Cmd+Enter`（macOS）：提交反馈（主键盘与数字键盘皆支持）
- `Ctrl+V`（Windows/Linux）/ `Cmd+V`（macOS）：直接粘贴剪贴板图片
- `Ctrl+I`（Windows/Linux）/ `Cmd+I`（macOS）：快速聚焦输入框 (感谢 @penn201500)

## 🚀 快速开始

### 1. 安装与测试
```bash
# 安装 uv（如果尚未安装）
pip install uv
```

### 2. 配置 MCP
**基本配置**（适合大多数用户）：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

**进阶配置**（需要自定义环境）：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DEBUG": "false",
        "MCP_WEB_HOST": "127.0.0.1",
        "MCP_WEB_PORT": "8765",
        "MCP_LANGUAGE": "zh-CN"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

**桌面应用程序配置**（v2.5.0 新功能 - 使用原生桌面应用程序）：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DESKTOP_MODE": "true",
        "MCP_WEB_HOST": "127.0.0.1",
        "MCP_WEB_PORT": "8765",
        "MCP_DEBUG": "false"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

> **⚠️ 桌面应用程序维护状态（v2.8.0 起）**
>
> 桌面应用程序进入 **maintenance-only**：不再新增功能（例如窗口置顶、常驻、提交后保留窗口），只修安全问题与「完全无法启动」的兼容性问题；预计于 v3 移除，届时会在发布说明标明最后一个含桌面 binary 的版本。理由：它只是加载 Web UI 的一层 Tauri 壳，却占了包八成体积、需要三平台 CI 与签名，而反馈的问题多是无法在 CI 重现的平台兼容性（杀毒误判、glibc、Gatekeeper、高 DPI、多显示器）。
>
> - **想继续用桌面模式**：把 IDE 的 MCP 配置 `args` 从 `mcp-feedback-enhanced@latest` 改成固定版本（例如 `mcp-feedback-enhanced@2.8.0`），并保留 `MCP_DESKTOP_MODE=true`。2.8.0 起若桌面壳无法启动（被杀毒隔离、glibc 太旧、Gatekeeper 拦下、启动后随即出错退出），该次会自动改开浏览器并在 stderr 打印网址，不再空等到超时；重启 MCP 服务器后会再尝试桌面。不要固定到 2.6.0 或更早（含未认证命令执行漏洞，见 [SECURITY.md](SECURITY.md)）。
> - **改用 Web 模式**：移除 `MCP_DESKTOP_MODE` 即可，功能完全相同，提交后标签页会保留、下次调用自动更新内容。想要独立窗口，可在 Chrome／Edge 打开反馈页后选「安装为应用」——但这只是浏览器功能，不是桌面版的等价替代：后端仍由 MCP 调用启动、关掉应用窗口后下次调用会打开在普通浏览器标签页而非该窗口、端口改变时要重新安装、通知权限需重新授权；窗口置顶请用操作系统工具。

**配置文件示例**：
- 桌面模式：[examples/mcp-config-desktop.json](examples/mcp-config-desktop.json)
- Web 模式：[examples/mcp-config-web.json](examples/mcp-config-web.json)

### 3. 设置提示工程
为了获得最佳效果，请在 AI 助手中添加以下规则：

```
# MCP Interactive Feedback 规则

注意在任务完成前根据mcp-feedback-enhanced工具的要求进行工具调用
```

## ⚙️ 高级设置

### 环境变量
| 变量 | 用途 | 值 | 默认 |
|------|------|-----|------|
| `MCP_DEBUG` | 调试模式 | `true`/`false` | `false` |
| `MCP_WEB_HOST` | Web UI 主机绑定 | IP 地址或主机名 | `127.0.0.1` |
| `MCP_WEB_PORT` | Web UI 端口 | `1024-65535` | `8765` |
| `MCP_DESKTOP_MODE` | 桌面应用程序模式 | `true`/`false` | `false` |
| `MCP_LANGUAGE` | 强制指定界面语言 | `zh-TW`/`zh-CN`/`en` | 自动检测 |

**`MCP_WEB_HOST` 说明**：
- `127.0.0.1`（默认）：仅本地访问，**建议保持此设置**
- `0.0.0.0`：绑定所有网络接口。⚠️ **不建议**：Web UI 与 `/ws` 端点**没有任何认证机制**，任何能连到该端口的人都能读取会话内容（含项目路径与 AI 摘要）并提交反馈。远程开发请改用 SSH 端口转发（见常见问题）。

**`MCP_LANGUAGE` 说明**：
- 用于强制指定界面语言，覆盖系统自动检测
- 支持的语言代码：
  - `zh-TW`：繁体中文
  - `zh-CN`：简体中文
  - `en`：英文
- 语言检测优先顺序：
  1. `MCP_LANGUAGE` 环境变量（最高优先级；设置后，界面中的语言选择只在当次会话生效）
  2. 用户在界面中保存的语言设置
  3. 系统环境变量（LANG、LC_ALL 等）
  4. 系统默认语言
  5. 回退到默认语言（繁体中文）

### 测试选项
```bash
# 版本查询
uvx mcp-feedback-enhanced@latest version       # 检查版本

# 界面测试
uvx mcp-feedback-enhanced@latest test --web    # 测试 Web UI (自动持续运行)
uvx mcp-feedback-enhanced@latest test --desktop # 测试桌面应用程序 (v2.5.0 新功能)

# 调试模式
MCP_DEBUG=true uvx mcp-feedback-enhanced@latest test

# 指定语言测试
MCP_LANGUAGE=en uvx mcp-feedback-enhanced@latest test --web    # 强制使用英文界面
MCP_LANGUAGE=zh-TW uvx mcp-feedback-enhanced@latest test --web  # 强制使用繁体中文
MCP_LANGUAGE=zh-CN uvx mcp-feedback-enhanced@latest test --web  # 强制使用简体中文
```

### 开发者安装
```bash
git clone https://github.com/Minidoracat/mcp-feedback-enhanced.git
cd mcp-feedback-enhanced
uv sync
```

**本地测试方式**
```bash
# 功能测试
make test-func                                           # 标准功能测试
make test-web                                            # Web UI 测试 (持续运行)
make test-desktop-func                                   # 桌面应用功能测试

# 或直接使用指令
uv run python -m mcp_feedback_enhanced test              # 标准功能测试
uvx --no-cache --with-editable . mcp-feedback-enhanced test --web   # Web UI 测试 (持续运行)
uvx --no-cache --with-editable . mcp-feedback-enhanced test --desktop # 桌面应用测试

# 桌面应用构建 (v2.5.0 新功能)
make build-desktop                                       # 构建桌面应用 (debug 模式)
make build-desktop-release                               # 构建桌面应用 (release 模式)
make test-desktop                                        # 测试桌面应用
make clean-desktop                                       # 清理桌面构建产物

# 单元测试
make test                                                # 运行所有单元测试
make test-fast                                          # 快速测试 (跳过慢速测试)
make test-cov                                           # 测试并生成覆盖率报告

# 代码质量检查
make check                                              # 完整代码质量检查
make quick-check                                        # 快速检查并自动修复
```

**测试说明**
- **功能测试**：测试 MCP 工具的完整功能流程
- **单元测试**：测试各个模块的独立功能
- **覆盖率测试**：生成 HTML 覆盖率报告到 `htmlcov/` 目录
- **质量检查**：包含 linting、格式化、类型检查

## 🆕 版本更新记录

📋 **完整版本更新记录：** [RELEASE_NOTES/CHANGELOG.zh-CN.md](RELEASE_NOTES/CHANGELOG.zh-CN.md)

### 最新版本亮点（v2.6.0）
- 📊 **会话导出功能**: 支持将会话记录导出为多种格式，方便分享和存档
- ⏸️ **自动提交控制**: 新增暂停和开始按钮，让用户更好控制自动提交时机
- 🔔 **系统通知**: 新增系统级通知功能，重要事件即时提醒
- ⏱️ **会话超时机制优化**: 重新设计会话管理，提供更弹性的设置选项
- 🌏 **多语系强化**: 重构多语系架构，通知系统也完整支持多语言
- 🎨 **界面简化**: 大幅简化用户界面，提升使用体验

## 🐛 常见问题

### 🌐 SSH Remote 环境问题
**Q: SSH Remote 环境下浏览器无法启动或无法访问**
A: **建议使用 SSH 端口转发**（安全，不暴露服务）：

1. 使用默认配置（`MCP_WEB_HOST`: `127.0.0.1`）
2. 设置 SSH 端口转发：
   - **VS Code Remote SSH**: 按 `Ctrl+Shift+P` → "Forward a Port" → 输入 `8765`
   - **Cursor SSH Remote**: 手动添加端口转发规则（端口 8765）
3. 在本地浏览器打开：`http://localhost:8765`

> ⚠️ 旧版 README 曾建议设置 `MCP_WEB_HOST=0.0.0.0` 直接对外开放。**已不再建议**：
> Web UI 与 `/ws` 端点没有认证机制，对外绑定等同于让同网段任何人读取你的会话内容并提交反馈。

详细解决方案请参考：[SSH Remote 环境使用指南](docs/zh-CN/ssh-remote/browser-launch-issues.md)

**Q: 为什么没有接收到 MCP 新的反馈？**
A: 可能是 WebSocket 连接问题。**解决方法**：直接重新刷新浏览器页面。

**Q: 为什么没有调用出 MCP？**
A: 请确认 MCP 工具状态为绿灯。**解决方法**：反复开关 MCP 工具，等待几秒让系统重新连接。

**Q: Augment 无法启动 MCP**
A: **解决方法**：完全关闭并重新启动 VS Code 或 Cursor，重新打开项目。

### 🔧 一般问题
**Q: 如何使用桌面应用程序？**
A: v2.5.0 新增跨平台桌面应用程序支持。在 MCP 配置中设定 `"MCP_DESKTOP_MODE": "true"` 即可启用：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DESKTOP_MODE": "true",
        "MCP_WEB_PORT": "8765"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```
**配置文件示例**：[examples/mcp-config-desktop.json](examples/mcp-config-desktop.json)

**Q: 如何使用旧版 PyQt6 GUI 界面？**
A: v2.4.0 版本已完全移除 PyQt6 GUI 依赖。如需使用旧版 GUI，请指定 v2.3.0 或更早版本：`uvx mcp-feedback-enhanced@2.3.0`
**注意**：旧版本不包含新功能（提示词管理、自动提交、会话管理、桌面应用程序等）。

**Q: 出现 "Unexpected token 'D'" 错误**
A: 调试输出干扰。设置 `MCP_DEBUG=false` 或移除该环境变量。

**Q: 中文字符乱码**
A: 已在 v2.0.3 修复。更新到最新版本：`uvx mcp-feedback-enhanced@latest`

**Q: 多屏幕环境下窗口消失或定位错误**
A: 已在 v2.1.1 修复。进入「⚙️ 设置」标签页，勾选「总是在主屏幕中心显示窗口」即可解决。特别适用于 T 字型屏幕排列等复杂多屏幕配置。

**Q: 图片上传失败**
A: 检查文件格式（PNG/JPG/JPEG/GIF/BMP/WebP）。系统支持任意大小的图片文件。

**Q: Web UI 无法启动**
A: 检查防火墙设置或尝试使用不同的端口。

**Q: UV Cache 占用过多磁盘空间**
A: 由于频繁使用 `uvx` 命令，cache 可能会累积到数十 GB。建议定期清理：
```bash
# 查看 cache 大小和详细信息
python scripts/cleanup_cache.py --size

# 预览清理内容（不实际清理）
python scripts/cleanup_cache.py --dry-run

# 执行标准清理
python scripts/cleanup_cache.py --clean

# 强制清理（会尝试关闭相关程序，解决 Windows 文件占用问题）
python scripts/cleanup_cache.py --force

# 或直接使用 uv 命令
uv cache clean
```
详细说明请参考：[Cache 管理指南](docs/zh-CN/cache-management.md)

**Q: AI 模型无法解析图片**
A: 各种 AI 模型（包括 Gemini Pro 2.5、Claude 等）在图片解析上可能存在不稳定性，表现为有时能正确识别、有时无法解析上传的图片内容。这是 AI 视觉理解技术的已知限制。建议：
1. 确保图片质量良好（高对比度、清晰文字）
2. 多尝试几次上传，通常重试可以成功
3. 如持续无法解析，可尝试调整图片大小或格式

## 🙏 致谢

### 🌟 支持原作者
**Fábio Ferreira** - [X @fabiomlferreira](https://x.com/fabiomlferreira)
**原始项目：** [noopstudios/interactive-feedback-mcp](https://github.com/noopstudios/interactive-feedback-mcp)

如果您觉得有用，请：
- ⭐ [为原项目按星星](https://github.com/noopstudios/interactive-feedback-mcp)
- 📱 [关注原作者](https://x.com/fabiomlferreira)

### 设计灵感
**sanshao85** - [mcp-feedback-collector](https://github.com/sanshao85/mcp-feedback-collector)

### 贡献者
**penn201500** - [GitHub @penn201500](https://github.com/penn201500)
- 🎯 自动聚焦输入框功能 ([PR #39](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/39))

**leo108** - [GitHub @leo108](https://github.com/leo108)
- 🌐 SSH 远程开发支持 (`MCP_WEB_HOST` 环境变量) ([PR #113](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/113))

**Alsan** - [GitHub @Alsan](https://github.com/Alsan)
- 🍎 macOS PyO3 编译配置支持 ([PR #93](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/93))

**fireinice** - [GitHub @fireinice](https://github.com/fireinice)
- 📝 工具文档优化 (LLM 指令移至 docstring) ([PR #105](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/105))

### 社群支援
- **Discord：** [https://discord.gg/Gur2V67](https://discord.gg/Gur2V67)
- **Issues：** [GitHub Issues](https://github.com/Minidoracat/mcp-feedback-enhanced/issues)

## 📄 授权

MIT 授权条款 - 详见 [LICENSE](LICENSE) 档案

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Minidoracat/mcp-feedback-enhanced&type=Date)](https://star-history.com/#Minidoracat/mcp-feedback-enhanced&Date)

---
**🌟 欢迎 Star 并分享给更多开发者！**
