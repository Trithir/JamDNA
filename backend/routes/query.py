from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from db import get_session
from models import Track
from index import Index
import numpy as np

router = APIRouter()

# Simple in-memory index for now (rebuild on startup)
faiss_index = Index(dim=128)  # dim will be faked from fingerprint length
track_vectors = {}  # id -> vector

def fp_to_vec(fp: str, dim=128):
    """
    Convert Chromaprint string of ints into a fixed-length numpy vector.
    Very rough stub — later we’ll improve with smarter packing.
    """
    # Try the common comma-separated integers first
    parts = fp.split(",")
    arr = None
    try:
        if len(parts) > 1:
            ints = [int(x) for x in parts]
            arr = np.array(ints, dtype=np.float32)
    except Exception:
        arr = None

    # If that failed, try to interpret fingerprint as a URL-safe base64-like
    # chromaprint string: decode bytes and use their values.
    if arr is None:
        try:
            import base64

            # chromaprint uses a URL-safe base64 variant without padding in some
            # contexts. Add padding if needed and decode.
            s = fp.replace("-", "+").replace("_", "/")
            padding = len(s) % 4
            if padding:
                s += "=" * (4 - padding)
            decoded = base64.b64decode(s)
            arr = np.frombuffer(decoded, dtype=np.uint8).astype(np.float32)
        except Exception:
            arr = None

    # As a last resort, create a deterministic vector by hashing the string.
    if arr is None:
        import hashlib

        h = hashlib.md5(fp.encode("utf8")).digest()
        arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
    if len(arr) > dim:
        arr = arr[:dim]
    elif len(arr) < dim:
        arr = np.pad(arr, (0, dim - len(arr)))
    return arr.reshape(1, -1)

def rebuild_index(session: Session):
    global faiss_index, track_vectors
    faiss_index = Index(dim=128)
    track_vectors = {}
    tracks = session.query(Track).all()
    for t in tracks:
        vec = fp_to_vec(t.fingerprint)
        faiss_index.add(vec)
        track_vectors[t.id] = vec

@router.get("/similar/{track_id}")
def get_similar(track_id: int, k: int = 5):
    session: Session = next(get_session())
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # lazy rebuild if needed
    if not track_vectors:
        rebuild_index(session)

    vec = fp_to_vec(track.fingerprint)
    D, I = faiss_index.search(vec, k)
    results = []
    ids = list(track_vectors.keys())
    for dist, idx in zip(D[0], I[0]):
        if idx < len(ids):
            tid = ids[idx]
            results.append({"track_id": tid, "distance": float(dist)})

    return {"track": track_id, "neighbors": results}
