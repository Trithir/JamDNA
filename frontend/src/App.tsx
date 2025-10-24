import { useState } from "react";
import ReviewQueue from "./components/ReviewQueue";
import ClusterList from "./components/ClusterList";
import ClusterChart from "./components/ClusterChart";

function App() {
  const [tab, setTab] = useState<"review" | "clusters">("review");

  return (
    <div style={{ fontFamily: "sans-serif", margin: "2rem" }}>
      <h1>JamDNA</h1>
      <div style={{ marginBottom: "1rem" }}>
        <button
          onClick={() => setTab("review")}
          style={{
            marginRight: "0.5rem",
            background: tab === "review" ? "#ccc" : "#eee",
            padding: "0.5rem 1rem",
            border: "1px solid #aaa",
          }}
        >
          Review Queue
        </button>
        <button
          onClick={() => setTab("clusters")}
          style={{
            background: tab === "clusters" ? "#ccc" : "#eee",
            padding: "0.5rem 1rem",
            border: "1px solid #aaa",
          }}
        >
          Cluster List
        </button>
      </div>

      {tab === "review" && (
        <div style={{ display: "flex", gap: "1rem", height: "70vh" }}>
          <div style={{ width: "50%", overflowY: "auto", paddingRight: "0.5rem" }}>
            <ReviewQueue />
          </div>
          <div style={{ width: "50%", borderLeft: "1px solid #ddd", paddingLeft: "0.5rem", overflow: "hidden" }}>
            {/* Chart stays visible while the left pane scrolls */}
            <ClusterChart />
          </div>
        </div>
      )}

      {tab === "clusters" && <ClusterList />}
    </div>
  );
}

export default App;
