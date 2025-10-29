# 🤖 AI 智能代码分析功能

## 📖 概述

这是为 **MCP Feedback Enhanced** 项目设计的 AI 集成方案，在自动提交前通过 AI 智能分析代码变更，动态生成提示词和建议。

### 🎯 核心价值

**传统方式的问题：**
- ❌ 手动编写 commit message 耗时
- ❌ 容易遗漏代码中的潜在问题
- ❌ 缺乏代码质量的客观评估
- ❌ 团队成员提交规范不统一

**AI 增强后的优势：**
- ✅ **自动分析** - AI 自动检查代码变更
- ✅ **智能建议** - 生成规范的 commit message
- ✅ **问题检测** - 发现潜在 bug、安全漏洞、性能问题
- ✅ **风险评估** - 评估变更的影响范围和风险等级
- ✅ **持续学习** - 基于项目特点提供定制化建议

---

## 🏗️ 技术架构

### 文件结构

```
mcp-feedback-enhanced/
├── src/mcp_feedback_enhanced/
│   ├── ai/                                    # 🆕 AI 模块
│   │   ├── __init__.py                        # 模块入口
│   │   └── ai_analyzer.py                     # AI 分析器核心
│   └── web/
│       ├── routes/
│       │   └── ai_routes.py                   # 🆕 AI API 路由
│       └── static/
│           ├── js/modules/ai/
│           │   └── ai-analyzer.js             # 🆕 前端 AI 模块
│           └── css/
│               └── ai-analyzer.css            # 🆕 AI UI 样式
├── examples/
│   ├── ai-config-example.env                  # 🆕 配置示例
│   └── ai-integration-example.py              # 🆕 集成示例
└── docs/
    └── ai-integration-guide.md                # 🆕 详细文档
```

### 核心组件

#### 1. **AI Analyzer (后端)**
文件: `src/mcp_feedback_enhanced/ai/ai_analyzer.py`

**功能：**
- 支持多种 AI 提供商 (OpenAI, Anthropic, Ollama)
- Git diff 智能解析
- 结构化分析结果
- 异步 API 调用

**关键类：**
```python
class AIAnalyzer:
    async def analyze_git_diff(git_diff, git_status, context) -> AIAnalysisResult
```

#### 2. **API Routes (后端)**
文件: `src/mcp_feedback_enhanced/web/routes/ai_routes.py`

**端点：**
- `POST /api/ai/analyze-code` - 执行代码分析
- `GET /api/ai/status` - 获取 AI 功能状态

#### 3. **AI Analyzer Module (前端)**
文件: `src/mcp_feedback_enhanced/web/static/js/modules/ai/ai-analyzer.js`

**功能：**
- 调用 AI 分析 API
- 格式化展示分析结果
- 一键复制 commit message
- 状态管理

---

## 🚀 快速开始

### 方式 1: 本地免费方案 (Ollama)

**优势**: 完全免费、隐私安全、无需 API 密钥

```bash
# 1. 安装 Ollama
brew install ollama  # macOS
# 或访问 https://ollama.com/download

# 2. 下载代码分析模型
ollama pull qwen2.5-coder:latest

# 3. 配置环境变量
export MCP_AI_ENABLED=true
export MCP_AI_PROVIDER=ollama
export MCP_AI_MODEL=qwen2.5-coder:latest

# 4. 启动测试
uvx mcp-feedback-enhanced@latest test --web
```

### 方式 2: 云端方案 (OpenAI/Claude)

```bash
# 配置 OpenAI
export MCP_AI_ENABLED=true
export MCP_AI_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key

# 或配置 Claude
export MCP_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-your-api-key
```

---

## 💡 使用场景

### 场景 1: 自动提交前的代码审查

**工作流：**
```
1. 修改代码文件
   ↓
2. 点击 "🤖 AI 分析" 按钮
   ↓
3. AI 分析 git diff
   ↓
4. 展示分析报告:
   - 变更类型 (feat/fix/refactor...)
   - Commit Message 建议
   - 发现的问题
   - 优化建议
   - 风险评估
   ↓
5. 一键复制 commit message
   ↓
6. 提交代码
```

**示例输出：**
```
🤖 AI 代码分析报告
─────────────────────────────────────

📋 变更摘要
修复了用户输入处理中的安全漏洞，将危险的 eval() 替换为安全的 json.loads()

💬 Commit Message 建议
标题: fix(security): 修复用户输入处理安全漏洞
正文:
- 移除危险的 eval() 调用
- 使用 json.loads() 替代，添加异常处理
- 降低 SQL 注入和代码注入风险

⚠️ 发现的问题
1. 原代码使用 eval() 存在严重安全风险
2. 缺少输入验证和错误处理

💡 优化建议
1. 添加输入长度限制
2. 记录异常日志便于追踪
3. 考虑使用 schema 验证

🎯 风险等级: 中
🎯 置信度: 95%
```

### 场景 2: 团队代码规范检查

AI 自动检查：
- Commit message 是否符合 Conventional Commits 规范
- 代码风格是否一致
- 是否有明显的代码异味
- 文档是否需要更新

### 场景 3: 安全漏洞扫描

针对性检测：
- SQL 注入风险
- XSS 跨站脚本
- 密码/密钥硬编码
- 不安全的加密算法
- 依赖库安全问题

---

## 🔧 配置选项

### 环境变量

| 变量 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `MCP_AI_ENABLED` | 启用 AI 功能 | `false` | `true` |
| `MCP_AI_PROVIDER` | AI 提供商 | `ollama` | `openai`, `anthropic`, `ollama` |
| `MCP_AI_MODEL` | 模型名称 | 自动选择 | `gpt-4-turbo-preview` |
| `MCP_AI_API_KEY` | 通用 API 密钥 | - | `sk-...` |
| `OPENAI_API_KEY` | OpenAI 密钥 | - | `sk-...` |
| `ANTHROPIC_API_KEY` | Claude 密钥 | - | `sk-ant-...` |
| `MCP_AI_BASE_URL` | 自定义 API 端点 | - | `https://api.openai.com/v1` |

### MCP 配置示例

在 Cursor/Cline 的 MCP 配置文件中：

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
        "MCP_WEB_PORT": "8765",
        "MCP_DEBUG": "false"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

---

## 📊 性能与成本

### Ollama (本地)
- **成本**: 免费
- **速度**: 快 (取决于本地硬件)
- **隐私**: 100% 本地，无数据上传
- **推荐**: 日常开发使用

### OpenAI GPT-4
- **成本**: $0.01/1K tokens (输入) + $0.03/1K tokens (输出)
- **速度**: 中等 (网络延迟)
- **质量**: 非常高
- **推荐**: 关键代码审查、生产环境

### Anthropic Claude 3.5 Sonnet
- **成本**: $0.003/1K tokens (输入) + $0.015/1K tokens (输出)
- **速度**: 快
- **质量**: 高，代码理解深度好
- **推荐**: 大规模代码分析

**估算**: 分析一次中等规模的代码变更 (~500 行 diff):
- Ollama: 免费
- GPT-4: ~$0.05
- Claude 3.5: ~$0.02

---

## 🛠️ 开发与测试

### 运行示例

```bash
# 基础示例
python examples/ai-integration-example.py

# 测试 AI 功能
uv run python -m mcp_feedback_enhanced.ai.ai_analyzer
```

### API 测试

```bash
# 检查 AI 状态
curl http://localhost:8765/api/ai/status

# 分析代码
curl -X POST http://localhost:8765/api/ai/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "project_dir": ".",
    "context": "Python Web 项目"
  }'
```

### 单元测试

```bash
# 运行 AI 模块测试
pytest tests/unit/test_ai_analyzer.py -v

# 测试覆盖率
pytest tests/ --cov=src/mcp_feedback_enhanced/ai
```

---

## 🎨 UI 集成

### 在 Web UI 中添加 AI 分析按钮

```html
<!-- 在提交表单中添加 -->
<button class="btn-ai-analyze" onclick="analyzeCode()">
  🤖 AI 分析
</button>

<div id="ai-analysis-result"></div>
```

```javascript
// 调用 AI 分析
async function analyzeCode() {
    const analyzer = new MCPFeedback.AI.AIAnalyzer();

    const result = await analyzer.analyzeCode(
        '/path/to/project',
        '项目上下文信息'
    );

    // 展示结果
    const html = analyzer.formatAnalysisHTML(result);
    document.getElementById('ai-analysis-result').innerHTML = html;
}
```

---

## 🔒 安全性考虑

### 数据隐私

- ✅ **Ollama**: 完全本地运行,零数据泄露风险
- ⚠️ **OpenAI/Claude**: 代码会发送到云端,请注意:
  - 不要分析包含敏感信息的代码
  - 遵守公司的数据安全政策
  - 考虑使用私有化部署

### 最佳实践

1. **敏感项目**: 使用 Ollama 本地分析
2. **开源项目**: 可以使用云端服务
3. **企业项目**: 咨询安全团队后决定
4. **API 密钥**: 使用环境变量,不要提交到 Git

---

## 📚 进阶应用

### 自定义分析维度

创建专项分析器:

```python
from mcp_feedback_enhanced.ai import AIAnalyzer

class PerformanceAnalyzer(AIAnalyzer):
    """专注于性能优化的分析器"""

    def _build_analysis_prompt(self, git_diff, git_status, context):
        return f"""
        请从性能优化角度分析这次代码变更:

        关注点:
        1. 算法复杂度
        2. 内存使用
        3. 数据库查询优化
        4. 缓存策略
        5. 异步处理

        ...
        """
```

### 集成到 CI/CD

在 GitHub Actions 中:

```yaml
- name: AI Code Review
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    MCP_AI_ENABLED: true
  run: |
    python -c "
    from mcp_feedback_enhanced.ai import AIAnalyzer
    # 分析代码并发布评论
    "
```

---

## 🤝 贡献

欢迎贡献改进! 可以:

- 🔧 添加新的 AI 提供商支持
- 📝 优化分析提示词模板
- 🎨 改进 UI 展示
- 📖 完善文档
- 🐛 修复 Bug

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 📞 支持

- 📖 详细文档: [docs/ai-integration-guide.md](docs/ai-integration-guide.md)
- 🐛 问题反馈: [GitHub Issues](https://github.com/Minidoracat/mcp-feedback-enhanced/issues)
- 💬 社区讨论: [Discord](https://discord.gg/Gur2V67)

---

**更新日期**: 2025-10-29
**作者**: MCP Feedback Enhanced Team
