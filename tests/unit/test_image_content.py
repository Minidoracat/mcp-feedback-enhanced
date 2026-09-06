#!/usr/bin/env python3
"""
圖片序列化回歸測試（issues #154 / #168 / #180 等）

舊實作回傳 fastmcp.utilities.types.Image，在 FastMCP 3.x 下會讓 tools/call
失敗：「Output validation error: outputSchema defined but no structured output
returned」。v2.6.1 改為回傳標準 mcp.types.ImageContent，FastMCP 會正確
辨識為 content block。

這些測試守住輸出型別與 base64 往返正確性。
"""

import base64

import pytest
from mcp.types import ImageContent

from mcp_feedback_enhanced.server import process_images
from mcp_feedback_enhanced.web.models.feedback_session import WebFeedbackSession


# 最小合法 1x1 PNG
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


class TestProcessImagesOutputType:
    """輸出必須是標準 MCP ImageContent"""

    def test_returns_image_content_objects(self):
        result = process_images([{"data": PNG_BYTES, "name": "shot.png"}])

        assert len(result) == 1
        assert isinstance(result[0], ImageContent)
        assert result[0].type == "image"

    def test_does_not_return_fastmcp_image(self):
        """不得再回傳 fastmcp 的 Image 型別（會觸發 output validation 錯誤）"""
        result = process_images([{"data": PNG_BYTES, "name": "shot.png"}])

        assert type(result[0]) is ImageContent, (
            f"預期 mcp.types.ImageContent，實際為 {type(result[0])}"
        )

    def test_serializes_to_wire_format(self):
        """序列化後必須是 MCP content block 的 wire 欄位（camelCase）"""
        result = process_images([{"data": PNG_BYTES, "name": "shot.png"}])
        dumped = result[0].model_dump(by_alias=True)

        assert dumped["type"] == "image"
        assert dumped["mimeType"] == "image/png"
        assert isinstance(dumped["data"], str)


class TestImageDataRoundTrip:
    """base64 往返必須無損"""

    def test_bytes_input_round_trip(self):
        result = process_images([{"data": PNG_BYTES, "name": "shot.png"}])

        assert base64.b64decode(result[0].data) == PNG_BYTES

    def test_base64_string_input_round_trip(self):
        encoded = base64.b64encode(PNG_BYTES).decode("ascii")
        result = process_images([{"data": encoded, "name": "shot.png"}])

        assert base64.b64decode(result[0].data) == PNG_BYTES

    def test_output_is_clean_base64(self):
        """輸出不得含換行等雜訊，避免客戶端解析失敗"""
        noisy = base64.encodebytes(PNG_BYTES).decode("ascii")  # 含換行
        result = process_images([{"data": noisy.replace("\n", ""), "name": "s.png"}])

        assert "\n" not in result[0].data
        assert base64.b64decode(result[0].data, validate=True) == PNG_BYTES


class TestMimeTypeDetection:
    """MIME 類型依副檔名推斷"""

    def test_known_extensions(self):
        cases = {
            "a.png": "image/png",
            "b.jpg": "image/jpeg",
            "c.jpeg": "image/jpeg",
            "d.gif": "image/gif",
            "e.webp": "image/webp",
        }
        images = [{"data": PNG_BYTES, "name": name} for name in cases]

        result = process_images(images)

        assert [c.mime_type for c in result] == list(cases.values())

    def test_unknown_extension_defaults_to_png(self):
        result = process_images([{"data": PNG_BYTES, "name": "weird.bin"}])

        assert result[0].mime_type == "image/png"

    def test_extension_is_case_insensitive(self):
        result = process_images([{"data": PNG_BYTES, "name": "SHOT.JPEG"}])

        assert result[0].mime_type == "image/jpeg"


class TestInvalidInputHandling:
    """壞資料必須被跳過，不得中斷整批處理"""

    def test_empty_and_missing_data_skipped(self):
        result = process_images(
            [
                {"name": "no-data.png"},
                {"data": "", "name": "empty.png"},
                {"data": PNG_BYTES, "name": "good.png"},
            ]
        )

        assert len(result) == 1

    def test_invalid_base64_skipped(self):
        """非法 base64 必須被擋下，不得產出無效 content"""
        result = process_images(
            [
                {"data": "!!!not-base64!!!", "name": "bad.png"},
                {"data": PNG_BYTES, "name": "good.png"},
            ]
        )

        assert len(result) == 1
        assert base64.b64decode(result[0].data) == PNG_BYTES

    def test_unsupported_type_skipped(self):
        result = process_images([{"data": 12345, "name": "int.png"}])

        assert result == []


class TestSessionToServerContract:
    """固定 session → server 的圖片資料流契約

    WebFeedbackSession._process_images 會把前端傳來的 base64 解碼為 bytes，
    因此 server.process_images 在正常流程中只會走 bytes 路徑。
    若這個契約改變（例如改傳 base64 字串），這裡會失敗——
    屆時要一併確認 process_images 的 str 路徑仍正確。
    """

    @pytest.mark.asyncio
    async def test_session_emits_bytes_and_server_accepts_it(self, test_project_dir):
        session = WebFeedbackSession("img-flow", str(test_project_dir), "測試摘要")
        try:
            await session.submit_feedback(
                "文字回饋",
                [
                    {
                        "name": "shot.png",
                        "data": base64.b64encode(PNG_BYTES).decode("ascii"),
                        "size": len(PNG_BYTES),
                    }
                ],
                {},
            )

            assert len(session.images) == 1
            assert isinstance(session.images[0]["data"], bytes), (
                "session 應輸出 bytes；若改為 str，請確認 process_images 的 str 路徑"
            )

            result = process_images(session.images)

            assert len(result) == 1
            assert isinstance(result[0], ImageContent)
            assert result[0].mime_type == "image/png"
            assert base64.b64decode(result[0].data) == PNG_BYTES
        finally:
            session._cleanup_sync()
