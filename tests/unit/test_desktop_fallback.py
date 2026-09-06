#!/usr/bin/env python3
"""桌面模式退回 Web 的行為（桌面版退役前置修正）

MCP_DESKTOP_MODE=true 但桌面殼起不來（binary 缺失、被防毒隔離、glibc／
Gatekeeper 擋下、啟動後隨即退出）時，舊版什麼介面都不開：fallback 呼叫的
瀏覽器 opener 會因為同一個環境變數而直接 return，使用者只能空等到 timeout。

這裡守住：
1. 桌面失敗 → 本 process 改走 Web，真的把網址交給瀏覽器
2. 之後的呼叫不再重試桌面，並重用既有分頁（活躍分頁偵測）
3. 桌面健康時完全不碰瀏覽器
4. native 啟動後隨即退出算失敗
5. 瀏覽器也開不了時，網址無條件印到 stderr
"""

import subprocess
import sys
import time
import webbrowser
from unittest.mock import AsyncMock

import pytest

from mcp_feedback_enhanced.web import main as web_main
from mcp_feedback_enhanced.web.models.feedback_session import WebFeedbackSession
from mcp_feedback_enhanced.web.utils import browser


class FakeWebSocket:
    """只需要能收 send_json 的最小 WebSocket 替身"""

    def __init__(self):
        self.sent: list[dict] = []

    async def send_json(self, message):
        self.sent.append(message)


@pytest.fixture(autouse=True)
def standard_browser_path(monkeypatch):
    """開發機可能被判成 WSL（WSLENV／/mnt/c 存在）而走 cmd.exe 真的開瀏覽器；一律走標準路徑"""
    monkeypatch.setattr(browser, "is_wsl_environment", lambda: False)


@pytest.fixture
def desktop_env(monkeypatch, web_ui_manager, test_project_dir):
    """桌面模式 + 不啟動真實伺服器 + 不真的等待回饋 + 只攔最底層的 webbrowser.open"""
    monkeypatch.setenv("MCP_DESKTOP_MODE", "true")
    monkeypatch.setattr(web_main, "get_web_ui_manager", lambda: web_ui_manager)
    monkeypatch.setattr(web_ui_manager, "start_server", lambda: None)

    monkeypatch.setattr(
        WebFeedbackSession,
        "wait_for_feedback",
        AsyncMock(
            return_value={"interactive_feedback": "", "images": [], "settings": {}}
        ),
    )

    opened: list[str] = []
    monkeypatch.setattr(
        webbrowser, "open", lambda url, *a, **k: opened.append(url) or True
    )
    return web_ui_manager, str(test_project_dir), opened


def make_desktop_unavailable(monkeypatch):
    """讓發佈包與開發環境兩條 import 路徑都失敗（等同 PyPI 安裝但 binary 模組缺失）"""
    monkeypatch.setitem(sys.modules, "mcp_feedback_enhanced.desktop_app", None)
    monkeypatch.setitem(sys.modules, "mcp_feedback_enhanced_desktop", None)


class TestDesktopUnavailableFallsBackToWeb:
    @pytest.mark.asyncio
    async def test_first_call_opens_browser_and_leaves_desktop_mode(
        self, desktop_env, monkeypatch, capsys
    ):
        manager, project_dir, opened = desktop_env
        make_desktop_unavailable(monkeypatch)
        monkeypatch.setenv("MCP_DEBUG", "false")  # 提示不得只存在於 debug log

        await web_main.launch_web_feedback_ui(project_dir, "摘要", timeout=60)

        assert opened == [manager.get_server_url()], "必須真的把網址交給瀏覽器"
        assert "MCP_DESKTOP_MODE" not in web_main.os.environ, (
            "本 process 應改走 Web 模式"
        )
        err = capsys.readouterr().err
        assert manager.get_server_url() in err, "降級必須無條件告知使用者"
        assert "桌面應用程式無法啟動" in err, "失敗原因必須讓使用者看到"
        assert "mcp_feedback_enhanced_desktop" in err, "要帶出具體原因，不是固定文案"

    @pytest.mark.asyncio
    async def test_second_call_reuses_existing_tab_instead_of_retrying_desktop(
        self, desktop_env, monkeypatch
    ):
        manager, project_dir, opened = desktop_env
        make_desktop_unavailable(monkeypatch)
        await web_main.launch_web_feedback_ui(project_dir, "第一次", timeout=60)

        # 模擬第一次開出來的分頁已連上並有心跳
        tab = FakeWebSocket()
        manager.get_current_session().websocket = tab
        manager.get_current_session().last_heartbeat = time.time()

        await web_main.launch_web_feedback_ui(project_dir, "第二次", timeout=60)

        assert len(opened) == 1, "第二次不得再開新分頁"
        assert any(m.get("type") == "session_updated" for m in tab.sent), (
            "既有分頁必須收到新會話通知"
        )


class TestHealthyDesktopDoesNotTouchBrowser:
    @pytest.mark.asyncio
    async def test_desktop_success_keeps_mode_and_opens_nothing(
        self, desktop_env, monkeypatch
    ):
        manager, project_dir, opened = desktop_env

        async def launched(url):
            return True

        monkeypatch.setattr(manager, "launch_desktop_app", launched)

        await web_main.launch_web_feedback_ui(project_dir, "摘要", timeout=60)

        assert opened == []
        assert web_main.os.environ.get("MCP_DESKTOP_MODE") == "true"


@pytest.fixture
def fake_desktop_binary(monkeypatch, tmp_path):
    """讓 launch_tauri_app 找到一個假的平台 binary，測試不依賴入庫的真 binary"""
    import platform

    from mcp_feedback_enhanced import desktop_release

    names = {
        "windows": "mcp-feedback-enhanced-desktop.exe",
        "darwin": "mcp-feedback-enhanced-desktop-macos-arm64",
        "linux": "mcp-feedback-enhanced-desktop-linux",
    }
    (
        tmp_path / names.get(platform.system().lower(), "mcp-feedback-enhanced-desktop")
    ).touch()
    (tmp_path / "mcp-feedback-enhanced-desktop-macos-intel").touch()
    monkeypatch.setattr(desktop_release, "__file__", str(tmp_path / "__init__.py"))


def popen_returning(process, monkeypatch):
    """只在啟動桌面 binary 時回傳替身；platform.system() 等內部 Popen 照常"""
    real_popen = subprocess.Popen

    def popen(args, *a, **k):
        if isinstance(args, list) and "mcp-feedback-enhanced-desktop" in args[0]:
            return process
        return real_popen(args, *a, **k)

    monkeypatch.setattr(subprocess, "Popen", popen)


class TestNativeEarlyExitIsLaunchFailure:
    @pytest.mark.asyncio
    async def test_non_zero_exit_during_startup_raises(
        self, monkeypatch, fake_desktop_binary
    ):
        """Popen 成功但 native 隨即失敗退出（Defender／glibc／Gatekeeper）不能被當成啟動成功"""
        from mcp_feedback_enhanced.desktop_app import desktop_app

        class ExitedProcess:
            def poll(self):
                return 127

            def communicate(self, timeout=None):
                return (
                    b"",
                    b"error while loading shared libraries: GLIBC_2.39 not found",
                )

        popen_returning(ExitedProcess(), monkeypatch)
        monkeypatch.setattr(desktop_app.asyncio, "sleep", _no_sleep)

        app = desktop_app.DesktopApp()
        with pytest.raises(RuntimeError, match=r"隨即退出.*127.*GLIBC"):
            await app.launch_tauri_app("http://127.0.0.1:8765")
        assert app.app_handle is None

    @pytest.mark.asyncio
    async def test_stderr_held_by_descendant_does_not_hang(
        self, monkeypatch, fake_desktop_binary
    ):
        """WebView 等後代程序握著 stderr 寫端時，讀尾段有上限，逾時只報 exit code"""
        from mcp_feedback_enhanced.desktop_app import desktop_app

        class HangingStderr:
            """像真實 Popen：有 timeout 就在期限內拋 TimeoutExpired，沒有就一直等後代關閉 pipe"""

            def poll(self):
                return 1

            def communicate(self, timeout=None):
                if timeout is None:
                    time.sleep(3)  # 模擬後代握著 stderr：無上限讀取會卡在這裡
                    return b"", b""
                time.sleep(min(timeout, 3))
                raise subprocess.TimeoutExpired(cmd="desktop", timeout=timeout)

        popen_returning(HangingStderr(), monkeypatch)
        monkeypatch.setattr(desktop_app.asyncio, "sleep", _no_sleep)

        app = desktop_app.DesktopApp()
        start = time.monotonic()
        with pytest.raises(RuntimeError, match=r"exit code 1"):
            await app.launch_tauri_app("http://127.0.0.1:8765")
        assert time.monotonic() - start < 2.5, "讀取 stderr 尾段必須有上限"

    @pytest.mark.asyncio
    async def test_clean_exit_during_startup_is_not_failure(
        self, monkeypatch, fake_desktop_binary
    ):
        """使用者在觀察期內自己關掉視窗（exit 0）沿用既有語意，不能被降級成 Web"""
        from mcp_feedback_enhanced.desktop_app import desktop_app

        class ClosedByUser:
            def poll(self):
                return 0

        popen_returning(ClosedByUser(), monkeypatch)
        monkeypatch.setattr(desktop_app.asyncio, "sleep", _no_sleep)

        app = desktop_app.DesktopApp()
        await app.launch_tauri_app("http://127.0.0.1:8765")
        assert app.app_handle is not None


def test_launcher_copies_stay_identical():
    """build_desktop.py 會用 src-tauri/python 覆蓋發佈版；兩份漂移過一次，用位元組比對守住"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    shipped = root / "src/mcp_feedback_enhanced/desktop_app/desktop_app.py"
    source = root / "src-tauri/python/mcp_feedback_enhanced_desktop/desktop_app.py"
    assert shipped.read_bytes() == source.read_bytes()


class TestBrowserOpenFailureIsSurfaced:
    def test_false_from_webbrowser_prints_url_to_stderr(
        self, web_ui_manager, monkeypatch, capsys
    ):
        monkeypatch.delenv("MCP_DESKTOP_MODE", raising=False)
        monkeypatch.setenv("MCP_DEBUG", "false")
        monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: False)

        assert web_ui_manager.open_browser("http://127.0.0.1:9999") is False
        assert "http://127.0.0.1:9999" in capsys.readouterr().err


async def _no_sleep(_seconds):
    return None
