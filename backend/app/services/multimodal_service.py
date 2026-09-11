"""Multimodal content extraction service for images and videos using Ollama Vision."""

import os
import base64
import logging
import hashlib
import tempfile
from typing import List, Dict, Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# Vision model to use for image description (must be pulled separately)
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "minicpm-v")

# Image extensions that can be processed
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}

# Video extensions (requires ffmpeg for keyframe extraction)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


class MultimodalService:
    """Extracts textual knowledge from images and videos via Ollama Vision LLM."""

    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.vision_model = VISION_MODEL
        self._vision_available: Optional[bool] = None

    def check_vision_model(self) -> bool:
        """Check if the vision model is available in Ollama."""
        if self._vision_available is not None:
            return self._vision_available

        try:
            resp = httpx.get(
                f"{self.ollama_url}/api/tags",
                timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
            )
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            self._vision_available = self.vision_model.split(":")[0] in model_names
            if not self._vision_available:
                logger.warning(
                    f"Vision model '{self.vision_model}' not found in Ollama. "
                    f"Available models: {model_names}. "
                    f"Run: ollama pull {self.vision_model}"
                )
            return self._vision_available
        except Exception as e:
            logger.warning(f"Cannot check Ollama models: {e}")
            self._vision_available = False
            return False

    def _image_to_base64(self, file_path: str) -> str:
        """Read image file and encode as base64 string."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def describe_image(self, file_path: str) -> str:
        """Use Ollama Vision to extract text and describe image content in detail.

        Returns a comprehensive text description including any text found in the image,
        diagrams, tables, error messages, screenshots, etc.
        """
        if not self.check_vision_model():
            return self._fallback_image_description(file_path)

        try:
            img_b64 = self._image_to_base64(file_path)
            filename = os.path.basename(file_path)

            prompt = (
                "Bạn là trợ lý AI phân tích hình ảnh chuyên nghiệp cho doanh nghiệp. "
                "Hãy phân tích toàn bộ nội dung hình ảnh này một cách chi tiết và chính xác bằng tiếng Việt:\n\n"
                "1. ĐỌC TOÀN BỘ VĂN BẢN: Nếu có bất kỳ chữ nào trong ảnh (tài liệu, bảng biểu, email, "
                "thông báo lỗi, cấu hình, dòng lệnh...), hãy trích xuất CHÍNH XÁC toàn bộ văn bản.\n"
                "2. MÔ TẢ SƠ ĐỒ/BIỂU ĐỒ: Nếu có sơ đồ mạng, biểu đồ, bảng, luồng quy trình, "
                "hãy mô tả chi tiết các thành phần và mối quan hệ.\n"
                "3. PHÂN TÍCH SCREENSHOT: Nếu là ảnh chụp màn hình phần mềm, Windows, "
                "hãy mô tả giao diện, thông báo lỗi, cấu hình, và hướng dẫn liên quan.\n"
                "4. THÔNG TIN KỸ THUẬT: Ghi nhận mọi thông số kỹ thuật, địa chỉ IP, "
                "tên thiết bị, mã lỗi, serial number.\n\n"
                f"Tên file: {filename}\n"
                "Hãy trả lời chi tiết, có cấu trúc, sử dụng tiêu đề Markdown khi cần."
            )

            timeout_config = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=30.0)
            with httpx.Client(timeout=timeout_config) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.vision_model,
                        "prompt": prompt,
                        "images": [img_b64],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 2048,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                text = result.get("response", "").strip()

                if text:
                    header = f"## Nội dung trích xuất từ hình ảnh: {filename}\n\n"
                    return header + text
                else:
                    return self._fallback_image_description(file_path)

        except Exception as e:
            logger.error(f"Vision analysis failed for {file_path}: {e}")
            return self._fallback_image_description(file_path)

    def _fallback_image_description(self, file_path: str) -> str:
        """Generate basic metadata when vision model is unavailable."""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(filename)[1].lower()

        return (
            f"## Hình ảnh: {filename}\n\n"
            f"- **Loại file**: {ext.upper().strip('.')}\n"
            f"- **Dung lượng**: {file_size / 1024:.1f} KB\n"
            f"- **Ghi chú**: Không thể phân tích nội dung chi tiết do chưa cài đặt "
            f"model Vision AI. Chạy lệnh: `ollama pull {self.vision_model}` để kích hoạt.\n"
        )

    def extract_video_knowledge(self, file_path: str) -> str:
        """Extract knowledge from video file.

        Strategy:
        1. Extract keyframes at intervals using ffmpeg (if available)
        2. Analyze each keyframe with vision model
        3. Combine into structured document

        Falls back to metadata-only if ffmpeg is not installed.
        """
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Check if ffmpeg is available
        ffmpeg_available = self._check_ffmpeg()

        if not ffmpeg_available:
            return self._fallback_video_description(file_path)

        # Extract keyframes
        try:
            keyframe_texts = []
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract 1 frame every 30 seconds, max 20 frames
                import subprocess
                result = subprocess.run(
                    [
                        "ffmpeg", "-i", file_path,
                        "-vf", "fps=1/30",
                        "-frames:v", "20",
                        "-q:v", "2",
                        os.path.join(tmpdir, "frame_%03d.jpg"),
                    ],
                    capture_output=True,
                    timeout=120,
                )

                # Get duration from ffprobe
                duration_text = "Không xác định"
                try:
                    probe = subprocess.run(
                        [
                            "ffprobe", "-v", "error",
                            "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1",
                            file_path,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if probe.stdout.strip():
                        seconds = float(probe.stdout.strip())
                        mins = int(seconds // 60)
                        secs = int(seconds % 60)
                        duration_text = f"{mins} phút {secs} giây"
                except Exception:
                    pass

                # Analyze each extracted frame
                frames = sorted(
                    [f for f in os.listdir(tmpdir) if f.endswith(".jpg")]
                )

                header = (
                    f"## Nội dung trích xuất từ video: {filename}\n\n"
                    f"- **Dung lượng**: {file_size / (1024 * 1024):.1f} MB\n"
                    f"- **Thời lượng**: {duration_text}\n"
                    f"- **Số khung hình phân tích**: {len(frames)}\n\n"
                )

                if frames and self.check_vision_model():
                    for i, frame_file in enumerate(frames):
                        frame_path = os.path.join(tmpdir, frame_file)
                        timestamp = (i + 1) * 30
                        mins = timestamp // 60
                        secs = timestamp % 60

                        description = self.describe_image(frame_path)
                        keyframe_texts.append(
                            f"### Khung hình tại {mins}:{secs:02d}\n\n{description}\n"
                        )
                elif frames:
                    header += (
                        "**Lưu ý**: Model Vision AI chưa được cài đặt. "
                        f"Chạy `ollama pull {self.vision_model}` để phân tích nội dung slide trong video.\n\n"
                    )

            return header + "\n".join(keyframe_texts)

        except FileNotFoundError:
            return self._fallback_video_description(file_path)
        except Exception as e:
            logger.error(f"Video extraction failed for {file_path}: {e}")
            return self._fallback_video_description(file_path)

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available on the system."""
        try:
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, Exception):
            return False

    def _fallback_video_description(self, file_path: str) -> str:
        """Generate basic metadata when ffmpeg is unavailable."""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(filename)[1].lower()

        return (
            f"## Video: {filename}\n\n"
            f"- **Loại file**: {ext.upper().strip('.')}\n"
            f"- **Dung lượng**: {file_size / (1024 * 1024):.1f} MB\n"
            f"- **Ghi chú**: Không thể trích xuất nội dung video do chưa cài ffmpeg. "
            f"Tải từ https://ffmpeg.org và thêm vào PATH.\n"
            f"- **Gợi ý**: Chụp màn hình các slide quan trọng và đặt vào thư mục images/ "
            f"để AI đọc và phân tích.\n"
        )

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Compute SHA-256 hash of file for deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @staticmethod
    def is_image(file_path: str) -> bool:
        """Check if file is an image by extension."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in IMAGE_EXTENSIONS

    @staticmethod
    def is_video(file_path: str) -> bool:
        """Check if file is a video by extension."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in VIDEO_EXTENSIONS

    def extract_content(self, file_path: str) -> str:
        """Universal content extractor - routes to appropriate handler."""
        if self.is_image(file_path):
            return self.describe_image(file_path)
        elif self.is_video(file_path):
            return self.extract_video_knowledge(file_path)
        else:
            raise ValueError(f"File type not supported for multimodal extraction: {file_path}")


multimodal_service = MultimodalService()
