#!/usr/bin/env python3
"""
統一調試日誌模組
================

提供統一的調試日誌功能，確保調試輸出不會干擾 MCP 通信。
所有調試輸出都會發送到 stderr，並且只在調試模式啟用時才輸出。

使用方法：
```python
from .debug import debug_log

debug_log("這是一條調試信息")
```

環境變數控制：
- MCP_DEBUG=true/1/yes/on: 啟用調試模式
- MCP_DEBUG=false/0/no/off: 關閉調試模式（默認）

作者: Minidoracat
"""

import os
import sys
from typing import Any


def _write_stderr(prefix: str, message: Any) -> None:
    """寫一行 `[prefix] message` 到 stderr；格式化與輸出的任何失敗都靜默。

    必須先抓住 sys.stderr：它在 pythonw／宿主關閉 stderr 時會是 None，而
    print(file=None) 會改寫 sys.stdout —— 那是 MCP 協定通道，一個字都不能碰。
    """
    stream = sys.stderr
    if stream is None:
        return
    try:
        line = f"[{prefix}] {message}"
        try:
            print(line, file=stream, flush=True)
        except UnicodeEncodeError:
            print(
                line.encode("ascii", errors="replace").decode("ascii"),
                file=stream,
                flush=True,
            )
    except Exception:
        # 最後的備用方案：靜默失敗，不影響主程序
        pass


def debug_log(message: Any, prefix: str = "DEBUG") -> None:
    """
    輸出調試訊息到標準錯誤，避免污染標準輸出

    Args:
        message: 要輸出的調試信息
        prefix: 調試信息的前綴標識，默認為 "DEBUG"
    """
    # 只在啟用調試模式時才輸出，避免干擾 MCP 通信
    if os.getenv("MCP_DEBUG", "").lower() not in ("true", "1", "yes", "on"):
        return
    _write_stderr(prefix, message)


def user_notice(message: Any) -> None:
    """給使用者看的提示：不受 MCP_DEBUG 控制，一律寫到 stderr（不碰 stdout 協定通道）

    用於「介面開不了、請手動開網址」這類使用者沒看到就會空等的訊息。
    與 debug_log 一樣，stderr 不可寫（例如宿主已關閉 pipe）時靜默，不影響主流程。
    """
    _write_stderr("mcp-feedback-enhanced", message)


def i18n_debug_log(message: Any) -> None:
    """國際化模組專用的調試日誌"""
    debug_log(message, "I18N")


def server_debug_log(message: Any) -> None:
    """伺服器模組專用的調試日誌"""
    debug_log(message, "SERVER")


def web_debug_log(message: Any) -> None:
    """Web UI 模組專用的調試日誌"""
    debug_log(message, "WEB")


def is_debug_enabled() -> bool:
    """檢查是否啟用了調試模式"""
    return os.getenv("MCP_DEBUG", "").lower() in ("true", "1", "yes", "on")


def set_debug_mode(enabled: bool) -> None:
    """設置調試模式（用於測試）"""
    os.environ["MCP_DEBUG"] = "true" if enabled else "false"
