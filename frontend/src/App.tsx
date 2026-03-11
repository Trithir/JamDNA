import { useState } from "react"
import ReviewQueue from "./components/ReviewQueue"
import ClusterList from "./components/ClusterList"
import ClusterChart from "./components/ClusterChart"

function App() {
	const [tab, setTab] = useState<"review" | "clusters">("review")
	const [chartRefreshKey, setChartRefreshKey] = useState(0)
	const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null)

	function refreshClusterMap() {
		setChartRefreshKey(prev => prev + 1)
	}

	return (
		<div style={{ fontFamily: "sans-serif", margin: "1rem 1.5rem" }}>
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
				<div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
					<div style={{ width: "42%", maxHeight: "calc(100vh - 150px)", overflowY: "auto", paddingRight: "0.5rem" }}>
						<ReviewQueue
							onDataChanged={refreshClusterMap}
							selectedTrackId={selectedTrackId}
							onSelectTrack={setSelectedTrackId}
						/>
					</div>
					<div style={{ width: "58%", borderLeft: "1px solid #ddd", paddingLeft: "0.75rem", position: "sticky", top: "0.5rem", alignSelf: "flex-start" }}>
						<ClusterChart
							refreshKey={chartRefreshKey}
							selectedTrackId={selectedTrackId}
							onSelectTrack={setSelectedTrackId}
						/>
					</div>
				</div>
			)}

			{tab === "clusters" && <ClusterList />}
		</div>
	)
}

export default App