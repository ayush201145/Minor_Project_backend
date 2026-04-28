"""
CityPulse-X REST Routes — Upload, weather, video feed endpoints.
"""

import os
import time
import glob
import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

import config
import weather as weather_svc

router = APIRouter()


@router.post("/upload")
async def upload_endpoint(request: Request):
    """Handle video uploads for all 4 lanes and trigger simulation."""
    form = await request.form()
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    for old_file in glob.glob(os.path.join(upload_dir, "*.mp4")):
        try:
            os.remove(old_file)
        except Exception:
            pass
    for field_name, file_obj in form.items():
        if hasattr(file_obj, 'filename') and file_obj.filename:
            with open(os.path.join(upload_dir, f"{field_name}_{int(time.time())}.mp4"), "wb") as buffer:
                buffer.write(await file_obj.read())
    config.SIMULATION_TRIGGERED = True
    return {"status": "success", "message": "Engine started"}


@router.get("/weather")
async def get_weather():
    """Return current cached weather data."""
    w = await weather_svc.fetch_weather_from_api()
    return JSONResponse(weather_svc.get_weather_payload())


@router.post("/set_location")
async def set_location(request: Request):
    """Change the weather target city."""
    body = await request.json()
    city = body.get("city", "").strip()
    if not city:
        return JSONResponse({"error": "City name required"}, status_code=400)
    weather_svc.WEATHER_CITY = city
    weather_svc.WEATHER_CACHE["last_fetch"] = 0  # force refresh
    await weather_svc.fetch_weather_from_api()
    return JSONResponse({"status": "ok", "weather": weather_svc.get_weather_payload()})


@router.get("/video_feed/{lane_idx}")
async def video_feed(lane_idx: int):
    """Stream MJPEG frames for a specific lane."""
    async def frame_generator(idx):
        while True:
            frame_bytes = config.LATEST_FRAMES.get(idx)
            if frame_bytes:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.05)
    return StreamingResponse(frame_generator(lane_idx), media_type="multipart/x-mixed-replace; boundary=frame")
