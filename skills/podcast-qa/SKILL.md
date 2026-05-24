---
name: podcast-qa
description: Answer follow-up questions over an existing analyzed episode using only saved local transcript and analysis artifacts.
---

# Podcast QA

Use this skill for questions like:

- `他在哪一段提到 X`
- `只看关于 AI / 创业 / 融资的部分`
- `这段怎么评价`

## Workflow

Run:

```bash
python3 scripts/qa_transcript.py --artifact-dir artifacts/<slug>-<trackId> --question "<user question>"
```

## Rules

- Never re-download or re-transcribe unless the user explicitly starts a new analysis workflow.
- Prefer citing `topics.json` timestamp ranges.
- Fall back to transcript segment citations when the topic map is too coarse.
