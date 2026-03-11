from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db import SessionLocal
from models import Track
from fingerprint import compute_fingerprint, file_sha1
from embedding import compute_embedding
import json
import os
import traceback

router = APIRouter()

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIO_FOLDER = os.path.join(REPO_ROOT, "data", "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)


@router.post("/")
def ingest_tracks():
	session: Session = SessionLocal()

	try:
		print(f"[ingest] repo_root={REPO_ROOT}")
		print(f"[ingest] audio_folder={AUDIO_FOLDER}")

		entries = sorted(os.listdir(AUDIO_FOLDER)) if os.path.isdir(AUDIO_FOLDER) else []
		files = [fname for fname in entries if os.path.isfile(os.path.join(AUDIO_FOLDER, fname))]
		print(f"[ingest] found {len(files)} file(s)")

		imported = []
		skipped = []
		errors = []

		for index, fname in enumerate(files, start=1):
			path = os.path.join(AUDIO_FOLDER, fname)
			print(f"[ingest] {index}/{len(files)} -> {fname}")

			existing_by_path = session.query(Track).filter_by(path=path).first()
			if existing_by_path:
				print(f"[ingest] skip existing_path id={existing_by_path.id}")
				skipped.append({
					"path": path,
					"reason": "existing_path",
					"existing_id": existing_by_path.id
				})
				continue

			sha1 = file_sha1(path)
			existing_by_sha1 = session.query(Track).filter_by(sha1=sha1).first()
			if existing_by_sha1:
				print(f"[ingest] skip duplicate_sha1 id={existing_by_sha1.id}")
				skipped.append({
					"path": path,
					"reason": "duplicate_sha1",
					"existing_id": existing_by_sha1.id
				})
				continue

			try:
				fp, duration = compute_fingerprint(path)
				embedding = compute_embedding(path)
			except Exception as exc:
				print(f"[ingest] ERROR processing {fname}: {exc}")
				traceback.print_exc()
				errors.append({
					"path": path,
					"reason": "processing_error",
					"error": str(exc)
				})
				continue

			track = Track(
				path=path,
				duration=duration,
				sha1=sha1,
				fingerprint=fp,
				embedding=json.dumps(embedding.tolist())
			)
			session.add(track)

			try:
				session.commit()
				print(f"[ingest] saved id={track.id}")
				imported.append({"id": track.id, "path": path, "duration": duration})
			except IntegrityError:
				session.rollback()
				existing = session.query(Track).filter((Track.sha1 == sha1) | (Track.path == path)).first()
				print(f"[ingest] skip already_present id={(existing.id if existing else None)}")
				skipped.append({
					"path": path,
					"reason": "already_present",
					"existing_id": (existing.id if existing else None)
				})

		print(f"[ingest] done imported={len(imported)} skipped={len(skipped)} errors={len(errors)}")
		return {"imported": imported, "skipped": skipped, "errors": errors}
	finally:
		session.close()
