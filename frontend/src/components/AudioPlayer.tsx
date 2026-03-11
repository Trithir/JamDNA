import { useMemo, useState } from "react"
import { getAudioStreamUrl } from "../api"

type AudioPlayerProps = {
	trackId?: number
	src?: string
	title?: string
	className?: string
	autoPlay?: boolean
	preload?: "none" | "metadata" | "auto"
	controlsList?: string
}

export default function AudioPlayer(props: AudioPlayerProps) {
	const {
		trackId,
		src,
		title,
		className,
		autoPlay = false,
		preload = "none",
		controlsList
	} = props

	const [hasError, setHasError] = useState(false)

	const resolvedSrc = useMemo(
		() => src ?? (trackId != null ? getAudioStreamUrl(trackId) : undefined),
		[src, trackId]
	)

	if (!resolvedSrc) {
		return <div className={className}>No audio source</div>
	}

	return (
		<div className={className}>
			{title ? <div style={{ marginBottom: "0.25rem" }}>{title}</div> : null}
			<audio
				key={resolvedSrc}
				controls
				src={resolvedSrc}
				autoPlay={autoPlay}
				preload={preload}
				controlsList={controlsList}
				style={{ width: "100%" }}
				onError={() => setHasError(true)}
				onPlay={() => setHasError(false)}
			/>
			{hasError ? (
				<div style={{ marginTop: "0.25rem", color: "#b91c1c", fontSize: "0.9rem" }}>
					Playback failed for this track.
				</div>
			) : null}
		</div>
	)
}
