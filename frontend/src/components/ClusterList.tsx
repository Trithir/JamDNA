// frontend/src/components/ClusterList.tsx
import { useEffect, useState } from "react";
import { listClusters, getAudioStreamUrl } from "../api";

interface Track {
  id: number;
  path: string;
  duration: number;
}

interface Cluster {
  id: number;
  name: string;
  members: Track[];
}

function ClusterList() {
  const [clusters, setClusters] = useState<Cluster[]>([]);

  useEffect(() => {
    listClusters().then(data => setClusters(data.clusters));
  }, []);

  return (
    <div>
      <h2>All Clusters</h2>
      {clusters.length === 0 && <p>No clusters yet.</p>}

      {clusters.map(c => (
        <div key={c.id} style={{ marginBottom: "1rem", border: "1px solid #ccc", padding: "1rem" }}>
          <h3>{c.name} (id: {c.id})</h3>
          {c.members.length === 0 && <p>No tracks assigned.</p>}
          {c.members.map(m => (
            <div key={m.id} style={{ marginLeft: "1rem" }}>
              <p>{m.path} ({Math.round(m.duration)}s)</p>
              <audio controls src={getAudioStreamUrl(m.id)} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default ClusterList;
