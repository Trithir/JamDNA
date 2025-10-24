import { useEffect, useState, useMemo } from "react";
import { getClusterCoords } from "../api";

type Point = {
  id: number;
  x: number; // -1..1
  y: number; // -1..1
  cluster_id: number | null;
  path: string;
};

const COLORS = [
  "#ef4444",
  "#f97316",
  "#f59e0b",
  "#10b981",
  "#06b6d4",
  "#3b82f6",
  "#6366f1",
  "#a78bfa",
  "#ec4899",
  "#64748b",
];

export default function ClusterChart() {
  const [points, setPoints] = useState<Point[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getClusterCoords()
      .then((data) => setPoints(data.points || []))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  // Map cluster ids to palette indices
  const clusterMap = useMemo(() => {
    const ids = Array.from(new Set(points.map((p) => p.cluster_id).filter((c) => c != null) as number[]));
    const map = new Map<number, string>();
    ids.forEach((id, i) => map.set(id, COLORS[i % COLORS.length]));
    return map;
  }, [points]);

  const size = { width: 500, height: 500, padding: 24 };

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Cluster Map</h2>
      {loading && <p>Loading...</p>}
      {!loading && points.length === 0 && <p>No tracks to display.</p>}

      {!loading && points.length > 0 && (
        <svg width={size.width} height={size.height} style={{ border: "1px solid #eee", background: "#fafafa" }}>
          {/* axes */}
          <line x1={size.width/2} y1={0} x2={size.width/2} y2={size.height} stroke="#eee" />
          <line x1={0} y1={size.height/2} x2={size.width} y2={size.height/2} stroke="#eee" />

          {points.map((p) => {
            const cx = ((p.x + 1) / 2) * (size.width - size.padding * 2) + size.padding;
            const cy = ((1 - (p.y + 1) / 2)) * (size.height - size.padding * 2) + size.padding; // invert y for svg
            const color = p.cluster_id == null ? "#9ca3af" : clusterMap.get(p.cluster_id!) || "#111827";
            return (
              <circle key={p.id} cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={1}>
                <title>{`#${p.id} ${p.path} (cluster: ${p.cluster_id})`}</title>
              </circle>
            );
          })}
        </svg>
      )}
    </div>
  );
}
