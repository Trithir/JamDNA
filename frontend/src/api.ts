const BASE_URL = "http://localhost:8000";

// Helper for GET requests
async function getJSON(path: string) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Helper for POST requests
async function postJSON(path: string, body: any = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

/* ------------------------
   Ingest
------------------------- */
export async function ingestTracks() {
  return postJSON("/ingest/");
}

/* ------------------------
   Query
------------------------- */
export async function getSimilar(trackId: number, k: number = 5) {
  return getJSON(`/query/similar/${trackId}?k=${k}`);
}

/* ------------------------
   Audio
------------------------- */
export function getAudioStreamUrl(trackId: number): string {
  return `${BASE_URL}/audio/stream/${trackId}`;
}

/* ------------------------
   Clusters
------------------------- */
export async function createCluster(name: string) {
  return postJSON(`/cluster/create?name=${encodeURIComponent(name)}`);
}

export async function assignTrack(trackId: number, clusterId: number) {
  return postJSON(`/cluster/assign?track_id=${trackId}&cluster_id=${clusterId}`);
}

export async function renameCluster(clusterId: number, newName: string) {
  return postJSON(
    `/cluster/rename?cluster_id=${clusterId}&new_name=${encodeURIComponent(newName)}`
  );
}

export async function listClusters() {
  return getJSON("/cluster/list");
}
