import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.logger import logger

try:
    from backend.config import TEMP_DIR, ALLOWED_UPLOAD_TYPES, ALLOWED_AUDIO_TYPES, ALLOWED_VIDEO_TYPES
    from backend.inference import MediaInference
    from backend.database import log_analysis, get_logs
except ImportError:
    from config import TEMP_DIR, ALLOWED_UPLOAD_TYPES, ALLOWED_AUDIO_TYPES, ALLOWED_VIDEO_TYPES
    from inference import MediaInference
    from database import log_analysis, get_logs

app = FastAPI(title="VEERA_SAFETY_AI - Elite Crowd Safety Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR.mkdir(exist_ok=True)

inference_engine = MediaInference()

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "VEERA_SAFETY_AI backend is alive."}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
):
    """Upload a video or audio file and analyze it with the multimodal AI engine."""
    if upload_type not in ALLOWED_UPLOAD_TYPES:
        return JSONResponse({"error": "Unsupported upload_type"}, status_code=400)

    suffix = file.filename.split(".")[-1].lower()
    if upload_type == "audio" and suffix not in ALLOWED_AUDIO_TYPES:
        return JSONResponse({"error": "Unsupported audio format"}, status_code=400)

    if upload_type in ["video", "video_audio"] and suffix not in ALLOWED_VIDEO_TYPES:
        return JSONResponse({"error": "Unsupported video format"}, status_code=400)

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    target_path = TEMP_DIR / filename

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        logger.info(f"Starting analysis for {file.filename} (type: {upload_type})")
        if upload_type == "audio":
            result = inference_engine.analyze_audio(str(target_path))
        elif upload_type == "video":
            result = inference_engine.analyze_video(str(target_path))
        else:
            result = inference_engine.analyze_media(str(target_path), str(target_path))

        # Log to database
        log_analysis(
            media_type=upload_type,
            filename=file.filename,
            panic_score=result.get("panic_score", 0.0),
            alert=result.get("alert", False),
            detections_count=len(result.get("detections", []))
        )
        
        logger.info(f"Analysis successful for {file.filename}")
        return {"filename": file.filename, "type": upload_type, "results": result}
    except Exception as exc:
        logger.error(f"Analysis failure for {file.filename}: {exc}", exc_info=True)
        return JSONResponse(
            {"error": "Analysis failed", "detail": str(exc)}, 
            status_code=500
        )
    finally:
        # Optional: cleanup temp file if needed
        # if target_path.exists(): target_path.unlink()
        pass

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    media_type: str = Form("video_audio"),
):
    """Analyze an uploaded file using the same multimodal inference pipeline."""
    return await upload_file(file=file, upload_type=media_type)

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_engine = MediaInference()
    logger.info("WebSocket client connected for live inference")

    try:
        while True:
            try:
                message = await websocket.receive_text()
                payload = MediaInference.deserialize_message(message)
                if payload["type"] == "frame":
                    result = session_engine.analyze_frame(payload["data"])
                    await websocket.send_json({
                        "type": "result",
                        "score": result["panic_score"],
                        "detections": result["detections"],
                        "alert": result["alert"],
                        "motion": result["motion"],
                        "audio_score": result.get("audio_score", None),
                    })
                elif payload["type"] == "audio":
                    result = session_engine.analyze_audio_bytes(payload["data"], payload.get("mime_type", "audio/webm"))
                    await websocket.send_json({
                        "type": "audio_result",
                        "audio_score": result["audio_score"],
                        "confidence": result["confidence"],
                    })
            except WebSocketDisconnect:
                raise # Re-raise to be handled by the outer try-except
            except Exception as exc:
                logger.error(f"Error processing websocket message: {exc}")
                # Continue the loop instead of breaking it
                continue
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket fatal error", exc_info=exc)

@app.get("/logs")
async def get_analysis_logs():
    """Retrieve historical analysis logs from the database."""
    return {"logs": get_logs()}

if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    
    # Determine the correct module name based on current directory
    # If run from root as 'python backend/main.py', it should be 'backend.main:app'
    # If run from backend as 'python main.py', it should be 'main:app'
    cwd = os.getcwd()
    if os.path.basename(cwd) == "backend":
        module = "main:app"
    else:
        module = "backend.main:app"
        
    print(f"Starting VEERA_SAFETY_AI Backend via {module}...")
    uvicorn.run(module, host="0.0.0.0", port=8000, reload=True)
