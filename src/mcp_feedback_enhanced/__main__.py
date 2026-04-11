#!/usr/bin/env python3
"""
MCP Interactive Feedback Enhanced - 主程式入口
==============================================

此檔案允許套件透過 `python -m mcp_feedback_enhanced` 執行。

使用方法:
  python -m mcp_feedback_enhanced        # 啟動 MCP 伺服器
  python -m mcp_feedback_enhanced test   # 執行測試
"""

import argparse
import asyncio
import os
import sys
import warnings


# 抑制 Windows 上的 asyncio ResourceWarning
if sys.platform == "win32":
    warnings.filterwarnings(
        "ignore", category=ResourceWarning, message=".*unclosed transport.*"
    )
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")

    # 設置 asyncio 事件循環策略以減少警告
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass


def main():
    """主程式入口點"""
    parser = argparse.ArgumentParser(
        description="MCP Feedback Enhanced Enhanced - 互動式回饋收集 MCP 伺服器"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 伺服器命令（預設）
    subparsers.add_parser("server", help="啟動 MCP 伺服器（預設）")

    # 測試命令
    test_parser = subparsers.add_parser("test", help="執行測試")
    test_parser.add_argument(
        "--web", action="store_true", help="測試 Web UI (自動持續運行)"
    )
    test_parser.add_argument(
        "--desktop", action="store_true", help="啟動桌面應用程式模式"
    )
    test_parser.add_argument(
        "--timeout", type=int, default=60, help="測試超時時間 (秒)"
    )

    # 版本命令
    subparsers.add_parser("version", help="顯示版本資訊")

    args = parser.parse_args()

    if args.command == "test":
        run_tests(args)
    elif args.command == "version":
        show_version()
    elif args.command == "server" or args.command is None:
        run_server()
    else:
        # 不應該到達這裡
        parser.print_help()
        sys.exit(1)


def run_server():
    """啟動 MCP 伺服器"""
    from .server import main as server_main

    return server_main()


def run_tests(args):
    """執行測試"""
    # 啟用調試模式以顯示測試過程
    os.environ["MCP_DEBUG"] = "true"

    # 在 Windows 上抑制 asyncio 警告
    if sys.platform == "win32":
        import warnings

        # 設置更全面的警告抑制
        os.environ["PYTHONWARNINGS"] = (
            "ignore::ResourceWarning,ignore::DeprecationWarning"
        )
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", message=".*unclosed transport.*")
        warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
        warnings.filterwarnings("ignore", message=".*unclosed.*")
        # 抑制 asyncio 相關的所有警告
        warnings.filterwarnings("ignore", module="asyncio.*")

    if args.web:
        print("🧪 執行 Web UI 測試...")
        success = test_web_ui_simple()
        if not success:
            sys.exit(1)
    elif args.desktop:
        print("🖥️ 啟動桌面應用程式...")
        success = test_desktop_app()
        if not success:
            sys.exit(1)
    else:
        print("❌ 測試功能已簡化")
        print("💡 可用的測試選項：")
        print("  --web         測試 Web UI")
        print("  --desktop     啟動桌面應用程式")
        print("💡 對於開發者：使用 'uv run pytest' 執行完整測試")
        sys.exit(1)


def test_web_ui_simple():
    """簡單的 Web UI 測試"""
    try:
        import tempfile
        import time
        import webbrowser

        from .web.main import WebUIManager

        # 設置測試模式，禁用自動清理避免權限問題
        os.environ["MCP_TEST_MODE"] = "true"
        os.environ["MCP_WEB_HOST"] = "127.0.0.1"
        # 設置更高的端口範圍避免系統保留端口
        os.environ["MCP_WEB_PORT"] = "9765"

        print("🔧 創建 Web UI 管理器...")
        manager = WebUIManager()  # 使用環境變數控制主機和端口

        # 顯示最終使用的端口（可能因端口佔用而自動切換）
        if manager.port != 9765:
            print(f"💡 端口 9765 被佔用，已自動切換到端口 {manager.port}")

        print("🔧 創建測試會話...")
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_test_content = """# Web UI 測試 - Markdown 渲染功能

## 🎯 測試目標
驗證 **combinedSummaryContent** 區域的 Markdown 語法顯示功能

### ✨ 支援的語法特性

#### 文字格式
- **粗體文字** 使用雙星號
- *斜體文字* 使用單星號
- ~~刪除線文字~~ 使用雙波浪號
- `行內程式碼` 使用反引號

#### 程式碼區塊
```javascript
// JavaScript 範例
function renderMarkdown(content) {
    return marked.parse(content);
}
```

```python
# Python 範例
def process_feedback(data):
    return {"status": "success", "data": data}
```

#### 列表功能
**無序列表：**
- 第一個項目
- 第二個項目
  - 巢狀項目 1
  - 巢狀項目 2
- 第三個項目

**有序列表：**
1. 初始化 Markdown 渲染器
2. 載入 marked.js 和 DOMPurify
3. 配置安全選項
4. 渲染內容

#### 連結和引用
- 專案連結：[MCP Feedback Enhanced](https://github.com/example/mcp-feedback-enhanced)
- 文檔連結：[Marked.js 官方文檔](https://marked.js.org/)

> **重要提示：** 所有 HTML 輸出都經過 DOMPurify 清理，確保安全性。

#### 表格範例（窄表格）
| 功能 | 狀態 | 說明 |
|------|------|------|
| 標題渲染 | ✅ | 支援 H1-H6 |
| 程式碼高亮 | ✅ | 基本語法高亮 |
| 列表功能 | ✅ | 有序/無序列表 |
| 連結處理 | ✅ | 安全連結渲染 |

#### 寬表格測試（水平滾動）
| 模組名稱 | 版本號 | 作者 | 授權協議 | 最後更新日期 | 下載次數 | 依賴數量 | 相容性 | 說明描述 | 備註資訊 |
|----------|--------|------|----------|-------------|---------|---------|--------|----------|----------|
| marked | 12.0.1 | Christopher Jeffrey | MIT License | 2024-03-15 | 15,234,567 | 0 | Node 16+ | Markdown 解析器和編譯器 | 用於渲染 AI 摘要內容 |
| dompurify | 3.0.8 | Mario Heiderich | Apache 2.0 | 2024-02-28 | 8,765,432 | 0 | 所有瀏覽器 | XSS 清理工具 | 確保 HTML 安全性 |
| fastapi | 0.110.0 | Sebastián Ramírez | MIT License | 2024-03-10 | 5,432,100 | 12 | Python 3.8+ | 現代 Web 框架 | 後端 API 服務 |

---

### 🔒 安全特性
- XSS 防護：使用 DOMPurify 清理
- 白名單標籤：僅允許安全的 HTML 標籤
- URL 驗證：限制允許的 URL 協議

### 📝 長文字段落測試

這是一段非常長的文字，用於測試當 AI 摘要內容超過可視區域高度時，左側面板是否能夠正確顯示垂直滾動條，同時右側回饋輸入區域保持固定不動。在水平佈局模式下，左側的 AI 工作摘要區域應該獨立滾動，這對於閱讀大量 AI 分析報告非常重要。使用者應該能夠通過鼠標滾輪在左側區域上下滾動，而不會導致整個頁面跟著滾動。

#### 長程式碼行測試
```python
# 這是一行非常長的程式碼，用於測試代碼區塊的水平滾動功能
def very_long_function_name_for_testing_horizontal_scroll(parameter_one, parameter_two, parameter_three, parameter_four, parameter_five, parameter_six, parameter_seven, parameter_eight):
    result = parameter_one + parameter_two + parameter_three + parameter_four + parameter_five + parameter_six + parameter_seven + parameter_eight
    return {"status": "success", "message": "This is a very long return value to test horizontal scrolling in code blocks", "data": result, "metadata": {"timestamp": "2024-03-15T10:30:00Z", "version": "1.0.0"}}
```

#### 更多文字內容

在軟體開發中，良好的 UI/UX 設計對於提升使用者體驗至關重要。當我們處理大量文字內容時，需要確保滾動行為符合使用者的預期。在雙欄佈局中，每個面板應該有獨立的滾動區域，這樣使用者可以在閱讀左側的 AI 分析結果的同時，右側的回饋輸入框始終保持可見，方便隨時輸入回饋意見。

這種設計模式在很多現代 Web 應用中都很常見，例如：
- **VS Code**：左側檔案樹和右側編輯器各自獨立滾動
- **Slack**：左側頻道列表和右側聊天訊息各自獨立滾動
- **GitHub**：程式碼審查時，左右兩側的 diff 各自獨立滾動

### 📝 測試結果
如果您能看到上述內容以正確的格式顯示，表示 Markdown 渲染功能運作正常！"""

            created_session_id = manager.create_session(temp_dir, markdown_test_content)

            if created_session_id:
                print("✅ 會話創建成功")

                print("🚀 啟動 Web 服務器...")
                manager.start_server()
                time.sleep(5)  # 等待服務器完全啟動

                if (
                    manager.server_thread is not None
                    and manager.server_thread.is_alive()
                ):
                    print("✅ Web 服務器啟動成功")
                    url = f"http://{manager.host}:{manager.port}"
                    print(f"🌐 服務器運行在: {url}")

                    # 如果端口有變更，額外提醒
                    if manager.port != 9765:
                        print(
                            f"📌 注意：由於端口 9765 被佔用，服務已切換到端口 {manager.port}"
                        )

                    # 嘗試開啟瀏覽器
                    print("🌐 正在開啟瀏覽器...")
                    try:
                        webbrowser.open(url)
                        print("✅ 瀏覽器已開啟")
                    except Exception as e:
                        print(f"⚠️  無法自動開啟瀏覽器: {e}")
                        print(f"💡 請手動開啟瀏覽器並訪問: {url}")

                    print("📝 Web UI 測試完成，進入持續模式...")
                    print("💡 提示：服務器將持續運行，可在瀏覽器中測試互動功能")
                    print("💡 按 Ctrl+C 停止服務器")

                    try:
                        # 保持服務器運行
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n🛑 停止服務器...")
                        return True
                else:
                    print("❌ Web 服務器啟動失敗")
                    return False
            else:
                print("❌ 會話創建失敗")
                return False

    except Exception as e:
        print(f"❌ Web UI 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 清理測試環境變數
        os.environ.pop("MCP_TEST_MODE", None)
        os.environ.pop("MCP_WEB_HOST", None)
        os.environ.pop("MCP_WEB_PORT", None)


def test_desktop_app():
    """測試桌面應用程式"""
    try:
        print("🔧 檢查桌面應用程式依賴...")

        # 檢查是否有 Tauri 桌面模組
        try:
            import os
            import sys

            # 嘗試導入桌面應用程式模組
            def import_desktop_app():
                # 首先嘗試從發佈包位置導入
                try:
                    from .desktop_app import launch_desktop_app as desktop_func

                    print("✅ 找到發佈包中的桌面應用程式模組")
                    return desktop_func
                except ImportError:
                    print("🔍 發佈包中未找到桌面應用程式模組，嘗試開發環境...")

                # 回退到開發環境路徑
                tauri_python_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "src-tauri", "python"
                )
                if os.path.exists(tauri_python_path):
                    sys.path.insert(0, tauri_python_path)
                    print(f"✅ 找到 Tauri Python 模組路徑: {tauri_python_path}")
                    try:
                        from mcp_feedback_enhanced_desktop import (  # type: ignore
                            launch_desktop_app as dev_func,
                        )

                        return dev_func
                    except ImportError:
                        print("❌ 無法從開發環境路徑導入桌面應用程式模組")
                        return None
                else:
                    print(f"⚠️  開發環境路徑不存在: {tauri_python_path}")
                    print("💡 這可能是 PyPI 安裝的版本，桌面應用功能不可用")
                    return None

            launch_desktop_app_func = import_desktop_app()
            if launch_desktop_app_func is None:
                print("❌ 桌面應用程式不可用")
                print("💡 可能的原因：")
                print("   1. 此版本不包含桌面應用程式二進制檔案")
                print("   2. 請使用包含桌面應用的版本，或使用 Web 模式")
                print("   3. Web 模式指令：uvx mcp-feedback-enhanced test --web")
                return False

            print("✅ 桌面應用程式模組導入成功")

        except ImportError as e:
            print(f"❌ 無法導入桌面應用程式模組: {e}")
            print(
                "💡 請確保已執行 'make build-desktop' 或 'python scripts/build_desktop.py'"
            )
            return False

        print("🚀 啟動桌面應用程式...")

        # 設置桌面模式環境變數
        os.environ["MCP_DESKTOP_MODE"] = "true"

        # 使用 asyncio 啟動桌面應用程式
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 使用 WebUIManager 來管理桌面應用實例
            from .web.main import get_web_ui_manager

            manager = get_web_ui_manager()

            # 啟動桌面應用並保存實例到 manager
            app = loop.run_until_complete(launch_desktop_app_func(test_mode=True))
            manager.desktop_app_instance = app

            print("✅ 桌面應用程式啟動成功")
            print("💡 桌面應用程式正在運行，按 Ctrl+C 停止...")

            # 保持應用程式運行
            try:
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 停止桌面應用程式...")
                app.stop()
                return True

        except Exception as e:
            print(f"❌ 桌面應用程式啟動失敗: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            loop.close()

    except Exception as e:
        print(f"❌ 桌面應用程式測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 清理環境變數
        os.environ.pop("MCP_DESKTOP_MODE", None)


async def wait_for_process(process):
    """等待進程結束"""
    try:
        # 等待進程自然結束
        await process.wait()

        # 確保管道正確關閉
        try:
            if hasattr(process, "stdout") and process.stdout:
                process.stdout.close()
            if hasattr(process, "stderr") and process.stderr:
                process.stderr.close()
            if hasattr(process, "stdin") and process.stdin:
                process.stdin.close()
        except Exception as close_error:
            print(f"關閉進程管道時出錯: {close_error}")

    except Exception as e:
        print(f"等待進程時出錯: {e}")


def show_version():
    """顯示版本資訊"""
    from . import __author__, __version__

    print(f"MCP Feedback Enhanced Enhanced v{__version__}")
    print(f"作者: {__author__}")
    print("GitHub: https://github.com/Minidoracat/mcp-feedback-enhanced")


if __name__ == "__main__":
    main()
