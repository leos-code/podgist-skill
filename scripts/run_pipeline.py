#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from common import ARTIFACTS_DIR, PodgistError, print_json
from download_episode import build_artifact_dir  # type: ignore
from search_episodes import search_episodes  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the common search -> download -> transcribe -> analyze flow.")
    parser.add_argument("--query", required=True, help="Episode query")
    parser.add_argument("--limit", type=int, default=5, help="Candidate count to show")
    parser.add_argument("--select", type=int, help="Auto-select a candidate index")
    parser.add_argument("--model", default="small", help="Whisper model name when running transcription")
    return parser.parse_args()


def run_step(command: list[str]) -> dict:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def main() -> None:
    args = parse_args()
    candidates, _ = search_episodes(args.query, limit=args.limit, country="US", lang="en_us")
    if args.select is None:
        print_json(
            {
                "status": "selection_required",
                "query": args.query,
                "candidates": candidates,
            }
        )
        return
    if args.select < 0 or args.select >= len(candidates):
        raise PodgistError(f"--select must be between 0 and {len(candidates) - 1}")

    selected = candidates[args.select]
    artifact_dir = build_artifact_dir(Path(ARTIFACTS_DIR), selected)
    download_result = run_step(
        ["python3", "scripts/download_episode.py", "--candidate-json", json.dumps(selected, ensure_ascii=False)]
    )
    transcribe_result = run_step(
        [
            "python3",
            "scripts/transcribe_episode.py",
            "--artifact-dir",
            str(artifact_dir),
            "--model",
            args.model,
            "--srt",
        ]
    )
    analyze_result = run_step(
        ["python3", "scripts/analyze_episode.py", "--artifact-dir", str(artifact_dir)]
    )
    print_json(
        {
            "status": "completed",
            "candidate": selected,
            "artifactDir": str(artifact_dir),
            "download": download_result,
            "transcribe": transcribe_result,
            "analyze": analyze_result,
        }
    )


if __name__ == "__main__":
    main()
