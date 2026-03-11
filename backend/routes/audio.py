from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Track
import os
import subprocess

router = APIRouter()

BROWSER_SAFE_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac"}


def guess_media_type(path: str):
	ext = os.path.splitext(path)[1].lower()
	if ext == ".mp3":
		return "audio/mpeg"
	if ext == ".wav":
		return "audio/wav"
	if ext == ".ogg":
		return "audio/ogg"
	if ext in {".m4a", ".aac"}:
		return "audio/mp4"
	if ext == ".flac":
		return "audio/flac"
	return "application/octet-stream"


@router.get("/stream/{track_id}")
def stream_audio(track_id: int):
	session: Session = SessionLocal()
	try:
		track = session.get(Track, track_id)

		if not track:
			raise HTTPException(status_code=404, detail="Track not found")

		if not os.path.exists(track.path):
			raise HTTPException(status_code=404, detail="Audio file missing on disk")

		ext = os.path.splitext(track.path)[1].lower()

		if ext in BROWSER_SAFE_EXTENSIONS:
			return FileResponse(
				track.path,
				media_type=guess_media_type(track.path),
				filename=os.path.basename(track.path)
			)

		def iterfile():
			process = subprocess.Popen(
				[
					"ffmpeg",
					"-i", track.path,
					"-vn",
					"-acodec", "libmp3lame",
					"-f", "mp3",
					"-"
				],
				stdout=subprocess.PIPE,
				stderr=subprocess.DEVNULL
			)

			try:
				for chunk in iter(lambda: process.stdout.read(64 * 1024), b""):
					yield chunk
			finally:
				if process.stdout:
					process.stdout.close()
				process.terminate()

		return StreamingResponse(iterfile(), media_type="audio/mpeg")
	finally:
		session.close()