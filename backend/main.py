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

@app.on_event("startup")
async def startup_event():
    """Start pre-warming in the background so we don't block the health check."""
    import asyncio
    asyncio.create_task(pre_warm_model())

async def pre_warm_model():
    """Pre-warm the AI model to ensure fast first-request response."""
    logger.info("Pre-warming VEERA_AI Neural Core in background...")
    try:
        # Run a dummy inference with a blank frame
        blank_frame = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAREDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZnaEfX19fM3FyE6qp6kx8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q=="
        inference_engine.analyze_frame(blank_frame)
        logger.info("Neural Core Warm-up Complete.")
    except Exception as e:
        logger.warning(f"Warm-up failed (non-critical): {e}")

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "VEERA_SAFETY_AI Neural Core",
        "version": "v2.4.1",
        "endpoints": ["/health", "/upload", "/logs", "/stream"]
    }

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
    module = "main:app" if os.path.basename(cwd) == "backend" else "backend.main:app"
    
    # Render provides the port via environment variable
    port = int(os.environ.get("PORT", 8000))
    
    # Disable reload in production to avoid port issues
    is_dev = os.environ.get("RENDER") is None
    
    print(f"Starting VEERA_SAFETY_AI Backend on port {port} (reload={is_dev})...")
    uvicorn.run(module, host="0.0.0.0", port=port, reload=is_dev)
