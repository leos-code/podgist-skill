---
name: podgist-orchestrator
description: Chain podcast search, selection, download, transcription, analysis, and later Q&A into a single user-facing workflow.
---

# Podgist Orchestrator

Use this skill for requests like:

- `帮我判断这个播客值不值得听`
- `搜索某期 podcast 并总结`
- `给我能快速跳听的时间点`

## Workflow

1. Search first:

```bash
python3 scripts/search_episodes.py --query "<user query>" --limit 5
```

2. Present candidates and wait for selection when the result is ambiguous.

3. After selection, run:

```bash
python3 scripts/download_episode.py --candidate-file <candidate-json-path> --index <n>
python3 scripts/transcribe_episode.py --artifact-dir artifacts/<slug>-<trackId> --srt
python3 scripts/analyze_episode.py --artifact-dir artifacts/<slug>-<trackId>
```

4. Return:
   - worth-listening judgment
   - one-screen summary
   - recommended segments
   - timestamp table

5. For follow-up questions, switch to `podcast-qa` and reuse the same artifact directory.

## Rules

- Default language is Chinese.
- Do not guess the best episode automatically when several look plausible.
- Explain preview-only fallback when the source audio is not a full episode file.
