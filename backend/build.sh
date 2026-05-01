#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Pre-download the YOLOv8 model weights so they are baked into the deployment
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Create temp directory
mkdir -p /tmp/veera_uploads
