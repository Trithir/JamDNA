import { useState } from "react";
import ReviewQueue from "./components/ReviewQueue";
import ClusterList from "./components/ClusterList";

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

      {tab === "review" && <ReviewQueue />}
      {tab === "clusters" && <ClusterList />}
    </div>
  );
}

export default App;
