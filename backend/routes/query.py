from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Track
from index import Index
from embedding import EMBEDDING_DIM
import json
import numpy as np

router = APIRouter()

VECTOR_DIM = EMBEDDING_DIM
faiss_index = Index(dim=VECTOR_DIM)
track_vectors = {}
track_ids = []
track_durations = {}


def _fallback_fp_to_vec(fp: str, dim: int = VECTOR_DIM):
	parts = fp.split(",")
	try:
		ints = [int(x) for x in parts if x.strip() != ""]
		arr = np.array(ints, dtype=np.float32)
	except Exception:
		arr = np.frombuffer(fp.encode("utf8"), dtype=np.uint8).astype(np.float32)

	if len(arr) < dim:
		arr = np.pad(arr, (0, dim - len(arr)))
	elif len(arr) > dim:
		bins = np.linspace(0, len(arr), dim + 1, dtype=np.int32)
		arr = np.array([
			float(arr[bins[i]:max(bins[i] + 1, bins[i + 1])].mean())
			for i in range(dim)
		], dtype=np.float32)

	arr = arr.astype(np.float32)
	norm = float(np.linalg.norm(arr))
	if norm > 1e-6:
		arr = arr / norm
	return arr


def _duration_weight(a: float | None, b: float | None) -> float:
	if not a or not b or a <= 0 or b <= 0:
		return 1.0
	ratio = min(a, b) / max(a, b)
	# Mild penalty. Same songs in jams may differ, but wildly different durations should lose points.
	return float(0.75 + (0.25 * ratio))


def track_to_vec(track: Track, dim: int = VECTOR_DIM) -> np.ndarray:
	if track.embedding:
		try:
			arr = np.array(json.loads(track.embedding), dtype=np.float32)
			if arr.shape[0] == dim:
				return arr.reshape(1, -1)
		except Exception:
			pass

	return _fallback_fp_to_vec(track.fingerprint, dim=dim).reshape(1, -1)


def rebuild_index(session: Session):
	global faiss_index, track_vectors, track_ids, track_durations

	faiss_index = Index(dim=VECTOR_DIM)
	track_vectors = {}
	track_ids = []
	track_durations = {}

	tracks = session.query(Track).all()
	for t in tracks:
		vec = track_to_vec(t)
		faiss_index.add(vec)
		track_vectors[t.id] = vec
		track_ids.append(t.id)
		track_durations[t.id] = float(t.duration or 0.0)


def get_track_matrix(session: Session):
	tracks = session.query(Track).all()
	if not tracks:
		return [], np.zeros((0, VECTOR_DIM), dtype=np.float32), np.zeros((0,), dtype=np.float32)

	mat = np.vstack([track_to_vec(t).reshape(-1) for t in tracks]).astype(np.float32)
	durations = np.array([float(t.duration or 0.0) for t in tracks], dtype=np.float32)
	return tracks, mat, durations


@router.get("/similar/{track_id}")
def get_similar(track_id: int, k: int = 5):
	session: Session = SessionLocal()

	try:
		track = session.get(Track, track_id)
		if not track:
			raise HTTPException(status_code=404, detail="Track not found")

		if not track_vectors:
			rebuild_index(session)

		vec = track_to_vec(track)
		D, I = faiss_index.search(vec, max((k * 3) + 1, 12))

		scored = []
		for score, idx in zip(D[0], I[0]):
			if idx < 0 or idx >= len(track_ids):
				continue

			tid = track_ids[idx]
			if tid == track_id:
				continue

			t = session.get(Track, tid)
			if not t:
				continue

			weighted_score = float(score) * _duration_weight(track.duration, t.duration)
			scored.append((weighted_score, t))

		scored.sort(key=lambda x: x[0], reverse=True)
		results = []
		for score, t in scored[:k]:
			results.append({
				"track_id": t.id,
				"distance": float(1.0 - score),
				"score": float(score),
				"path": t.path,
				"duration": t.duration,
				"cluster_id": t.cluster_id
			})

		return {"track": track_id, "neighbors": results}
	finally:
		session.close()