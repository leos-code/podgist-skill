# podgist-skill

Local Codex plugin for turning a podcast episode into saved local artifacts:

- episode search via Apple iTunes Search API
- episode download and ffmpeg normalization
- local transcription with `faster-whisper`
- Chinese analysis markdown and topic timestamps
- grounded follow-up Q&A over saved artifacts

## Layout

- `.codex-plugin/plugin.json`: plugin manifest
- `skills/`: six focused Codex skills plus an orchestrator
- `scripts/`: reusable Python pipeline
- `references/`: artifact and prompt contracts
- `evals/`: manual eval prompts
- `artifacts/`: per-episode outputs created by the scripts

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Required runtime dependencies:

- `ffmpeg` on `PATH`
- Python 3.10+
- `faster-whisper`

Optional:

- `OPENAI_API_KEY` to let `analyze_episode.py` and `qa_transcript.py` use the Responses API
  for richer natural-language output. Without it, both scripts fall back to local heuristic logic.

## Common flow

Search:

```bash
python3 scripts/search_episodes.py --query "lex fridman openai" --limit 5 --output /tmp/candidates.json
```

Download and normalize:

```bash
python3 scripts/download_episode.py --candidate-file /tmp/candidates.json --index 0
```

Transcribe:

```bash
python3 scripts/transcribe_episode.py --artifact-dir artifacts/<slug>-<trackId>
```

Analyze:

```bash
python3 scripts/analyze_episode.py --artifact-dir artifacts/<slug>-<trackId>
```

Follow-up Q&A:

```bash
python3 scripts/qa_transcript.py --artifact-dir artifacts/<slug>-<trackId> --question "只想听他讲创业低谷的部分"
```

Orchestrated run:

```bash
python3 scripts/run_pipeline.py --query "lex fridman openai"
```

## Artifact contract

Each episode gets one directory:

```
artifacts/<slug>-<trackId>/
```

Expected files:

- `episode.json`
- `audio.wav`
- `transcript.txt`
- `transcript.segments.json`
- `transcript.srt`
- `analysis.md`
- `topics.json`
- `summary.json`

See `references/artifact-contract.md` for the detailed schema.
