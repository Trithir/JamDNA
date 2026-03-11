from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Cluster, Track
from utils.fileops import move_track_to_cluster, rename_cluster_folder
import numpy as np
from . import query as query_routes

router = APIRouter()


def _duration_similarity_matrix(durations: np.ndarray) -> np.ndarray:
	if len(durations) == 0:
		return np.zeros((0, 0), dtype=np.float32)
	base = np.maximum(durations[:, None], durations[None, :])
	base[base == 0] = 1.0
	ratio = np.minimum(durations[:, None], durations[None, :]) / base
	return (0.75 + (0.25 * ratio)).astype(np.float32)


def _compute_similarity_matrix(mat: np.ndarray, durations: np.ndarray) -> np.ndarray:
	sim = (mat @ mat.T).astype(np.float32)
	duration_weight = _duration_similarity_matrix(durations)
	sim = sim * duration_weight
	np.fill_diagonal(sim, 1.0)
	return sim


def _knn_distance_scale(dist: np.ndarray, k: int = 6) -> float:
	if dist.shape[0] <= 2:
		return 0.18
	sorted_rows = np.sort(dist, axis=1)
	k = max(2, min(k, sorted_rows.shape[1] - 1))
	knn = sorted_rows[:, k]
	return float(np.median(knn))


def _auto_cluster(dist: np.ndarray):
	if dist.shape[0] == 0:
		return [], np.zeros((0,), dtype=np.int32)

	try:
		from sklearn.cluster import DBSCAN
	except Exception:
		labels = np.arange(dist.shape[0], dtype=np.int32)
		return [(None, 1) for _ in range(dist.shape[0])], labels

	eps = _knn_distance_scale(dist, k=6)
	eps = float(np.clip(eps * 1.18, 0.10, 0.40))
	min_samples = 2 if dist.shape[0] < 12 else 3

	labels = DBSCAN(metric="precomputed", eps=eps, min_samples=min_samples).fit_predict(dist)
	auto_info = []
	for idx, label in enumerate(labels):
		if label < 0:
			auto_info.append((None, 1))
		else:
			size = int(np.sum(labels == label))
			auto_info.append((int(label), size))
	return auto_info, labels


def _project_points(dist: np.ndarray):
	n = dist.shape[0]
	if n == 0:
		return np.zeros((0, 2), dtype=np.float32)
	if n == 1:
		return np.zeros((1, 2), dtype=np.float32)

	# Prefer UMAP if available, because it usually produces much better islands.
	try:
		import umap
		reducer = umap.UMAP(
			n_components=2,
			metric="precomputed",
			n_neighbors=max(4, min(15, n - 1)),
			min_dist=0.08,
			random_state=42,
		)
		return reducer.fit_transform(dist).astype(np.float32)
	except Exception:
		pass

	# Fall back to t-SNE on precomputed distances if UMAP is unavailable.
	try:
		from sklearn.manifold import TSNE
		perplexity = max(2, min(20, n - 1))
		coords = TSNE(
			n_components=2,
			metric="precomputed",
			init="random",
			learning_rate="auto",
			perplexity=perplexity,
			random_state=42,
		).fit_transform(dist)
		return coords.astype(np.float32)
	except Exception:
		pass

	# Final fallback: classical MDS-ish approximation via PCA on similarity.
	mat_centered = dist - dist.mean(axis=0)
	try:
		u, s, vh = np.linalg.svd(mat_centered, full_matrices=False)
		coords = u[:, :2] * s[:2]
	except Exception:
		coords = mat_centered[:, :2]

	if coords.shape[1] < 2:
		coords = np.pad(coords, ((0, 0), (0, 2 - coords.shape[1])))
	return coords.astype(np.float32)


def _nudge_clusters(coords: np.ndarray, auto_info, tighten: float, spread: float):
	if len(coords) == 0:
		return coords

	adjusted = coords.copy().astype(np.float32)
	overall_center = adjusted.mean(axis=0)
	cluster_ids = sorted({cid for cid, size in auto_info if cid is not None})

	for cluster_id in cluster_ids:
		members = [i for i, (cid, size) in enumerate(auto_info) if cid == cluster_id]
		if not members:
			continue

		centroid = adjusted[members].mean(axis=0)
		for idx in members:
			adjusted[idx] = centroid + ((adjusted[idx] - centroid) * (1.0 - tighten))

		shifted_centroid = overall_center + ((centroid - overall_center) * spread)
		shift = shifted_centroid - centroid
		for idx in members:
			adjusted[idx] = adjusted[idx] + shift

	return adjusted


def _normalize_2d(coords: np.ndarray):
	def norm(a):
		mn = a.min()
		mx = a.max()
		if mx - mn == 0:
			return np.zeros_like(a)
		return (2 * (a - mn) / (mx - mn)) - 1

	xs_n = norm(coords[:, 0])
	ys_n = norm(coords[:, 1])
	return xs_n, ys_n


@router.post("/create")
def create_cluster(name: str):
	session: Session = SessionLocal()
	try:
		cluster = Cluster(name=name)
		session.add(cluster)
		session.commit()
		return {"id": cluster.id, "name": cluster.name}
	finally:
		session.close()


@router.post("/assign")
def assign_track(track_id: int, cluster_id: int):
	session: Session = SessionLocal()
	try:
		track = session.get(Track, track_id)
		cluster = session.get(Cluster, cluster_id)

		if not track:
			raise HTTPException(status_code=404, detail="Track not found")
		if not cluster:
			raise HTTPException(status_code=404, detail="Cluster not found")

		new_path = move_track_to_cluster(track.path, cluster.name)
		track.cluster_id = cluster.id
		track.path = new_path
		session.commit()
		return {"track_id": track.id, "cluster_id": cluster.id, "new_path": new_path}
	finally:
		session.close()


@router.post("/rename")
def rename_cluster(cluster_id: int, new_name: str):
	session: Session = SessionLocal()
	try:
		cluster = session.get(Cluster, cluster_id)
		if not cluster:
			raise HTTPException(status_code=404, detail="Cluster not found")

		old_name = cluster.name
		cluster.name = new_name
		session.commit()
		rename_cluster_folder(old_name, new_name)
		return {"id": cluster.id, "old_name": old_name, "new_name": new_name}
	finally:
		session.close()


@router.get("/list")
def list_clusters():
	session: Session = SessionLocal()
	try:
		clusters = session.query(Cluster).all()
		data = []
		for c in clusters:
			members = [
				{"id": t.id, "path": t.path, "duration": t.duration, "cluster_id": t.cluster_id}
				for t in c.tracks
			]
			data.append({"id": c.id, "name": c.name, "members": members})

		unclustered_q = session.query(Track).filter(Track.cluster_id == None).all()
		unclustered = [
			{"id": t.id, "path": t.path, "duration": t.duration, "cluster_id": None}
			for t in unclustered_q
		]
		return {"clusters": data, "unclustered": unclustered}
	finally:
		session.close()


@router.get("/coords")
def cluster_coords(
	tighten: float = 0.16,
	spread: float = 1.28,
):
	session: Session = SessionLocal()
	try:
		tracks, mat, durations = query_routes.get_track_matrix(session)
		if len(tracks) == 0:
			return {"points": []}

		sim = _compute_similarity_matrix(mat, durations)
		dist = 1.0 - sim
		dist = np.clip(dist, 0.0, 2.0).astype(np.float32)
		auto_info, labels = _auto_cluster(dist)
		coords = _project_points(dist)
		coords = _nudge_clusters(coords, auto_info, tighten=tighten, spread=spread)
		xs_n, ys_n = _normalize_2d(coords)

		points = []
		for i, t in enumerate(tracks):
			auto_cluster_id, auto_cluster_size = auto_info[i]
			points.append({
				"id": int(t.id),
				"x": float(xs_n[i]),
				"y": float(ys_n[i]),
				"cluster_id": t.cluster_id,
				"auto_cluster_id": auto_cluster_id,
				"auto_cluster_size": auto_cluster_size,
				"path": t.path,
			})

		return {
			"points": points,
			"meta": {
				"tighten": tighten,
				"spread": spread,
				"projection": "umap_or_tsne_or_svd",
			}
		}
	finally:
		session.close()