import os
from pathlib import Path

# Use absolute path for TEMP_DIR to avoid issues on deployment platforms
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = BASE_DIR / "temp"

ALLOWED_UPLOAD_TYPES = {"video", "audio", "video_audio"}
ALLOWED_AUDIO_TYPES = {"mp3", "wav", "m4a", "webm"}
ALLOWED_VIDEO_TYPES = {"mp4", "avi", "mov", "mkv", "webm"}
