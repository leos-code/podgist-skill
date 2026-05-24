# Prompt Contracts

The plugin keeps repeatable data work in Python scripts and uses skills for interaction rules.

## Orchestrator contract

1. Search first.
2. Show 3-8 candidates with title, show, date, duration, and URL.
3. Wait for user selection when more than one plausible match exists.
4. Only after selection, download, transcribe, and analyze.
5. Return the Chinese blog summary plus topic timestamp table.

## Analysis contract

When a model is available, the analysis should still write the same artifact files:

- `analysis.md`: Chinese markdown article
- `topics.json`: 3-10 topic segments
- `summary.json`: structured recap for Q&A

The analysis output must include:

- whether the episode is worth hearing, and for whom
- a one-screen summary
- major themes
- notable claims or stories
- recommended listen-first segments
- timestamp table
- caveats or weak sections

## Q&A contract

- Load only saved local artifacts.
- Never re-download or re-transcribe unless the user explicitly starts a new workflow.
- Prefer citing topic ranges from `topics.json`.
- Fall back to transcript segment citations from `transcript.segments.json`.
