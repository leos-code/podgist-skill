#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import (
    ARTIFACTS_DIR,
    PodgistError,
    download_binary,
    ensure_dir,
    format_timestamp,
    guess_extension,
    print_json,
    read_json,
    run_command,
    slugify,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and normalize a selected episode.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate-file", help="Path to a JSON candidate object or candidate list")
    group.add_argument("--candidate-json", help="Literal JSON object for the selected candidate")
    parser.add_argument("--index", type=int, default=0, help="Index to use when --candidate-file is a list")
    parser.add_argument("--artifacts-dir", default=str(ARTIFACTS_DIR), help="Artifact root directory")
    return parser.parse_args()


def load_candidate(args: argparse.Namespace) -> dict[str, Any]:
    if args.candidate_json:
        payload = json.loads(args.candidate_json)
    else:
        payload = read_json(Path(args.candidate_file))
    if isinstance(payload, list):
        try:
            candidate = payload[args.index]
        except IndexError as exc:
            raise PodgistError(f"Candidate index {args.index} is out of range") from exc
    elif isinstance(payload, dict):
        candidate = payload
    else:
        raise PodgistError("Candidate payload must be a JSON object or list")
    if not isinstance(candidate, dict):
        raise PodgistError("Selected candidate must be a JSON object")
    return candidate


def choose_source(candidate: dict[str, Any]) -> tuple[str, str]:
    episode_url = (candidate.get("episodeUrl") or "").strip()
    preview_url = (candidate.get("previewUrl") or "").strip()
    if episode_url:
        return episode_url, "episodeUrl"
    if preview_url:
        return preview_url, "previewUrl"
    raise PodgistError("Candidate has neither episodeUrl nor previewUrl")


def normalize_audio(input_path: Path, output_path: Path) -> None:
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-sample_fmt",
            "s16",
            str(output_path),
        ]
    )


def build_artifact_dir(artifacts_root: Path, candidate: dict[str, Any]) -> Path:
    title = candidate.get("trackName") or "episode"
    track_id = candidate.get("trackId") or 0
    return artifacts_root / f"{slugify(title)}-{track_id}"


def main() -> None:
    args = parse_args()
    candidate = load_candidate(args)
    artifacts_root = ensure_dir(Path(args.artifacts_dir))
    artifact_dir = build_artifact_dir(artifacts_root, candidate)
    raw_dir = ensure_dir(artifact_dir / "raw")

    source_url, source_field = choose_source(candidate)
    temp_path = raw_dir / "source-download"
    downloaded_path, content_type = download_binary(source_url, temp_path)
    raw_ext = guess_extension(source_url, content_type)
    raw_audio_path = downloaded_path.with_suffix(raw_ext)
    downloaded_path.rename(raw_audio_path)

    normalized_audio_path = artifact_dir / "audio.wav"
    normalize_audio(raw_audio_path, normalized_audio_path)

    episode_payload = {
        **candidate,
        "artifactDir": str(artifact_dir),
        "downloadSource": source_field,
        "downloadUrl": source_url,
        "rawAudioPath": str(raw_audio_path),
        "audioPath": str(normalized_audio_path),
        "durationLabel": format_timestamp((candidate.get("trackTimeMillis") or 0) / 1000),
    }
    write_json(artifact_dir / "episode.json", episode_payload)
    print_json(episode_payload)


if __name__ == "__main__":
    main()
