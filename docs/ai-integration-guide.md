# AI 集成使用指南

## 📚 目录

- [功能简介](#功能简介)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [进阶配置](#进阶配置)
- [常见问题](#常见问题)

---

## 功能简介

MCP Feedback Enhanced 的 AI 集成功能为项目提供智能代码分析能力，主要特性包括:

### 🎯 核心功能

1. **Git Diff 智能分析** - AI 自动分析代码变更内容
2. **Commit Message 生成** - 自动生成符合规范的提交信息
3. **代码问题检测** - 识别潜在的 bug、安全问题、性能问题
4. **优化建议提供** - 提供具体可行的代码优化建议
5. **风险评估** - 评估代码变更的风险等级
6. **动态提示词生成** - 基于分析结果动态生成智能提示

### 🤖 支持的 AI 提供商

| 提供商 | 推荐场景 | API 密钥 | 成本 |
|--------|---------|----------|------|
| **Ollama** | 本地开发、隐私要求高 | ❌ 不需要 | ✅ 免费 |
| **OpenAI** | 高质量分析、生产环境 | ✅ 需要 | 💰 付费 |
| **Anthropic** | 代码理解深度、安全性 | ✅ 需要 | 💰 付费 |

---

## 快速开始

### 方案 1: 使用 Ollama (推荐新手)

**优势**: 完全免费、无需 API 密钥、隐私保护、响应快速

#### 步骤 1: 安装 Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 访问 https://ollama.com/download 下载安装程序
```

#### 步骤 2: 下载代码分析模型

```bash
# 推荐: Qwen2.5 Coder (专为代码优化)
ollama pull qwen2.5-coder:latest

# 备选: CodeLlama
ollama pull codellama:latest

# 备选: DeepSeek Coder
ollama pull deepseek-coder:latest
```

#### 步骤 3: 验证模型运行

```bash
# 测试模型是否正常运行
ollama run qwen2.5-coder:latest

# 输入任意代码相关问题测试
# 输入 /bye 退出
```

#### 步骤 4: 配置环境变量

在项目根目录创建 `.env` 文件:

```bash
# 启用 AI 功能
MCP_AI_ENABLED=true

# 使用 Ollama
MCP_AI_PROVIDER=ollama

# 指定模型 (可选)
MCP_AI_MODEL=qwen2.5-coder:latest
```

#### 步骤 5: 启动 MCP 服务

```bash
# 测试 AI 功能
uvx mcp-feedback-enhanced@latest test --web

# 或在 MCP 配置中添加环境变量
```

---

### 方案 2: 使用 OpenAI GPT-4

#### 步骤 1: 获取 API 密钥

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 登录并进入 API Keys 页面
3. 创建新的 API 密钥

#### 步骤 2: 配置环境变量

```bash
# 启用 AI 功能
MCP_AI_ENABLED=true

# 使用 OpenAI
MCP_AI_PROVIDER=openai

# 设置 API 密钥
OPENAI_API_KEY=sk-your-api-key-here

# 选择模型 (可选)
MCP_AI_MODEL=gpt-4-turbo-preview
```

---

### 方案 3: 使用 Anthropic Claude

#### 步骤 1: 获取 API 密钥

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 登录并创建 API 密钥

#### 步骤 2: 配置环境变量

```bash
# 启用 AI 功能
MCP_AI_ENABLED=true

# 使用 Anthropic
MCP_AI_PROVIDER=anthropic

# 设置 API 密钥
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# 选择模型 (可选)
MCP_AI_MODEL=claude-3-5-sonnet-20241022
```

---

## 配置说明

### 环境变量完整列表

```bash
# ===== AI 功能控制 =====
MCP_AI_ENABLED=true              # 启用/禁用 AI 功能

# ===== AI 提供商 =====
MCP_AI_PROVIDER=ollama           # 选项: openai, anthropic, ollama

# ===== API 认证 =====
MCP_AI_API_KEY=xxx               # 通用 API 密钥 (优先级最高)
OPENAI_API_KEY=sk-xxx            # OpenAI 专用密钥
ANTHROPIC_API_KEY=sk-ant-xxx     # Anthropic 专用密钥

# ===== 模型选择 =====
MCP_AI_MODEL=gpt-4-turbo-preview # 自定义模型

# ===== API 端点 =====
MCP_AI_BASE_URL=https://api.openai.com/v1  # 自定义 API 端点
```

### MCP 服务器配置示例

在 Cursor/Cline 等 IDE 的 MCP 配置中添加:

```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_AI_ENABLED": "true",
        "MCP_AI_PROVIDER": "ollama",
        "MCP_AI_MODEL": "qwen2.5-coder:latest",
        "MCP_WEB_HOST": "127.0.0.1",
        "MCP_WEB_PORT": "8765"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

---

## 使用方法

### 1. 在 Web UI 中使用

#### 自动提交前分析

1. **修改代码** - 进行代码变更
2. **点击 "🤖 AI 分析"** 按钮
3. **等待分析** - AI 自动分析 git diff
4. **查看结果**:
   - 📋 变更摘要
   - 💬 Commit Message 建议
   - ⚠️ 潜在问题列表
   - 💡 优化建议
   - 🎯 风险评估
5. **一键应用** - 点击复制按钮使用建议的 commit message

#### 动态提示词生成

AI 分析完成后，系统会自动:
- 生成与变更类型匹配的提示词
- 提供针对性的下一步建议
- 高亮显示需要关注的问题

### 2. 通过 API 调用

#### 检查 AI 状态

```bash
curl http://localhost:8765/api/ai/status
```

响应示例:
```json
{
  "enabled": true,
  "provider": "ollama",
  "model": "qwen2.5-coder:latest",
  "configured": true,
  "status": "ready"
}
```

#### 分析代码变更

```bash
curl -X POST http://localhost:8765/api/ai/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "project_dir": "/path/to/your/project",
    "context": "这是一个 Python Web 项目"
  }'
```

---

## 进阶配置

### 1. 自定义 AI 提示词模板

修改 `src/mcp_feedback_enhanced/ai/ai_analyzer.py` 中的 `_build_analysis_prompt` 方法:

```python
def _build_analysis_prompt(self, git_diff, git_status, project_context):
    """自定义提示词模板"""
    return f"""
    你是一个{project_context}领域的专家。

    请分析以下代码变更:
    {git_diff}

    关注点:
    1. 安全性
    2. 性能
    3. 可维护性

    ...
    """
```

### 2. 调整分析参数

```python
# 在 ai_analyzer.py 中调整
payload = {
    "model": self.model,
    "temperature": 0.1,  # 降低创造性,提高稳定性
    "max_tokens": 2048,  # 限制响应长度
}
```

### 3. 集成到 Git Hooks

在 `.git/hooks/pre-commit` 中:

```bash
#!/bin/bash

# 调用 AI 分析
python -c "
from mcp_feedback_enhanced.ai import AIAnalyzer
import asyncio

async def analyze():
    analyzer = AIAnalyzer()
    result = await analyzer.analyze_git_diff(
        git_diff='$(git diff --cached)',
        git_status='$(git status --short)'
    )

    if result.risk_level == 'high':
        print('❌ 检测到高风险变更,请仔细审查!')
        print(result.summary)
        exit(1)

asyncio.run(analyze())
"
```

---

## 常见问题

### Q1: AI 分析速度慢怎么办?

**A**:
- **使用 Ollama**: 本地运行,响应更快
- **限制 diff 大小**: 在 `ai_analyzer.py` 中调整 `git_diff[:5000]`
- **使用更快的模型**: 如 `gpt-3.5-turbo` 或 `claude-3-haiku`

### Q2: API 调用失败怎么办?

**A**: 检查以下几点:
```bash
# 1. 验证 API 密钥
echo $OPENAI_API_KEY

# 2. 测试网络连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 3. 检查 Ollama 服务状态
ollama list
```

### Q3: 如何降低 API 成本?

**A**:
1. **使用 Ollama** - 完全免费
2. **使用更便宜的模型** - `gpt-3.5-turbo` 而非 `gpt-4`
3. **限制调用频率** - 只在关键提交前分析
4. **缓存分析结果** - 避免重复分析相同代码

### Q4: 分析结果不准确?

**A**:
1. **提供更多上下文** - 在 `project_context` 中详细描述项目
2. **调整提示词** - 修改 `_build_analysis_prompt` 方法
3. **使用更强大的模型** - 切换到 `gpt-4` 或 `claude-3-5-sonnet`
4. **增加 temperature** - 提高创造性(但可能降低一致性)

### Q5: 如何在 CI/CD 中使用?

**A**: 在 GitHub Actions 中:

```yaml
name: AI Code Review

on: [pull_request]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install MCP Feedback Enhanced
        run: pip install mcp-feedback-enhanced

      - name: AI Code Analysis
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          MCP_AI_ENABLED: true
          MCP_AI_PROVIDER: openai
        run: |
          python -m mcp_feedback_enhanced.ai.ai_analyzer
```

---

## 技术架构

```
┌─────────────────────────────────────────┐
│          Web UI / API 层                │
│  - 用户交互界面                          │
│  - RESTful API 端点                     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│        AI Analyzer 服务层               │
│  - AIAnalyzer 类                        │
│  - 提示词构建                            │
│  - 结果解析                              │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│         AI Provider 层                  │
│  ├─ OpenAI API Client                  │
│  ├─ Anthropic API Client               │
│  └─ Ollama API Client                  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│         外部 AI 服务                     │
│  - OpenAI GPT Models                    │
│  - Anthropic Claude Models              │
│  - Local Ollama Models                  │
└─────────────────────────────────────────┘
```

---

## 贡献指南

欢迎贡献代码! 以下是一些改进方向:

1. **新增 AI 提供商** - 支持 Google Gemini、Cohere 等
2. **提示词优化** - 改进分析准确性
3. **性能优化** - 减少 API 调用次数
4. **UI 增强** - 更好的分析结果展示
5. **多语言支持** - 支持更多编程语言的专项分析

---

## 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件

---

**更新日期**: 2025-10-29
**版本**: 1.0.0
**维护者**: MCP Feedback Enhanced Team
