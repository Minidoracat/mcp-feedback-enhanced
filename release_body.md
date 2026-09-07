# Release v2.8.1 - 2026-09-07 - Desktop Fallback Follow-ups

## 🌟 Key Highlights
- stderr notices are now protected writes and never fall back to stdout (the MCP protocol channel) when `sys.stderr` is None.
- The desktop shell only counts as failed on a non-zero exit, so closing the window yourself no longer demotes the process to web mode; the failure reason is printed for the user.

## 🌐 Detailed Release Notes

### 🇺🇸 English
📖 **[View Complete English Release Notes](https://github.com/Minidoracat/mcp-feedback-enhanced/blob/main/RELEASE_NOTES/CHANGELOG.en.md)**

### 🇹🇼 繁體中文
📖 **[查看完整繁體中文發布說明](https://github.com/Minidoracat/mcp-feedback-enhanced/blob/main/RELEASE_NOTES/CHANGELOG.zh-TW.md)**

### 🇨🇳 简体中文
📖 **[查看完整简体中文发布说明](https://github.com/Minidoracat/mcp-feedback-enhanced/blob/main/RELEASE_NOTES/CHANGELOG.zh-CN.md)**

---

## 📦 Quick Installation / 快速安裝

```bash
# Latest version / 最新版本
uvx mcp-feedback-enhanced@latest

# This specific version / 此特定版本
uvx mcp-feedback-enhanced@v2.8.1
```

## 🔗 Links
- **Documentation**: [README.md](https://github.com/Minidoracat/mcp-feedback-enhanced/blob/main/README.md)
- **Full Changelog**: [CHANGELOG](https://github.com/Minidoracat/mcp-feedback-enhanced/blob/main/RELEASE_NOTES/)
- **Issues**: [GitHub Issues](https://github.com/Minidoracat/mcp-feedback-enhanced/issues)

---
**Release automatically generated from CHANGELOG system** 🤖
