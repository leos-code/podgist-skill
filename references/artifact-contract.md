# Artifact Contract

Each analyzed episode is stored in:

```text
artifacts/<slug>-<trackId>/
```

Required files:

- `episode.json`
- `audio.wav`
- `transcript.txt`
- `transcript.segments.json`
- `analysis.md`
- `topics.json`
- `summary.json`

Optional files:

- `transcript.srt`
- `raw/` with source download and raw API responses

## Candidate schema

```json
{
  "trackId": 0,
  "trackName": "",
  "collectionName": "",
  "artistName": "",
  "releaseDate": "",
  "trackTimeMillis": 0,
  "description": "",
  "episodeUrl": "",
  "previewUrl": "",
  "feedUrl": "",
  "trackViewUrl": ""
}
```

## Transcript segment schema

```json
{
  "start": 0.0,
  "end": 0.0,
  "text": ""
}
```

## Topic schema

```json
{
  "title": "",
  "why_it_matters": "",
  "start": 0.0,
  "end": 0.0,
  "keywords": [],
  "listen_reason": ""
}
```

## Summary schema

```json
{
  "episode": {},
  "stats": {
    "segmentCount": 0,
    "wordCount": 0,
    "durationSeconds": 0.0,
    "topicCount": 0
  },
  "worthListening": {
    "verdict": "值得一听",
    "audience": [],
    "reason": "",
    "caveats": []
  },
  "oneScreenSummary": [],
  "majorThemes": [],
  "notableClaimsOrStories": [],
  "recommendedSegments": [],
  "analysisMethod": "heuristic|openai_responses"
}
```
