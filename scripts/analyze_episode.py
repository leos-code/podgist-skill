#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from common import (
    PodgistError,
    clean_markdown_text,
    estimate_word_count,
    format_timestamp,
    load_episode_ref,
    print_json,
    read_json,
    require_file,
    shorten_text,
    top_keywords,
    write_json,
    write_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a transcript into Chinese markdown and topic JSON.")
    parser.add_argument("--artifact-dir", required=True, help="Episode artifact directory")
    parser.add_argument(
        "--topic-count",
        type=int,
        help="Override the number of topic buckets. Defaults to a duration-based 3-10 range.",
    )
    return parser.parse_args()


def load_transcript(artifact_dir: Path) -> list[dict[str, Any]]:
    transcript_path = require_file(artifact_dir / "transcript.segments.json", "transcript segments")
    segments = read_json(transcript_path)
    if not isinstance(segments, list) or not all(isinstance(item, dict) for item in segments):
        raise PodgistError("transcript.segments.json must contain a list of segment objects")
    return segments


def choose_topic_count(segments: list[dict[str, Any]], override: int | None) -> int:
    if override is not None:
        return max(3, min(10, override))
    duration_seconds = float(segments[-1]["end"]) if segments else 0.0
    return max(3, min(10, round(duration_seconds / 1200) or 3))


def build_topics(segments: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if not segments:
        return []
    chunk_size = max(1, math.ceil(len(segments) / count))
    topics: list[dict[str, Any]] = []
    for index in range(0, len(segments), chunk_size):
        chunk = segments[index : index + chunk_size]
        joined_text = " ".join(str(item["text"]) for item in chunk)
        keywords = top_keywords(joined_text, limit=5)
        first_line = shorten_text(str(chunk[0]["text"]), limit=48)
        title = " / ".join(keywords[:2]) if len(keywords) >= 2 else first_line
        why_it_matters = (
            f"这段集中讨论 {', '.join(keywords[:3]) or '核心议题'}，适合用来快速判断这一期的主线。"
        )
        listen_reason = (
            f"如果你只想抓重点，可从 {format_timestamp(float(chunk[0]['start']))} 开始听这段。"
        )
        topics.append(
            {
                "title": title or f"主题 {len(topics) + 1}",
                "why_it_matters": why_it_matters,
                "start": round(float(chunk[0]["start"]), 3),
                "end": round(float(chunk[-1]["end"]), 3),
                "keywords": keywords,
                "listen_reason": listen_reason,
            }
        )
    return topics[:10]


def build_heuristic_summary(
    episode: dict[str, Any],
    segments: list[dict[str, Any]],
    topics: list[dict[str, Any]],
) -> dict[str, Any]:
    transcript_text = " ".join(str(item["text"]) for item in segments)
    keywords = top_keywords(transcript_text, limit=8)
    word_count = estimate_word_count(transcript_text)
    duration_seconds = float(segments[-1]["end"]) if segments else 0.0
    audience = []
    if any(token in {"创业", "融资", "business", "startup"} for token in keywords):
        audience.append("对创业和商业决策感兴趣的人")
    if any(token in {"ai", "模型", "人工智能", "machine", "learning"} for token in keywords):
        audience.append("想快速了解 AI 议题的人")
    if not audience:
        audience.append("想用较短时间判断这期播客是否值得投入的人")

    verdict = "值得一听" if len(topics) >= 3 and word_count >= 600 else "可先跳听重点片段"
    reason = (
        f"转录文本约 {word_count} 词，能提炼出 {len(topics)} 个主题段，信息密度"
        f"{'较高' if word_count >= 1200 else '中等'}。"
    )
    caveats = []
    if episode.get("downloadSource") == "previewUrl":
        caveats.append("本次基于 preview 音频处理，可能不是完整正片。")
    if duration_seconds and duration_seconds < 900:
        caveats.append("音频较短，结论更适合做预判而不是完整复盘。")
    if not caveats:
        caveats.append("主题切分依赖本地转录与启发式聚类，边界可能略粗。")

    one_screen_summary = [
        f"这期主要围绕：{', '.join(keywords[:4]) or '核心观点'}。",
        f"建议先听 {format_timestamp(topics[0]['start'])} - {format_timestamp(topics[0]['end'])} 抓主线。"
        if topics
        else "当前没有足够的转录内容来切主题。",
        f"更适合 {audience[0]}。",
    ]

    major_themes = [topic["title"] for topic in topics[:5]]
    notable_claims = [shorten_text(str(item["text"]), 96) for item in segments[: min(5, len(segments))]]
    recommended_segments = [
        {
            "title": topic["title"],
            "timestamp": f"{format_timestamp(topic['start'])} - {format_timestamp(topic['end'])}",
            "reason": topic["listen_reason"],
        }
        for topic in topics[: min(4, len(topics))]
    ]

    return {
        "episode": episode,
        "stats": {
            "segmentCount": len(segments),
            "wordCount": word_count,
            "durationSeconds": round(duration_seconds, 3),
            "topicCount": len(topics),
        },
        "worthListening": {
            "verdict": verdict,
            "audience": audience,
            "reason": reason,
            "caveats": caveats,
        },
        "oneScreenSummary": one_screen_summary,
        "majorThemes": major_themes,
        "notableClaimsOrStories": notable_claims,
        "recommendedSegments": recommended_segments,
        "analysisMethod": "heuristic",
    }


def build_markdown(summary: dict[str, Any], topics: list[dict[str, Any]]) -> str:
    episode = summary["episode"]
    worth = summary["worthListening"]
    lines = [
        f"# {episode.get('trackName') or '播客分析'}",
        "",
        f"- 节目：{episode.get('collectionName') or '未知节目'}",
        f"- 主播 / 作者：{episode.get('artistName') or '未知'}",
        f"- 发布时间：{episode.get('releaseDate') or '未知'}",
        f"- 是否值得听：**{worth['verdict']}**",
        "",
        "## 适合谁",
        "",
        f"- {'；'.join(worth['audience'])}",
        "",
        "## 一屏总结",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["oneScreenSummary"])
    lines.extend(["", "## 主要主题", ""])
    lines.extend(f"- {item}" for item in summary["majorThemes"])
    lines.extend(["", "## 值得注意的观点 / 故事", ""])
    lines.extend(f"- {item}" for item in summary["notableClaimsOrStories"])
    lines.extend(["", "## 推荐先听片段", ""])
    for item in summary["recommendedSegments"]:
        lines.append(f"- {item['timestamp']} | {item['title']} | {item['reason']}")
    lines.extend(["", "## 时间戳总表", "", "| 时间段 | 主题 | 为什么值得听 |", "| --- | --- | --- |"])
    for topic in topics:
        lines.append(
            f"| {format_timestamp(topic['start'])} - {format_timestamp(topic['end'])} "
            f"| {topic['title']} | {topic['why_it_matters']} |"
        )
    lines.extend(["", "## 可能的弱项 / 注意点", ""])
    lines.extend(f"- {item}" for item in worth["caveats"])
    return clean_markdown_text("\n".join(lines)) + "\n"


def maybe_openai_refine(summary: dict[str, Any], topics: list[dict[str, Any]], artifact_dir: Path) -> tuple[dict[str, Any], str] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import requests
    except ImportError:
        return None

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "你是播客分析助手。请基于提供的结构化摘要和主题分段，"
                            "输出 JSON，包含 improved_summary 和 analysis_markdown。"
                            "improved_summary 必须保持与输入 summary 相同的顶层字段。"
                            "analysis_markdown 必须是中文 Markdown。不要编造不存在的时间戳。"
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(
                            {"summary": summary, "topics": topics},
                            ensure_ascii=False,
                        ),
                    }
                ],
            },
        ],
        "text": {"format": {"type": "json_object"}},
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()
    output_text = body.get("output_text") or ""
    if not output_text:
        return None
    parsed = json.loads(output_text)
    improved_summary = parsed.get("improved_summary")
    analysis_markdown = parsed.get("analysis_markdown")
    if not isinstance(improved_summary, dict) or not isinstance(analysis_markdown, str):
        return None
    improved_summary["analysisMethod"] = "openai_responses"
    write_json(artifact_dir / "summary.openai.raw.json", body)
    return improved_summary, clean_markdown_text(analysis_markdown) + "\n"


def main() -> None:
    args = parse_args()
    artifact_dir = Path(args.artifact_dir).resolve()
    episode_ref = load_episode_ref(artifact_dir)
    segments = load_transcript(artifact_dir)
    topic_count = choose_topic_count(segments, args.topic_count)
    topics = build_topics(segments, topic_count)
    summary = build_heuristic_summary(episode_ref.episode, segments, topics)
    analysis_md = build_markdown(summary, topics)

    openai_result = maybe_openai_refine(summary, topics, artifact_dir)
    if openai_result is not None:
        summary, analysis_md = openai_result

    write_json(artifact_dir / "topics.json", topics)
    write_json(artifact_dir / "summary.json", summary)
    write_text(artifact_dir / "analysis.md", analysis_md)

    print_json(
        {
            "artifactDir": str(artifact_dir),
            "analysisMethod": summary["analysisMethod"],
            "topicCount": len(topics),
            "analysisPath": str(artifact_dir / "analysis.md"),
        }
    )


if __name__ == "__main__":
    main()
