#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Interactive Feedback Enhanced
==================================

互動式用戶回饋 MCP 伺服器，提供 AI 輔助開發中的回饋收集功能。

作者: Fábio Ferreira
增強功能: Web UI 支援、圖片上傳、現代化界面設計

特色：
- 雙介面支援（Qt GUI 和 Web UI）
- 智慧環境檢測
- 命令執行功能
- 圖片上傳支援
- 現代化深色主題
"""

__version__ = "2.0.13"
__author__ = "Minidoracat"
__email__ = "minidora0702@gmail.com"

from .server import main as run_server
from .feedback_ui import feedback_ui
from .web_ui import WebUIManager

# 主要導出介面
__all__ = [
    "run_server",
    "feedback_ui", 
    "WebUIManager",
    "__version__",
    "__author__",
]

def main():
    """主要入口點，用於 uvx 執行"""
    from .__main__ import main as cli_main
    return cli_main() 