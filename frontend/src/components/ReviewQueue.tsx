import { useEffect, useMemo, useRef, useState } from "react"
import {
	listClusters,
	ingestTracks,
	getSimilar,
	assignTrack,
	createCluster
} from "../api"
import AudioPlayer from "./AudioPlayer"

interface Track {
	id: number
	path: string
	duration: number
	cluster_id?: number
}

interface Cluster {
	id: number
	name: string
	members: Track[]
}

interface Neighbor {
	track_id: number
	distance: number
	path: string
	duration: number
	cluster_id: number | null
}

type ReviewQueueProps = {
	onDataChanged?: () => void
	selectedTrackId?: number | null
	onSelectTrack?: (trackId: number | null) => void
}

function ReviewQueue({ onDataChanged, selectedTrackId = null, onSelectTrack }: ReviewQueueProps) {
	const [clusters, setClusters] = useState<Cluster[]>([])
	const [queue, setQueue] = useState<Track[]>([])
	const [loading, setLoading] = useState(false)
	const [ingesting, setIngesting] = useState(false)
	const [expandedTrack, setExpandedTrack] = useState<number | null>(null)
	const [neighbors, setNeighbors] = useState<Record<number, Neighbor[]>>({})
	const cardRefs = useRef<Record<number, HTMLDivElement | null>>({})

	useEffect(() => {
		refreshClustersOnly()
	}, [])

	useEffect(() => {
		if (selectedTrackId == null) return
		const node = cardRefs.current[selectedTrackId]
		if (!node) return
		node.scrollIntoView({ behavior: "smooth", block: "center" })
	}, [selectedTrackId, queue])

	const selectedTrackSet = useMemo(() => {
		return new Set(selectedTrackId != null ? [selectedTrackId] : [])
	}, [selectedTrackId])

	async function refreshClustersOnly() {
		setLoading(true)
		try {
			const cl = await listClusters()
			setClusters(cl.clusters)

			let unclustered: Track[] = []
			if ((cl as any).unclustered) {
				unclustered = (cl as any).unclustered
			} else {
				const allTracks: Track[] = cl.clusters.flatMap((c: Cluster) => c.members)
				unclustered = allTracks.filter(t => !t.cluster_id)
			}

			setQueue(unclustered)
			onDataChanged?.()
		} finally {
			setLoading(false)
		}
	}

	async function ingestAndRefresh() {
		setIngesting(true)
		try {
			await ingestTracks()
			await refreshClustersOnly()
		} finally {
			setIngesting(false)
		}
	}

	async function handleAssign(track: Track, clusterId: number) {
		await assignTrack(track.id, clusterId)
		await refreshClustersOnly()
	}

	async function handleNewCluster(track: Track) {
		const name = prompt("Enter new cluster name:")
		if (!name) return
		const newCl = await createCluster(name)
		await assignTrack(track.id, newCl.id)
		await refreshClustersOnly()
	}

	async function handleSuggest(track: Track) {
		if (expandedTrack === track.id) {
			setExpandedTrack(null)
			return
		}

		setExpandedTrack(track.id)
		onSelectTrack?.(track.id)

		if (!neighbors[track.id]) {
			const sim = await getSimilar(track.id, 5)
			setNeighbors(prev => ({ ...prev, [track.id]: sim.neighbors }))
		}
	}

	return (
		<div>
			<h2>Review Queue</h2>

			<div style={{ marginBottom: "0.75rem", display: "flex", gap: "0.5rem", alignItems: "center" }}>
				<button onClick={() => ingestAndRefresh()} disabled={ingesting}>
					{ingesting ? "Ingesting…" : "Ingest New Files"}
				</button>

				<button onClick={() => refreshClustersOnly()} disabled={loading || ingesting}>
					{loading ? "Refreshing…" : "Refresh List"}
				</button>

				{(loading || ingesting) ? <span style={{ color: "#6b7280" }}>Working…</span> : null}
			</div>

			{queue.length === 0 && !(loading || ingesting) && <p>No unclustered tracks.</p>}

			{queue.map(track => {
				const isSelected = selectedTrackSet.has(track.id)

				return (
					<div
						key={track.id}
						ref={node => {
							cardRefs.current[track.id] = node
						}}
						className="track-card"
						style={{
							border: isSelected ? "2px solid #2563eb" : "1px solid #ccc",
							boxShadow: isSelected ? "0 0 0 3px rgba(37, 99, 235, 0.15)" : "none",
							background: isSelected ? "#eff6ff" : "#fff",
							padding: "1rem",
							marginBottom: "1rem"
						}}
					>
						<p>
							<strong>Track #{track.id}</strong>
							<span style={{ marginLeft: "0.5rem", color: "#6b7280" }}>
								({Math.round(track.duration)}s)
							</span>
							{isSelected ? (
								<span style={{ marginLeft: "0.5rem", color: "#1d4ed8", fontWeight: 600 }}>
									selected
								</span>
							) : null}
						</p>

						<p style={{ marginTop: "0.25rem", marginBottom: "0.5rem", color: "#374151", wordBreak: "break-all" }}>
							{track.path}
						</p>

						<div onClick={() => onSelectTrack?.(track.id)}>
							<AudioPlayer trackId={track.id} title={isSelected ? "Selected track" : undefined} preload="none" />
						</div>

						<div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
							<button onClick={() => handleSuggest(track)}>
								{expandedTrack === track.id ? "Hide Similar" : "Check Similar"}
							</button>

							<button onClick={() => handleNewCluster(track)}>
								New Cluster
							</button>

							<select onChange={e => handleAssign(track, Number(e.target.value))} defaultValue="">
								<option value="" disabled>Assign to cluster</option>
								{clusters.map(c => (
									<option key={c.id} value={c.id}>{c.name}</option>
								))}
							</select>
						</div>

						{expandedTrack === track.id && neighbors[track.id] && (
							<div style={{ marginTop: "1rem", paddingLeft: "0.5rem", borderLeft: "3px solid #eee" }}>
								<h4 style={{ marginTop: 0 }}>Similar Tracks</h4>
								{neighbors[track.id].length === 0 && <p>No matches found.</p>}

								{neighbors[track.id].map(n => (
									<div key={n.track_id} style={{ marginBottom: "0.75rem" }}>
										<p style={{ marginBottom: "0.25rem" }}>
											<strong>Track #{n.track_id}</strong>
											<span style={{ marginLeft: "0.5rem", color: "#6b7280" }}>
												(distance {n.distance.toFixed(3)})
												{n.cluster_id != null ? `, cluster ${n.cluster_id}` : ", unclustered"}
											</span>
										</p>

										<p style={{ marginTop: 0, marginBottom: "0.5rem", color: "#374151", wordBreak: "break-all" }}>
											{n.path}
										</p>

										<div onClick={() => onSelectTrack?.(n.track_id)}>
											<AudioPlayer trackId={n.track_id} preload="none" />
										</div>
									</div>
								))}
							</div>
						)}
					</div>
				)
			})}
		</div>
	)
}

export default ReviewQueue
