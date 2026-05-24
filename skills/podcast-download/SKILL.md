---
name: podcast-download
description: Download the selected podcast episode to a local artifact directory and normalize it into a transcription-ready wav file.
---

# Podcast Download

Use this skill after the user has selected a single episode candidate.

## Workflow

1. Save or reuse the selected candidate JSON.
2. Run:

```bash
python3 scripts/download_episode.py --candidate-file <candidate-json-path> --index <n>
```

Or for a single object:

```bash
python3 scripts/download_episode.py --candidate-json '<json object>'
```

## Output

- `artifacts/<slug>-<trackId>/episode.json`
- `artifacts/<slug>-<trackId>/raw/source-download.*`
- `artifacts/<slug>-<trackId>/audio.wav`

## Rules

- Prefer `episodeUrl`.
- If `episodeUrl` is missing, fall back to `previewUrl` and state that explicitly.
- Do not start transcription inside this skill unless the user asked for the whole workflow.
