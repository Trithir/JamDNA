import { useEffect, useMemo, useState } from "react"
import { getClusterCoords } from "../api"

type Point = {
	id: number
	x: number
	y: number
	cluster_id: number | null
	auto_cluster_id?: number | null
	auto_cluster_size?: number
	path: string
}

type ClusterChartProps = {
	refreshKey?: number
	selectedTrackId?: number | null
	onSelectTrack?: (trackId: number) => void
}

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
	"#14b8a6",
	"#84cc16",
	"#8b5cf6",
]

const POINT_SIZE = 6
const DENSITY_RADIUS = 70
const DENSITY_STRENGTH = 0.82
const SAME_CLUSTER_BIAS = 1.6
const SHOW_LABELS = false
const BASE_WIDTH = 760
const BASE_HEIGHT = 760

function clamp(value: number, min: number, max: number) {
	return Math.max(min, Math.min(max, value))
}

function hexToRgb(hex: string) {
	const clean = hex.replace("#", "")
	const normalized = clean.length === 3 ? clean.split("").map(ch => ch + ch).join("") : clean
	const num = parseInt(normalized, 16)
	return {
		r: (num >> 16) & 255,
		g: (num >> 8) & 255,
		b: num & 255,
	}
}

function mixColors(hexA: string, hexB: string, amount: number) {
	const a = hexToRgb(hexA)
	const b = hexToRgb(hexB)
	const t = clamp(amount, 0, 1)
	const r = Math.round(a.r + (b.r - a.r) * t)
	const g = Math.round(a.g + (b.g - a.g) * t)
	const b2 = Math.round(a.b + (b.b - a.b) * t)
	return `rgb(${r}, ${g}, ${b2})`
}

function distance(ax: number, ay: number, bx: number, by: number) {
	const dx = ax - bx
	const dy = ay - by
	return Math.sqrt((dx * dx) + (dy * dy))
}

export default function ClusterChart({ refreshKey = 0, selectedTrackId = null, onSelectTrack }: ClusterChartProps) {
	const [points, setPoints] = useState<Point[]>([])
	const [loading, setLoading] = useState(true)
	const [zoom, setZoom] = useState(1)

	useEffect(() => {
		setLoading(true)
		getClusterCoords()
			.then(data => setPoints(data.points || []))
			.catch(console.error)
			.finally(() => setLoading(false))
	}, [refreshKey])

	const size = { width: BASE_WIDTH, height: BASE_HEIGHT, padding: 28 }

	const plottedPoints = useMemo(() => {
		return points.map(p => {
			const cx = ((p.x + 1) / 2) * (size.width - size.padding * 2) + size.padding
			const cy = ((1 - (p.y + 1) / 2)) * (size.height - size.padding * 2) + size.padding
			return { ...p, cx, cy }
		})
	}, [points])

	const clusterMap = useMemo(() => {
		const manualIds = Array.from(new Set(plottedPoints.map(p => p.cluster_id).filter(c => c != null) as number[]))
		const autoIds = Array.from(new Set(plottedPoints.map(p => p.auto_cluster_id).filter(c => c != null) as number[]))
		const map = new Map<number, string>()

		manualIds.forEach((id, i) => map.set(id, COLORS[i % COLORS.length]))
		autoIds.forEach((id, i) => {
			if (!map.has(id)) {
				map.set(id, COLORS[(manualIds.length + i) % COLORS.length])
			}
		})
		return map
	}, [plottedPoints])

	const coloredPoints = useMemo(() => {
		if (plottedPoints.length === 0) {
			return []
		}

		const rawScores = plottedPoints.map(p => {
			let score = 0
			for (const other of plottedPoints) {
				if (other.id === p.id) continue
				const dist = distance(p.cx, p.cy, other.cx, other.cy)
				if (dist > DENSITY_RADIUS) continue

				const closeness = 1 - (dist / DENSITY_RADIUS)
				const sameManual = p.cluster_id != null && other.cluster_id === p.cluster_id
				const sameAuto = p.auto_cluster_id != null && other.auto_cluster_id === p.auto_cluster_id
				const weight = sameManual || sameAuto ? SAME_CLUSTER_BIAS : 0.35
				score += closeness * weight
			}
			return score
		})

		const maxScore = Math.max(...rawScores, 0.0001)

		return plottedPoints.map((p, index) => {
			const normalized = clamp(rawScores[index] / maxScore, 0, 1)
			const boosted = Math.pow(normalized, DENSITY_STRENGTH)
			const colorKey = p.cluster_id != null ? p.cluster_id : p.auto_cluster_id
			const baseColor = colorKey != null ? (clusterMap.get(colorKey) || "#3b82f6") : "#94a3b8"
			const fill = mixColors("#f8fafc", baseColor, 0.26 + (boosted * 0.74))
			const stroke = mixColors("#ffffff", baseColor, 0.46 + (boosted * 0.54))
			return {
				...p,
				densityScore: rawScores[index],
				densityNormalized: normalized,
				fill,
				stroke,
			}
		})
	}, [plottedPoints, clusterMap])

	return (
		<div style={{ padding: "0.75rem", maxHeight: "calc(100vh - 150px)", overflowY: "auto", boxSizing: "border-box" }}>
			<div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", marginBottom: "0.5rem" }}>
				<h2 style={{ margin: 0 }}>Cluster Map</h2>
				<div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
					<button onClick={() => setZoom(z => Math.max(0.6, Number((z - 0.2).toFixed(2))))}>-</button>
					<button onClick={() => setZoom(1)}>Reset</button>
					<button onClick={() => setZoom(z => Math.min(2.4, Number((z + 0.2).toFixed(2))))}>+</button>
					<span style={{ color: "#4b5563", minWidth: "3.5rem", textAlign: "right" }}>{Math.round(zoom * 100)}%</span>
				</div>
			</div>

			{loading && <p>Loading...</p>}
			{!loading && points.length === 0 && <p>No tracks to display.</p>}

			{!loading && points.length > 0 && (
				<div style={{ overflow: "auto", border: "1px solid #eee", background: "#fafafa" }}>
					<svg width={size.width * zoom} height={size.height * zoom} style={{ display: "block", background: "#fafafa" }}>
						<g transform={`scale(${zoom})`}>
							<line x1={size.width / 2} y1={0} x2={size.width / 2} y2={size.height} stroke="#eee" />
							<line x1={0} y1={size.height / 2} x2={size.width} y2={size.height / 2} stroke="#eee" />

							{coloredPoints.map(p => {
								const isSelected = p.id === selectedTrackId
								return (
									<g key={p.id}>
										<circle
											cx={p.cx}
											cy={p.cy}
											r={isSelected ? POINT_SIZE + 2 : POINT_SIZE}
											fill={p.fill}
											stroke={isSelected ? "#111827" : p.stroke}
											strokeWidth={isSelected ? 2.5 : 1.2}
											style={{ cursor: "pointer" }}
											onClick={() => onSelectTrack?.(p.id)}
										>
											<title>{`#${p.id} ${p.path} (assigned: ${p.cluster_id}, auto: ${p.auto_cluster_id}, auto_size: ${p.auto_cluster_size ?? 1}, density: ${p.densityNormalized.toFixed(2)})`}</title>
										</circle>

										{SHOW_LABELS && (
											<text x={p.cx + POINT_SIZE + 3} y={p.cy + 4} fontSize="10" fill={isSelected ? "#111827" : "#1f2937"}>
												#{p.id}
											</text>
										)}
									</g>
								)
							})}
						</g>
					</svg>
				</div>
			)}
		</div>
	)
}