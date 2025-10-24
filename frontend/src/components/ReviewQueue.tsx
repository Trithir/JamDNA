import { useEffect, useState } from "react";
import {
  listClusters,
  ingestTracks,
  getSimilar,
  assignTrack,
  createCluster,
  getAudioStreamUrl,
} from "../api";
import AudioPlayer from "./AudioPlayer";

interface Track {
  id: number;
  path: string;
  duration: number;
  cluster_id?: number;
}

interface Cluster {
  id: number;
  name: string;
  members: Track[];
}

interface Neighbor {
  track_id: number;
  distance: number;
}

function ReviewQueue() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [queue, setQueue] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);

  // which track's suggestions are expanded
  const [expandedTrack, setExpandedTrack] = useState<number | null>(null);
  const [neighbors, setNeighbors] = useState<Record<number, Neighbor[]>>({});

  useEffect(() => {
    refreshData();
  }, []);

  async function refreshData() {
    setLoading(true);

    await ingestTracks();
    const cl = await listClusters();
    setClusters(cl.clusters);

    // Prefer backend-provided `unclustered` list when available (newer backend).
    // Fallback to deriving it from clusters for older backends.
    let unclustered: Track[] = [];
    if ((cl as any).unclustered) {
      unclustered = (cl as any).unclustered;
    } else {
      const allTracks: Track[] = cl.clusters.flatMap((c: Cluster) => c.members);
      unclustered = allTracks.filter(t => !t.cluster_id);
    }
    setQueue(unclustered);

    setLoading(false);
  }

  async function handleAssign(track: Track, clusterId: number) {
    await assignTrack(track.id, clusterId);
    await refreshData();
  }

  async function handleNewCluster(track: Track) {
    const name = prompt("Enter new cluster name:");
    if (!name) return;
    const newCl = await createCluster(name);
    await assignTrack(track.id, newCl.id);
    await refreshData();
  }

  async function handleSuggest(track: Track) {
    // toggle off if already open
    if (expandedTrack === track.id) {
      setExpandedTrack(null);
      return;
    }
    setExpandedTrack(track.id);

    // fetch neighbors if not already cached
    if (!neighbors[track.id]) {
      const sim = await getSimilar(track.id, 5);
      setNeighbors(prev => ({ ...prev, [track.id]: sim.neighbors }));
    }
  }

  return (
    <div>
      <h2>Review Queue</h2>
      {loading && <p>Loading...</p>}

      {queue.length === 0 && !loading && (
        <p>No unclustered tracks. 🎶</p>
      )}

      {queue.map(track => (
        <div
          key={track.id}
          className="track-card"
          style={{
            border: "1px solid #ccc",
            padding: "1rem",
            marginBottom: "1rem"
          }}
        >
          <p>
            <strong>{track.path}</strong> ({Math.round(track.duration)}s)
          </p>
          <audio controls src={getAudioStreamUrl(track.id)} />

          <div style={{ marginTop: "0.5rem" }}>
            <button onClick={() => handleSuggest(track)}>
              {expandedTrack === track.id ? "Hide Similar" : "Check Similar"}
            </button>
            <button onClick={() => handleNewCluster(track)}>New Cluster</button>

            <select
              onChange={(e) => handleAssign(track, Number(e.target.value))}
              defaultValue=""
            >
              <option value="" disabled>
                Assign to cluster…
              </option>
              {clusters.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Show neighbors inline */}
          {expandedTrack === track.id && neighbors[track.id] && (
            <div style={{ marginTop: "1rem", paddingLeft: "1rem" }}>
              <h4>Similar Tracks:</h4>
              {neighbors[track.id].length === 0 && <p>No matches found.</p>}
              {neighbors[track.id].map(n => (
                <div key={n.track_id} style={{ marginBottom: "0.5rem" }}>
                  <p>
                    Track #{n.track_id} (distance: {n.distance.toFixed(3)})
                  </p>
                  <AudioPlayer trackId={n.track_id} />
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default ReviewQueue;
