from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db import get_session
from models import Track
import subprocess

router = APIRouter()

@router.get("/stream/{track_id}")
def stream_audio(track_id: int):
    """
    Stream audio as mp3 for playback in frontend <audio> tags.
    """
    session: Session = next(get_session())
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    def iterfile():
        # transcode to mp3 for browser compatibility
        process = subprocess.Popen(
            ["ffmpeg", "-i", track.path, "-f", "mp3", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        for chunk in iter(lambda: process.stdout.read(4096), b""):
            yield chunk

    return StreamingResponse(iterfile(), media_type="audio/mpeg")
