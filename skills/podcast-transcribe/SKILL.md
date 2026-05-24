---
name: podcast-transcribe
description: Transcribe a locally normalized podcast audio file with faster-whisper and save timestamped transcript artifacts.
---

# Podcast Transcribe

Use this skill when an artifact directory already contains `audio.wav`.

## Workflow

Run:

```bash
python3 scripts/transcribe_episode.py --artifact-dir artifacts/<slug>-<trackId> --srt
```

## Output

- `transcript.txt`
- `transcript.segments.json`
- `transcript.srt`

## Rules

- Use `faster-whisper`, not the missing `whisper` CLI.
- Default model is `small`; override only when the user asks for speed or higher fidelity.
- Report missing dependencies clearly if `faster-whisper` is not installed.
