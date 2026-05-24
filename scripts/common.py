from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
CACHE_DIR = ROOT / ".cache"

EN_STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "your", "about", "they",
    "their", "there", "what", "when", "where", "which", "would", "could", "should", "into",
    "than", "them", "then", "were", "been", "being", "over", "also", "just", "like", "some",
    "more", "most", "such", "very", "only", "will", "here", "after", "before", "because",
}

ZH_STOPWORDS = {
    "我们", "你们", "他们", "这个", "那个", "一个", "一种", "一些", "如果", "所以", "然后", "就是",
    "还是", "因为", "已经", "没有", "可以", "觉得", "自己", "什么", "怎么", "不是", "现在", "其实",
    "比较", "这样", "那个时候", "这里", "那里", "一下", "时候", "里面", "出来", "还有", "以及",
}


class PodgistError(RuntimeError):
    pass


@dataclass
class EpisodeRef:
    artifact_dir: Path
    episode: dict[str, Any]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def slugify(value: str, fallback: str = "episode") -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:80] or fallback


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def estimate_word_count(text: str) -> int:
    latin_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", text)
    han_chars = re.findall(r"[\u4e00-\u9fff]", text)
    return len(latin_words) + len(han_chars)


def tokenize_keywords(text: str) -> list[str]:
    tokens: list[str] = []
    for match in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9'-]{2,}", text.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]{2,}", match):
            if match not in ZH_STOPWORDS:
                tokens.append(match)
            for size in (2, 3):
                if len(match) <= size:
                    continue
                for index in range(0, len(match) - size + 1):
                    shard = match[index : index + size]
                    if shard not in ZH_STOPWORDS:
                        tokens.append(shard)
        elif match not in EN_STOPWORDS:
            tokens.append(match)
    return tokens


def top_keywords(text: str, limit: int = 5) -> list[str]:
    counts: dict[str, int] = {}
    for token in tokenize_keywords(text):
        counts[token] = counts.get(token, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ordered[:limit]]


def shorten_text(text: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def clean_markdown_text(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def fetch_json(url: str, *, timeout: int = 30, headers: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(
        url,
        headers=headers or {"User-Agent": "podgist-skill/0.1 (+local plugin)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    return json.loads(data.decode("utf-8"))


def download_binary(url: str, destination: Path, *, timeout: int = 120) -> tuple[Path, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "podgist-skill/0.1 (+local plugin)"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type")
    ensure_dir(destination.parent)
    destination.write_bytes(data)
    return destination, content_type


def run_command(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        raise PodgistError(f"Missing executable: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise PodgistError(f"Command failed ({exc.returncode}): {' '.join(command)}") from exc


def require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise PodgistError(f"Missing {label}: {path}")
    return path


def load_episode_ref(artifact_dir: Path) -> EpisodeRef:
    episode = read_json(require_file(artifact_dir / "episode.json", "episode metadata"))
    return EpisodeRef(artifact_dir=artifact_dir, episode=episode)


def guess_extension(url: str, content_type: str | None) -> str:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".mp3", ".m4a", ".mp4", ".wav", ".aac", ".ogg"}:
        return suffix
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/aac": ".aac",
        "audio/ogg": ".ogg",
        "video/mp4": ".mp4",
    }
    if content_type:
        normalized = content_type.split(";")[0].strip().lower()
        return mapping.get(normalized, ".bin")
    return ".bin"


def print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
