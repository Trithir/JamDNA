import numpy as np

EMBEDDING_DIM = 256
TARGET_SR = 22050
SAMPLE_CLIP_SECONDS = 24.0
NUM_CLIPS = 5
MIN_ACTIVE_SECONDS = 6.0


def _normalize(arr: np.ndarray) -> np.ndarray:
	arr = arr.astype(np.float32)
	arr = arr - float(arr.mean())
	std = float(arr.std())
	if std > 1e-6:
		arr = arr / std
	norm = float(np.linalg.norm(arr))
	if norm > 1e-6:
		arr = arr / norm
	return arr


def _resample_feature_vector(arr: np.ndarray, dim: int) -> np.ndarray:
	if len(arr) == dim:
		return arr.astype(np.float32)
	if len(arr) < dim:
		return np.pad(arr.astype(np.float32), (0, dim - len(arr)))

	bins = np.linspace(0, len(arr), dim + 1, dtype=np.int32)
	pieces = []
	for i in range(dim):
		start = bins[i]
		end = max(start + 1, bins[i + 1])
		pieces.append(float(arr[start:end].mean()))
	return np.array(pieces, dtype=np.float32)


def _even_positions(total_len: int, clip_len: int, count: int):
	if total_len <= clip_len:
		return [0]
	max_start = total_len - clip_len
	if count <= 1:
		return [max_start // 2]
	return [int(round(x)) for x in np.linspace(0, max_start, count)]


def _clip_activity_score(librosa, clip: np.ndarray, sr: int) -> float:
	rms = librosa.feature.rms(y=clip).mean()
	onset = librosa.onset.onset_strength(y=clip, sr=sr).mean()
	return float(rms * 0.6 + onset * 0.4)


def _feature_summary(np_mod, feat: np.ndarray):
	return [
		np_mod.mean(feat, axis=1),
		np_mod.std(feat, axis=1),
		np_mod.median(feat, axis=1),
	]


def compute_embedding(path: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
	"""
	Compute a richer music-oriented embedding using multiple clips across the song.
	This is still lightweight enough for a local app, but much more song-aware than
	plain Chromaprint-derived vectors.
	"""
	try:
		import librosa
	except Exception as exc:
		raise RuntimeError(
			"librosa is required for embeddings. Install with: pip install librosa soundfile"
		) from exc

	y, sr = librosa.load(path, sr=TARGET_SR, mono=True)
	if y is None or len(y) == 0:
		return np.zeros(dim, dtype=np.float32)

	# Gentle trim first so we do not waste clips on dead air.
	y, _ = librosa.effects.trim(y, top_db=28)
	if len(y) == 0:
		return np.zeros(dim, dtype=np.float32)

	clip_len = int(SAMPLE_CLIP_SECONDS * sr)
	positions = _even_positions(len(y), clip_len, NUM_CLIPS)
	candidates = []
	for pos in positions:
		clip = y[pos:pos + clip_len]
		if len(clip) == 0:
			continue
		trimmed, _ = librosa.effects.trim(clip, top_db=25)
		if len(trimmed) < int(MIN_ACTIVE_SECONDS * sr):
			trimmed = clip
		if len(trimmed) == 0:
			continue
		score = _clip_activity_score(librosa, trimmed, sr)
		candidates.append((score, trimmed))

	if not candidates:
		return np.zeros(dim, dtype=np.float32)

	# Keep the most active clips, but preserve some spread by not collapsing to one region.
	candidates = sorted(candidates, key=lambda x: x[0], reverse=True)[:NUM_CLIPS]
	clip_vectors = []
	for _, clip in candidates:
		if len(clip) == 0:
			continue

		harmonic, percussive = librosa.effects.hpss(clip)
		mfcc = librosa.feature.mfcc(y=clip, sr=sr, n_mfcc=24)
		mfcc_delta = librosa.feature.delta(mfcc)
		chroma = librosa.feature.chroma_cqt(y=harmonic, sr=sr)
		contrast = librosa.feature.spectral_contrast(y=clip, sr=sr)
		tonnetz = librosa.feature.tonnetz(y=harmonic, sr=sr)
		tempogram = librosa.feature.tempogram(y=percussive, sr=sr)
		zcr = librosa.feature.zero_crossing_rate(clip)
		rms = librosa.feature.rms(y=clip)
		centroid = librosa.feature.spectral_centroid(y=clip, sr=sr)
		bandwidth = librosa.feature.spectral_bandwidth(y=clip, sr=sr)
		rolloff = librosa.feature.spectral_rolloff(y=clip, sr=sr)
		flatness = librosa.feature.spectral_flatness(y=clip)
		tempo, _ = librosa.beat.beat_track(y=clip, sr=sr)

		parts = []
		for feat in [mfcc, mfcc_delta, chroma, contrast, tonnetz, tempogram, zcr, rms, centroid, bandwidth, rolloff, flatness]:
			parts.extend(_feature_summary(np, feat))

		parts.append(np.array([float(tempo)], dtype=np.float32))
		vec = np.concatenate(parts).astype(np.float32)
		clip_vectors.append(vec)

	if not clip_vectors:
		return np.zeros(dim, dtype=np.float32)

	emb = np.mean(np.vstack(clip_vectors), axis=0)
	emb = _resample_feature_vector(emb, dim)
	emb = _normalize(emb)
	return emb.astype(np.float32)