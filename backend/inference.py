import os
# Set YOLO config directory to a writable location to avoid warnings on Render
os.environ['YOLO_CONFIG_DIR'] = '/tmp/ultralytics_config'

import cv2
import numpy as np
from ultralytics import YOLO

import os
import logging

logger = logging.getLogger(__name__)

# Load YOLOv8 Nano model for fast CPU/GPU inference
# It will download yolov8n.pt automatically on first run
MODEL_PATH = "yolov8n.pt"
if not os.path.exists(MODEL_PATH):
    # Try checking the parent directory as well
    PARENT_MODEL_PATH = os.path.join("..", MODEL_PATH)
    if os.path.exists(PARENT_MODEL_PATH):
        MODEL_PATH = PARENT_MODEL_PATH
        
logger.info(f"Initializing YOLOv8 with weights from: {os.path.abspath(MODEL_PATH)}")
try:
    yolo_model = YOLO(MODEL_PATH)
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    # Fallback or placeholder might be needed, but for now we let it raise
    raise

class InferenceEngine:
    def __init__(self):
        self.prev_gray = None
        self.panic_history = []
        
    def analyze_frame(self, frame):
        """
        Runs highly accurate deterministic inference using YOLOv8 and Optical Flow.
        Returns a panic score > 90% if crowd + erratic movement is detected.
        """
        # 1. Object Detection (YOLOv8)
        # Optimized for speed with smaller imgsz and classes filter
        results = yolo_model(frame, classes=[0], imgsz=320, verbose=False)
        
        detections = []
        num_people = 0
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                conf = round(box.conf[0].item(), 2)
                detections.append({
                    "label": "person",
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf
                })
                num_people += 1

        # 2. Motion Tracking (Dense Optical Flow)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (320, 240)) # Scale down for performance
        
        motion_magnitude = 0.0
        if self.prev_gray is not None:
            # Calculate dense optical flow using Farneback
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None, 
                pyr_scale=0.5, levels=3, winsize=15, 
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            # Calculate magnitude and angle of 2D vectors
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            # Average motion magnitude in the frame
            motion_magnitude = np.mean(mag)
            
        self.prev_gray = gray

        # 3. Deterministic Panic Scoring Algorithm
        # Base logic: If there are people AND they are moving erratically, it's panic.
        
        base_score = 0.05
        
        # Crowd density factor (max 0.4 at 10 people)
        density_factor = min(num_people * 0.04, 0.4)
        
        # Motion factor (erratic motion creates spikes)
        # Normal walking is around mag=0.5 to 2.0. Panic running is mag > 5.0
        motion_factor = 0.0
        if num_people > 0:
            if motion_magnitude > 4.0:
                motion_factor = 0.6  # High erratic movement!
            elif motion_magnitude > 2.0:
                motion_factor = 0.3
            elif motion_magnitude > 0.5:
                motion_factor = 0.1
                
        # Synergistic Spike: If crowd is dense and moving fast, guarantee > 90%
        if num_people >= 3 and motion_magnitude > 3.5:
            panic_score = 0.92 + (motion_magnitude / 100.0) # E.g., 0.92 + 0.05 = 0.97
        else:
            panic_score = base_score + density_factor + motion_factor

        # Clamp between 0 and 1
        panic_score = min(max(panic_score, 0.0), 1.0)

        # Smooth out the score slightly to avoid flickering, but keep spikes sharp
        self.panic_history.append(panic_score)
        if len(self.panic_history) > 5:
            self.panic_history.pop(0)
            
        smoothed_score = sum(self.panic_history) / len(self.panic_history)
        
        # If the raw score was a major spike (>0.8), keep it sharp instead of smoothing
        final_score = panic_score if panic_score > 0.8 else smoothed_score

        alert = bool(final_score > 0.75)

        return {
            "panic_score": float(round(final_score, 3)),
            "detections": detections,
            "alert": alert,
            "motion": float(round(motion_magnitude, 2))
        }

# Global instance for the websocket
engine = InferenceEngine()

def run_inference(frame):
    """ Wrapper for the websocket """
    return engine.analyze_frame(frame)

def analyze_video_offline(video_path):
    """ Offline analysis for uploaded files. Simulates processing a chunk and returning an aggregate. """
    cap = cv2.VideoCapture(video_path)
    engine_offline = InferenceEngine()
    max_score = 0
    detections_snapshot = []
    
    frame_jump = 15 # Process 1 frame every 0.5s (assuming 30fps)
    max_total_frames = 20 # Max frames to analyze to keep it fast
    frames_processed = 0
    current_frame_idx = 0
    
    if not cap.isOpened():
        logger.error(f"Could not open video file: {video_path}")
        return {
            "panic_score": 0.0,
            "detections": [],
            "alert": False,
            "status": "Error: Could not open video"
        }

    while cap.isOpened() and frames_processed < max_total_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        if current_frame_idx % frame_jump == 0:
            try:
                result = engine_offline.analyze_frame(frame)
                if result["panic_score"] > max_score:
                    max_score = result["panic_score"]
                    detections_snapshot = result["detections"]
                frames_processed += 1
            except Exception as frame_err:
                logger.warning(f"Error processing frame at index {current_frame_idx}: {frame_err}")
            
        current_frame_idx += 1
        
    cap.release()
    
    return {
        "panic_score": float(round(max_score, 3)),
        "detections": detections_snapshot,
        "alert": bool(max_score > 0.75),
        "status": "Analysis Complete"
    }

import base64
import json

class MediaInference:
    def __init__(self):
        self.engine = InferenceEngine()
        
    @staticmethod
    def deserialize_message(message):
        return json.loads(message)
        
    def analyze_frame(self, image_b64):
        try:
            # image_b64 typically has data:image/jpeg;base64, prefix
            if "," in image_b64:
                image_b64 = image_b64.split(",")[1]
            if not image_b64:
                return self._empty_result()
                
            # Handle potential padding issues
            missing_padding = len(image_b64) % 4
            if missing_padding:
                image_b64 += '=' * (4 - missing_padding)

            img_data = base64.b64decode(image_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return self._empty_result()
                
            return self.engine.analyze_frame(frame)
        except Exception as e:
            print(f"Error decoding frame: {e}")
            return self._empty_result()
            
    def _empty_result(self):
        return {
            "panic_score": 0.0,
            "detections": [],
            "alert": False,
            "motion": 0.0
        }
        
    def analyze_audio_bytes(self, data_b64, mime_type):
        # Fake audio analysis for now
        return {"audio_score": 0.5, "confidence": 0.9}
        
    def analyze_audio(self, target_path):
        return {"panic_score": 0.5, "alert": False, "detections": []}
        
    def analyze_video(self, target_path):
        return analyze_video_offline(target_path)
        
    def analyze_media(self, video_path, audio_path):
        res = analyze_video_offline(video_path)
        return res
