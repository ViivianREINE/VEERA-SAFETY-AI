import os
from pathlib import Path

# Use /tmp for temporary storage as it is guaranteed to be writable on Render
TEMP_DIR = Path("/tmp/veera_uploads")

ALLOWED_UPLOAD_TYPES = {"video", "audio", "video_audio"}
ALLOWED_AUDIO_TYPES = {"mp3", "wav", "m4a", "webm"}
ALLOWED_VIDEO_TYPES = {"mp4", "avi", "mov", "mkv", "webm"}
