#!/usr/bin/env python3
"""
AI 代码分析服务模块
==================

提供 AI 驱动的代码变更分析功能，支持多种 LLM 提供商。
用于在自动提交前智能分析代码变更并生成建议。

支持的 AI 提供商:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- 本地 LLM (Ollama)

作者: MCP Feedback Enhanced Team
版本: 1.0.0
"""

import asyncio
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiohttp


class AIProvider(Enum):
    """AI 提供商枚举"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"  # 本地 LLM


class ChangeSeverity(Enum):
    """代码变更严重性评级"""

    HIGH = "high"  # 重大变更
    MEDIUM = "medium"  # 中等变更
    LOW = "low"  # 轻微变更


class ChangeType(Enum):
    """代码变更类型"""

    FEAT = "feat"  # 新功能
    FIX = "fix"  # Bug 修复
    REFACTOR = "refactor"  # 重构
    DOCS = "docs"  # 文档更新
    STYLE = "style"  # 代码格式
    TEST = "test"  # 测试相关
    CHORE = "chore"  # 构建/工具
    PERF = "perf"  # 性能优化


@dataclass
class AIAnalysisResult:
    """AI 分析结果数据类"""

    # 基本信息
    change_type: ChangeType
    severity: ChangeSeverity
    summary: str  # 一句话摘要

    # Commit Message 建议
    commit_title: str  # 提交标题 (50 字符内)
    commit_body: str  # 提交正文

    # 代码分析
    issues_found: list[str]  # 发现的潜在问题
    suggestions: list[str]  # 优化建议
    affected_files: list[str]  # 影响的文件列表

    # 风险评估
    risk_level: str  # 风险等级: "low", "medium", "high"
    breaking_changes: bool  # 是否包含破坏性变更

    # 额外信息
    confidence_score: float  # AI 分析置信度 (0-1)
    raw_response: dict  # 原始 AI 响应


class AIAnalyzer:
    """AI 代码分析器主类"""

    def __init__(
        self,
        provider: AIProvider = AIProvider.OPENAI,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        """
        初始化 AI 分析器

        Args:
            provider: AI 提供商
            api_key: API 密钥（从环境变量或参数获取）
            model: 模型名称（可选，使用默认模型）
            base_url: API 基础 URL（用于自定义端点）
        """
        self.provider = provider
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model or self._get_default_model()
        self.base_url = base_url or self._get_default_base_url()

        # 验证配置
        if not self.api_key and provider != AIProvider.OLLAMA:
            raise ValueError(
                f"API key required for {provider.value}. "
                f"Set MCP_AI_API_KEY environment variable."
            )

    def _get_api_key_from_env(self) -> str | None:
        """从环境变量获取 API 密钥"""
        key_mapping = {
            AIProvider.OPENAI: "OPENAI_API_KEY",
            AIProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            AIProvider.OLLAMA: None,  # 本地 LLM 不需要密钥
        }
        env_var = key_mapping.get(self.provider)
        if env_var:
            # 优先使用 MCP 专用环境变量
            return os.getenv("MCP_AI_API_KEY") or os.getenv(env_var)
        return None

    def _get_default_model(self) -> str:
        """获取默认模型"""
        model_mapping = {
            AIProvider.OPENAI: "gpt-4-turbo-preview",
            AIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            AIProvider.OLLAMA: "qwen2.5-coder:latest",
        }
        # 允许环境变量覆盖
        env_model = os.getenv("MCP_AI_MODEL")
        return env_model or model_mapping.get(self.provider, "gpt-4")

    def _get_default_base_url(self) -> str:
        """获取默认 API 基础 URL"""
        url_mapping = {
            AIProvider.OPENAI: "https://api.openai.com/v1",
            AIProvider.ANTHROPIC: "https://api.anthropic.com/v1",
            AIProvider.OLLAMA: "http://localhost:11434",  # Ollama 默认端口
        }
        # 允许环境变量覆盖
        env_url = os.getenv("MCP_AI_BASE_URL")
        return env_url or url_mapping.get(self.provider, "")

    async def analyze_git_diff(
        self, git_diff: str, git_status: str, project_context: str = ""
    ) -> AIAnalysisResult:
        """
        分析 Git 代码变更

        Args:
            git_diff: git diff 输出
            git_status: git status 输出
            project_context: 项目上下文信息（可选）

        Returns:
            AIAnalysisResult: AI 分析结果
        """
        # 构建分析提示词
        prompt = self._build_analysis_prompt(git_diff, git_status, project_context)

        # 调用 AI API
        response = await self._call_ai_api(prompt)

        # 解析响应
        result = self._parse_ai_response(response)

        return result

    def _build_analysis_prompt(
        self, git_diff: str, git_status: str, project_context: str
    ) -> str:
        """构建 AI 分析提示词"""
        return f"""你是一个专业的代码审查助手。请分析以下 Git 代码变更，并提供详细的分析报告。

# 项目上下文
{project_context if project_context else "无额外上下文信息"}

# Git Status
```
{git_status}
```

# Git Diff
```diff
{git_diff[:5000]}  # 限制 diff 长度避免超出 token 限制
```

请以 JSON 格式返回分析结果，包含以下字段：

{{
  "change_type": "feat|fix|refactor|docs|style|test|chore|perf",
  "severity": "high|medium|low",
  "summary": "一句话总结这次变更",
  "commit_title": "符合 Conventional Commits 规范的提交标题（50字符内）",
  "commit_body": "详细的提交说明（多行，解释为什么做这个变更）",
  "issues_found": ["潜在问题1", "潜在问题2"],
  "suggestions": ["优化建议1", "优化建议2"],
  "affected_files": ["文件路径1", "文件路径2"],
  "risk_level": "low|medium|high",
  "breaking_changes": false,
  "confidence_score": 0.95
}}

注意事项：
1. commit_title 必须符合格式: <type>(<scope>): <description>
2. 检查是否有明显的 bug、安全问题、性能问题
3. 评估变更的风险等级
4. 提供具体、可操作的优化建议
5. 所有文本使用中文
"""

    async def _call_ai_api(self, prompt: str) -> dict[str, Any]:
        """
        调用 AI API

        Args:
            prompt: 分析提示词

        Returns:
            dict: AI API 响应
        """
        if self.provider == AIProvider.OPENAI:
            return await self._call_openai_api(prompt)
        elif self.provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic_api(prompt)
        elif self.provider == AIProvider.OLLAMA:
            return await self._call_ollama_api(prompt)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    async def _call_openai_api(self, prompt: str) -> dict[str, Any]:
        """调用 OpenAI API"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的代码审查助手，擅长分析代码变更并提供建设性建议。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,  # 降低随机性，提高稳定性
            "response_format": {"type": "json_object"},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data

    async def _call_anthropic_api(self, prompt: str) -> dict[str, Any]:
        """调用 Anthropic Claude API"""
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data

    async def _call_ollama_api(self, prompt: str) -> dict[str, Any]:
        """调用本地 Ollama API"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data

    def _parse_ai_response(self, response: dict[str, Any]) -> AIAnalysisResult:
        """
        解析 AI API 响应

        Args:
            response: AI API 原始响应

        Returns:
            AIAnalysisResult: 解析后的分析结果
        """
        try:
            # 提取内容文本
            if self.provider == AIProvider.OPENAI:
                content = response["choices"][0]["message"]["content"]
            elif self.provider == AIProvider.ANTHROPIC:
                content = response["content"][0]["text"]
            elif self.provider == AIProvider.OLLAMA:
                content = response["response"]
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # 解析 JSON 内容
            data = json.loads(content)

            # 构建结果对象
            return AIAnalysisResult(
                change_type=ChangeType(data.get("change_type", "chore")),
                severity=ChangeSeverity(data.get("severity", "low")),
                summary=data.get("summary", "代码变更"),
                commit_title=data.get("commit_title", "chore: 更新代码"),
                commit_body=data.get("commit_body", ""),
                issues_found=data.get("issues_found", []),
                suggestions=data.get("suggestions", []),
                affected_files=data.get("affected_files", []),
                risk_level=data.get("risk_level", "low"),
                breaking_changes=data.get("breaking_changes", False),
                confidence_score=data.get("confidence_score", 0.8),
                raw_response=response,
            )

        except (json.JSONDecodeError, KeyError) as e:
            # 解析失败时返回默认结果
            return AIAnalysisResult(
                change_type=ChangeType.CHORE,
                severity=ChangeSeverity.LOW,
                summary="AI 分析失败，请手动审查",
                commit_title="chore: 代码更新",
                commit_body=f"AI 分析遇到错误: {e!s}\n\n请手动审查代码变更。",
                issues_found=[f"AI 解析错误: {e!s}"],
                suggestions=["建议手动检查代码变更"],
                affected_files=[],
                risk_level="medium",
                breaking_changes=False,
                confidence_score=0.0,
                raw_response=response,
            )


# ===== 快速测试功能 =====
async def test_analyzer():
    """测试 AI 分析器"""
    # 示例 Git Diff
    sample_diff = """diff --git a/src/server.py b/src/server.py
index 1234567..abcdefg 100644
--- a/src/server.py
+++ b/src/server.py
@@ -10,7 +10,7 @@ def process_request(data):
-    return {"status": "ok"}
+    return {"status": "success", "data": data}
"""

    sample_status = """On branch main
Changes to be committed:
  modified:   src/server.py
"""

    # 创建分析器（使用 Ollama 本地测试）
    analyzer = AIAnalyzer(provider=AIProvider.OLLAMA)

    # 执行分析
    result = await analyzer.analyze_git_diff(
        git_diff=sample_diff,
        git_status=sample_status,
        project_context="这是一个 Python Web 服务器项目",
    )

    print("=" * 60)
    print("AI 分析结果:")
    print("=" * 60)
    print(f"变更类型: {result.change_type.value}")
    print(f"严重性: {result.severity.value}")
    print(f"摘要: {result.summary}")
    print(f"\nCommit 标题: {result.commit_title}")
    print(f"Commit 正文:\n{result.commit_body}")
    print(f"\n发现的问题: {result.issues_found}")
    print(f"优化建议: {result.suggestions}")
    print(f"风险等级: {result.risk_level}")
    print(f"置信度: {result.confidence_score:.2%}")


if __name__ == "__main__":
    asyncio.run(test_analyzer())
