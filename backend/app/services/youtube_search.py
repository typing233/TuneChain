import asyncio
import logging
from dataclasses import dataclass

from ytmusicapi import YTMusic

logger = logging.getLogger(__name__)

DURATION_TOLERANCE_SEC = 5
_ytmusic: YTMusic | None = None


def _get_ytmusic() -> YTMusic:
    global _ytmusic
    if _ytmusic is None:
        _ytmusic = YTMusic()
    return _ytmusic


@dataclass
class YouTubeMatch:
    video_id: str
    title: str
    duration_sec: int
    confidence: float


def _score_candidate(candidate_duration_sec: int, expected_ms: int) -> float:
    expected_sec = expected_ms / 1000
    diff = abs(candidate_duration_sec - expected_sec)
    if diff <= DURATION_TOLERANCE_SEC:
        return 1.0 - (diff / DURATION_TOLERANCE_SEC) * 0.2
    max_diff = 30.0
    if diff >= max_diff:
        return 0.0
    return max(0.0, 1.0 - diff / max_diff)


def _parse_duration(duration_str: str | None) -> int:
    if not duration_str:
        return 0
    parts = duration_str.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        pass
    return 0


def _search_sync(query: str, filter_type: str = "songs") -> list[dict]:
    yt = _get_ytmusic()
    try:
        results = yt.search(query, filter=filter_type, limit=10)
        return results or []
    except Exception as e:
        logger.warning(f"YTMusic search failed for '{query}': {e}")
        return []


async def search_youtube_music(
    title: str,
    artist: str,
    expected_duration_ms: int,
    timeout: float = 15.0,
) -> YouTubeMatch | None:
    query = f"{title} {artist}"
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(_search_sync, query, "songs"),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning(f"YouTube search timed out for: {query}")
        results = []

    if not results:
        try:
            fallback_results = await asyncio.wait_for(
                asyncio.to_thread(_search_sync, f"{title} {artist} audio", "videos"),
                timeout=timeout,
            )
            results = fallback_results
        except asyncio.TimeoutError:
            logger.warning(f"YouTube fallback search timed out for: {query}")
            return None

    if not results:
        return None

    best_match: YouTubeMatch | None = None
    best_score = -1.0

    for item in results:
        video_id = item.get("videoId")
        if not video_id:
            continue
        duration_str = item.get("duration")
        duration_seconds = item.get("duration_seconds")
        if duration_seconds:
            dur_sec = int(duration_seconds)
        else:
            dur_sec = _parse_duration(duration_str)

        score = _score_candidate(dur_sec, expected_duration_ms) if expected_duration_ms > 0 else 0.5
        item_title = item.get("title", "")

        if score > best_score:
            best_score = score
            best_match = YouTubeMatch(
                video_id=video_id,
                title=item_title,
                duration_sec=dur_sec,
                confidence=score,
            )

    return best_match
