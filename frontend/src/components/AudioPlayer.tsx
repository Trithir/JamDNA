import { useMemo } from "react";
import { getAudioStreamUrl } from "../api";

type AudioPlayerProps = {
	trackId?: number;
	src?: string;
	title?: string;
	className?: string;
	autoPlay?: boolean;
	preload?: "none" | "metadata" | "auto";
	controlsList?: string; // e.g. "nodownload noplaybackrate"
};

export default function AudioPlayer(props: AudioPlayerProps) {
	const {
		trackId,
		src,
		title,
		className,
		autoPlay = false,
		preload = "metadata",
		controlsList
	} = props;

	const resolvedSrc = useMemo(
		() => src ?? (trackId != null ? getAudioStreamUrl(trackId) : undefined),
		[src, trackId]
	);

	if (!resolvedSrc) {
		return <div className={className}>No audio source</div>;
	}

	return (
		<div className={className}>
			{title ? <div style={{ marginBottom: "0.25rem" }}>{title}</div> : null}
			<audio
				controls
				src={resolvedSrc}
				autoPlay={autoPlay}
				preload={preload}
				controlsList={controlsList}
				style={{ width: "100%" }}
			/>
		</div>
	);
}
