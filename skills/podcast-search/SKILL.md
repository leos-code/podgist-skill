---
name: podcast-search
description: Search Apple podcast episode candidates from keywords and return a compact candidate list for user selection before any download or transcription.
---

# Podcast Search

Use this skill when the user wants to find a specific podcast episode by keywords.

## Workflow

1. Run:

```bash
python3 scripts/search_episodes.py --query "<user query>" --limit 5
```

2. Present 3-8 candidates with:
   - index
   - episode title
   - podcast name
   - date
   - duration
   - `trackViewUrl` when present

3. If more than one result looks plausible, stop and ask the user to choose.

## Rules

- Do not auto-download on ambiguous results.
- Keep the normalized candidate JSON so later steps can reuse it directly.
- Mention when a result lacks `episodeUrl` and may require `previewUrl` fallback later.
