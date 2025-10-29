#!/usr/bin/env python3
"""
AI 分析 API 路由
===============

提供 AI 代码分析相关的 API 端点。
"""

import asyncio
import os
import subprocess
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...ai import AIAnalyzer, AIProvider
from ...debug import web_debug_log as debug_log


# 创建路由器
router = APIRouter()


class AnalyzeCodeRequest(BaseModel):
    """代码分析请求模型"""

    project_dir: str
    context: str = ""


class AnalyzeCodeResponse(BaseModel):
    """代码分析响应模型"""

    success: bool
    analysis: dict[str, Any] | None = None
    error: str | None = None


def get_git_diff(project_dir: str) -> tuple[str, str]:
    """
    获取 Git 状态和差异

    Args:
        project_dir: 项目目录

    Returns:
        tuple: (git_status, git_diff)
    """
    try:
        # 切换到项目目录
        original_dir = os.getcwd()
        os.chdir(project_dir)

        # 获取 git status
        status_result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        git_status = status_result.stdout

        # 获取 staged 和 unstaged 的 diff
        diff_staged = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        diff_unstaged = subprocess.run(
            ["git", "diff"], capture_output=True, text=True, check=True, timeout=10
        )

        # 合并 diff
        git_diff = ""
        if diff_staged.stdout:
            git_diff += "=== Staged Changes ===\n" + diff_staged.stdout + "\n"
        if diff_unstaged.stdout:
            git_diff += "=== Unstaged Changes ===\n" + diff_unstaged.stdout

        # 恢复原目录
        os.chdir(original_dir)

        return git_status, git_diff

    except subprocess.CalledProcessError as e:
        debug_log(f"Git 命令执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"Git 命令失败: {e}")
    except subprocess.TimeoutExpired:
        debug_log("Git 命令超时")
        raise HTTPException(status_code=500, detail="Git 命令执行超时")
    finally:
        # 确保恢复原目录
        try:
            os.chdir(original_dir)
        except Exception:
            pass


@router.post("/api/ai/analyze-code", response_model=AnalyzeCodeResponse)
async def analyze_code(request: AnalyzeCodeRequest) -> AnalyzeCodeResponse:
    """
    分析代码变更

    使用 AI 分析当前的 Git 代码变更，生成智能建议。
    """
    try:
        debug_log(f"收到 AI 分析请求，项目目录: {request.project_dir}")

        # 检查是否启用 AI 功能
        ai_enabled = os.getenv("MCP_AI_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        if not ai_enabled:
            return AnalyzeCodeResponse(
                success=False, error="AI 功能未启用。请设置 MCP_AI_ENABLED=true 环境变量。"
            )

        # 获取 Git 差异
        git_status, git_diff = get_git_diff(request.project_dir)

        if not git_diff.strip():
            return AnalyzeCodeResponse(
                success=False, error="没有检测到代码变更。请先修改文件后再分析。"
            )

        # 确定 AI 提供商
        provider_name = os.getenv("MCP_AI_PROVIDER", "ollama").lower()
        provider_map = {
            "openai": AIProvider.OPENAI,
            "anthropic": AIProvider.ANTHROPIC,
            "claude": AIProvider.ANTHROPIC,
            "ollama": AIProvider.OLLAMA,
        }
        provider = provider_map.get(provider_name, AIProvider.OLLAMA)

        debug_log(f"使用 AI 提供商: {provider.value}")

        # 创建 AI 分析器
        analyzer = AIAnalyzer(provider=provider)

        # 执行分析
        result = await analyzer.analyze_git_diff(
            git_diff=git_diff, git_status=git_status, project_context=request.context
        )

        # 转换结果为字典
        analysis_data = {
            "change_type": result.change_type.value,
            "severity": result.severity.value,
            "summary": result.summary,
            "commit_title": result.commit_title,
            "commit_body": result.commit_body,
            "issues_found": result.issues_found,
            "suggestions": result.suggestions,
            "affected_files": result.affected_files,
            "risk_level": result.risk_level,
            "breaking_changes": result.breaking_changes,
            "confidence_score": result.confidence_score,
        }

        debug_log(f"AI 分析完成: {result.summary}")

        return AnalyzeCodeResponse(success=True, analysis=analysis_data)

    except HTTPException:
        raise
    except Exception as e:
        debug_log(f"AI 分析失败: {e}")
        return AnalyzeCodeResponse(success=False, error=f"分析失败: {e!s}")


@router.get("/api/ai/status")
async def get_ai_status() -> dict[str, Any]:
    """
    获取 AI 功能状态

    返回当前 AI 配置和可用性信息。
    """
    ai_enabled = os.getenv("MCP_AI_ENABLED", "false").lower() in ("true", "1", "yes")
    provider = os.getenv("MCP_AI_PROVIDER", "ollama")
    model = os.getenv("MCP_AI_MODEL", "")

    # 检查 API 密钥是否配置
    has_api_key = False
    if provider == "openai":
        has_api_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("MCP_AI_API_KEY"))
    elif provider in ("anthropic", "claude"):
        has_api_key = bool(
            os.getenv("ANTHROPIC_API_KEY") or os.getenv("MCP_AI_API_KEY")
        )
    elif provider == "ollama":
        has_api_key = True  # Ollama 不需要 API 密钥

    return {
        "enabled": ai_enabled,
        "provider": provider,
        "model": model or "默认模型",
        "configured": has_api_key,
        "status": "ready" if (ai_enabled and has_api_key) else "not_configured",
    }
