---
name: podcast-analyze
description: Turn a saved transcript into a Chinese blog-style analysis, worth-listening judgment, and topic-level timestamp map.
---

# Podcast Analyze

Use this skill after transcription artifacts exist.

## Workflow

Run:

```bash
python3 scripts/analyze_episode.py --artifact-dir artifacts/<slug>-<trackId>
```

## Output

- `analysis.md`
- `topics.json`
- `summary.json`

## Required response shape

- say whether the episode is worth hearing, and for whom
- include a one-screen summary
- list major themes
- call out notable claims or stories
- recommend listen-first segments
- show a timestamp table
- note caveats or weak sections

## Rules

- Default output language is Chinese.
- Topic segmentation should stay at 3-10 coarse sections.
- Keep the saved JSON artifacts stable for later Q&A reuse.
