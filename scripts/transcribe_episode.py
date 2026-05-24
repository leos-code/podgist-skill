#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import PodgistError, format_timestamp, load_episode_ref, print_json, require_file, write_json, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe a normalized episode audio file.")
    parser.add_argument("--artifact-dir", required=True, help="Episode artifact directory")
    parser.add_argument("--model", default="small", help="faster-whisper model name")
    parser.add_argument("--device", default="auto", help="Whisper inference device")
    parser.add_argument("--compute-type", default="auto", help="Whisper compute type")
    parser.add_argument("--language", help="Optional language hint")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--srt", action="store_true", help="Also write transcript.srt")
    return parser.parse_args()


def build_srt(segments: list[dict[str, float | str]]) -> str:
    def render_srt_timestamp(seconds: float) -> str:
        total_ms = max(0, int(seconds * 1000))
        hours, remainder = divmod(total_ms, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.append(str(index))
        lines.append(
            f"{render_srt_timestamp(float(segment['start']))} --> "
            f"{render_srt_timestamp(float(segment['end']))}"
        )
        lines.append(str(segment["text"]).strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    artifact_dir = Path(args.artifact_dir).resolve()
    episode_ref = load_episode_ref(artifact_dir)
    audio_path = require_file(artifact_dir / "audio.wav", "normalized audio")

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise PodgistError(
            "Missing dependency `faster-whisper`. Install with `pip install -r requirements.txt`."
        ) from exc

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=args.language,
        beam_size=args.beam_size,
        vad_filter=True,
    )

    segments: list[dict[str, float | str]] = []
    transcript_parts: list[str] = []
    for segment in segments_iter:
        text = segment.text.strip()
        if not text:
            continue
        payload = {
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "text": text,
        }
        segments.append(payload)
        transcript_parts.append(text)

    transcript_text = "\n".join(transcript_parts).strip() + ("\n" if transcript_parts else "")
    write_text(artifact_dir / "transcript.txt", transcript_text)
    write_json(artifact_dir / "transcript.segments.json", segments)
    if args.srt:
        write_text(artifact_dir / "transcript.srt", build_srt(segments))

    result = {
        "artifactDir": str(artifact_dir),
        "episode": episode_ref.episode.get("trackName", ""),
        "model": args.model,
        "language": getattr(info, "language", None),
        "languageProbability": getattr(info, "language_probability", None),
        "segmentCount": len(segments),
        "durationLabel": format_timestamp(segments[-1]["end"]) if segments else "00:00",
    }
    print_json(result)


if __name__ == "__main__":
    main()
