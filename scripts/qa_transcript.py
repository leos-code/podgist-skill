#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from common import (
    PodgistError,
    format_timestamp,
    load_episode_ref,
    print_json,
    read_json,
    require_file,
    shorten_text,
    tokenize_keywords,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Answer grounded questions over saved podcast artifacts.")
    parser.add_argument("--artifact-dir", required=True, help="Episode artifact directory")
    parser.add_argument("--question", required=True, help="User follow-up question")
    return parser.parse_args()


def read_json_if_exists(path: Path) -> Any:
    if not path.is_file():
        return None
    return read_json(path)


def load_artifacts(artifact_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    episode = load_episode_ref(artifact_dir).episode
    topics = read_json_if_exists(artifact_dir / "topics.json") or []
    transcript_segments = read_json(require_file(artifact_dir / "transcript.segments.json", "transcript segments"))
    summary = read_json_if_exists(artifact_dir / "summary.json") or {
        "worthListening": {
            "verdict": "尚未生成完整分析",
            "reason": "当前仅使用转录片段回答。",
        }
    }
    return episode, topics, transcript_segments, summary


def overlap_score(question_terms: set[str], text: str) -> int:
    terms = tokenize_keywords(text)
    return sum(1 for term in terms if term in question_terms)


def heuristic_answer(
    episode: dict[str, Any],
    topics: list[dict[str, Any]],
    transcript_segments: list[dict[str, Any]],
    summary: dict[str, Any],
    question: str,
) -> dict[str, Any]:
    question_terms = set(tokenize_keywords(question))
    ranked_topics = sorted(
        topics,
        key=lambda item: overlap_score(
            question_terms,
            " ".join(
                [
                    str(item.get("title", "")),
                    str(item.get("why_it_matters", "")),
                    " ".join(item.get("keywords", [])),
                    str(item.get("listen_reason", "")),
                ]
            ),
        ),
        reverse=True,
    )
    ranked_segments = sorted(
        transcript_segments,
        key=lambda item: overlap_score(question_terms, str(item.get("text", ""))),
        reverse=True,
    )

    answer_lines = [f"问题：{question}", ""]
    citations: list[dict[str, str]] = []

    top_topic = ranked_topics[0] if ranked_topics else None
    if top_topic and overlap_score(question_terms, " ".join(top_topic.get("keywords", []))) > 0:
        answer_lines.append(
            "最相关的主题段是 "
            f"{format_timestamp(top_topic['start'])} - {format_timestamp(top_topic['end'])}："
            f"{top_topic['title']}。"
        )
        answer_lines.append(top_topic["why_it_matters"])
        citations.append(
            {
                "type": "topic",
                "range": f"{format_timestamp(top_topic['start'])} - {format_timestamp(top_topic['end'])}",
                "title": top_topic["title"],
            }
        )

    excerpt_matches = [item for item in ranked_segments[:3] if overlap_score(question_terms, item["text"]) > 0]
    if excerpt_matches:
        answer_lines.append("")
        answer_lines.append("转录里最接近问题的片段有：")
        for item in excerpt_matches:
            answer_lines.append(
                f"- {format_timestamp(item['start'])} - {format_timestamp(item['end'])} | "
                f"{shorten_text(item['text'], 120)}"
            )
            citations.append(
                {
                    "type": "transcript",
                    "range": f"{format_timestamp(item['start'])} - {format_timestamp(item['end'])}",
                    "text": shorten_text(item["text"], 120),
                }
            )
    else:
        answer_lines.append("现有主题摘要里没有直接命中这个问题，只能给出整体判断：")
        answer_lines.append(
            f"{summary['worthListening']['verdict']}。原因是：{summary['worthListening']['reason']}"
        )

    return {
        "episode": episode.get("trackName", ""),
        "question": question,
        "answer": "\n".join(answer_lines).strip(),
        "citations": citations,
        "analysisMethod": "heuristic",
    }


def maybe_openai_answer(context: dict[str, Any], question: str, artifact_dir: Path) -> dict[str, Any] | None:
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
                            "你是播客问答助手。只能依据提供的 transcript/topics/summary 回答，"
                            "必须用中文，并尽量给出时间段。返回 JSON，字段为 answer 和 citations。"
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
                            {"question": question, "context": context},
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
    if not isinstance(parsed, dict) or not isinstance(parsed.get("answer"), str):
        return None
    parsed["analysisMethod"] = "openai_responses"
    require_file(artifact_dir / "summary.json", "summary")
    return parsed


def main() -> None:
    args = parse_args()
    artifact_dir = Path(args.artifact_dir).resolve()
    episode, topics, transcript_segments, summary = load_artifacts(artifact_dir)

    context = {
        "episode": episode,
        "topics": topics[:6],
        "summary": summary,
        "transcriptMatches": transcript_segments[:100],
    }
    result = maybe_openai_answer(context, args.question, artifact_dir)
    if result is None:
        result = heuristic_answer(episode, topics, transcript_segments, summary, args.question)
    print_json(result)


if __name__ == "__main__":
    main()
