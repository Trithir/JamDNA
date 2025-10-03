from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from db import get_session
from models import Cluster, Track
from utils.fileops import move_track_to_cluster, rename_cluster_folder

router = APIRouter()

@router.post("/create")
def create_cluster(name: str):
    session: Session = next(get_session())
    cluster = Cluster(name=name)
    session.add(cluster)
    session.commit()
    return {"id": cluster.id, "name": cluster.name}

@router.post("/assign")
def assign_track(track_id: int, cluster_id: int):
    session: Session = next(get_session())
    track = session.get(Track, track_id)
    cluster = session.get(Cluster, cluster_id)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Move file to cluster folder
    new_path = move_track_to_cluster(track.path, cluster.name)

    # Update DB
    track.cluster_id = cluster.id
    track.path = new_path
    session.commit()

    return {"track_id": track.id, "cluster_id": cluster.id, "new_path": new_path}

@router.post("/rename")
def rename_cluster(cluster_id: int, new_name: str):
    session: Session = next(get_session())
    cluster = session.get(Cluster, cluster_id)

    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    old_name = cluster.name
    cluster.name = new_name
    session.commit()

    # Rename folder on disk
    rename_cluster_folder(old_name, new_name)

    return {"id": cluster.id, "old_name": old_name, "new_name": new_name}

@router.get("/list")
def list_clusters():
    session: Session = next(get_session())
    clusters = session.query(Cluster).all()
    data = []
    for c in clusters:
        members = [
            {"id": t.id, "path": t.path, "duration": t.duration}
            for t in c.tracks
        ]
        data.append({
            "id": c.id,
            "name": c.name,
            "members": members
        })
    # Also include tracks that are not assigned to any cluster so the
    # frontend can show a review queue without reconstructing from clusters.
    unclustered_q = session.query(Track).filter(Track.cluster_id == None).all()
    unclustered = [
        {"id": t.id, "path": t.path, "duration": t.duration, "cluster_id": None}
        for t in unclustered_q
    ]
    return {"clusters": data, "unclustered": unclustered}
