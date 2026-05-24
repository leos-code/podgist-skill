#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
from pathlib import Path
from typing import Any

from common import CACHE_DIR, PodgistError, ensure_dir, fetch_json, print_json, write_json


SEARCH_ENDPOINT = "https://itunes.apple.com/search"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Apple podcast episodes.")
    parser.add_argument("--query", required=True, help="Free-text episode query")
    parser.add_argument("--limit", type=int, default=5, help="Max candidates to return")
    parser.add_argument("--country", default="US", help="Apple search country code")
    parser.add_argument("--lang", default="en_us", help="Apple search language")
    parser.add_argument("--output", help="Optional JSON file to write normalized candidates")
    parser.add_argument(
        "--raw-output",
        help="Optional JSON file for the raw Apple response; defaults to .cache/search/<hash>.json",
    )
    return parser.parse_args()


def normalize_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "trackId": int(item.get("trackId") or 0),
        "trackName": item.get("trackName") or "",
        "collectionName": item.get("collectionName") or "",
        "artistName": item.get("artistName") or "",
        "releaseDate": item.get("releaseDate") or "",
        "trackTimeMillis": int(item.get("trackTimeMillis") or 0),
        "description": item.get("description") or item.get("shortDescription") or "",
        "episodeUrl": item.get("episodeUrl") or "",
        "previewUrl": item.get("previewUrl") or "",
        "feedUrl": item.get("feedUrl") or "",
        "trackViewUrl": item.get("trackViewUrl") or "",
    }


def search_episodes(query: str, *, limit: int, country: str, lang: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    params = {
        "term": query,
        "media": "podcast",
        "entity": "podcastEpisode",
        "limit": str(limit),
        "country": country,
        "lang": lang,
    }
    url = f"{SEARCH_ENDPOINT}?{urllib.parse.urlencode(params)}"
    payload = fetch_json(url)
    results = payload.get("results")
    if not isinstance(results, list):
        raise PodgistError("Apple search response did not contain a results list")
    normalized = [normalize_candidate(item) for item in results if isinstance(item, dict)]
    return normalized, payload


def default_raw_cache_path(query: str, limit: int, country: str, lang: str) -> Path:
    digest = hashlib.sha256(f"{query}|{limit}|{country}|{lang}".encode("utf-8")).hexdigest()[:16]
    return ensure_dir(CACHE_DIR / "search") / f"{digest}.json"


def main() -> None:
    args = parse_args()
    candidates, raw_payload = search_episodes(
        args.query,
        limit=args.limit,
        country=args.country,
        lang=args.lang,
    )

    raw_path = Path(args.raw_output) if args.raw_output else default_raw_cache_path(
        args.query, args.limit, args.country, args.lang
    )
    write_json(raw_path, raw_payload)

    if args.output:
        write_json(Path(args.output), candidates)
    print_json(candidates)


if __name__ == "__main__":
    main()
