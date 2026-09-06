#!/usr/bin/env python3
"""stderr 提示絕不能碰到 stdout（MCP 協定通道）

`print(file=sys.stderr)` 在 sys.stderr 為 None（pythonw、宿主關閉 stderr）時
會退回 sys.stdout —— 一行提示就足以讓 MCP 客戶端解析失敗。
"""

import io
import sys

import pytest

from mcp_feedback_enhanced import debug


@pytest.mark.parametrize("writer", [debug.user_notice, debug.debug_log])
def test_never_writes_to_stdout_when_stderr_is_none(monkeypatch, writer):
    monkeypatch.setenv("MCP_DEBUG", "true")
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", None)

    writer("http://127.0.0.1:1")

    assert stdout.getvalue() == ""


def test_user_notice_ignores_mcp_debug(monkeypatch, capsys):
    monkeypatch.setenv("MCP_DEBUG", "false")

    debug.user_notice("請手動開啟")

    assert "請手動開啟" in capsys.readouterr().err


def test_user_notice_survives_closed_stderr(monkeypatch):
    closed = io.StringIO()
    closed.close()
    monkeypatch.setattr(sys, "stderr", closed)

    debug.user_notice("x")  # 不得拋出
