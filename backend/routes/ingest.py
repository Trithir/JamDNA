from fastapi import APIRouter
from sqlalchemy.orm import Session
from db import get_session
from models import Track
from fingerprint import compute_fingerprint, file_sha1
import os

router = APIRouter()

AUDIO_FOLDER = "data/audio"

@router.post("/")
def ingest_tracks():
    """
    Scan AUDIO_FOLDER for new files, compute fingerprint, and save to DB.
    """
    session: Session = next(get_session())
    imported = []

    for fname in os.listdir(AUDIO_FOLDER):
        path = os.path.join(AUDIO_FOLDER, fname)
        if not os.path.isfile(path):
            continue

        sha1 = file_sha1(path)
        existing = session.query(Track).filter_by(sha1=sha1).first()
        if existing:
            continue  # already ingested

        fp, duration = compute_fingerprint(path)
        track = Track(
            path=path,
            duration=duration,
            sha1=sha1,
            fingerprint=fp
        )
        session.add(track)
        session.commit()
        imported.append({"id": track.id, "path": path, "duration": duration})

    return {"imported": imported}
