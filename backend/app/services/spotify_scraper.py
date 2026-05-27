import re
import json
import asyncio
import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.utils.http_client import get_http_client

logger = logging.getLogger(__name__)

SPOTIFY_URL_PATTERN = re.compile(
    r"https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)"
)

GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


@dataclass
class SpotifyTrackMeta:
    title: str
    artist: str
    album: str
    year: int | None
    duration_ms: int
    cover_art_url: str
    spotify_id: str


@dataclass
class SpotifyParsedResult:
    type: str
    tracks: list[SpotifyTrackMeta]


def parse_spotify_url(url: str) -> tuple[str, str]:
    match = SPOTIFY_URL_PATTERN.search(url)
    if not match:
        raise ValueError(f"Invalid Spotify URL: {url}")
    return match.group(1), match.group(2)


async def scrape_spotify(url: str) -> SpotifyParsedResult:
    url_type, spotify_id = parse_spotify_url(url)
    if url_type == "track":
        track = await _scrape_track(spotify_id)
        return SpotifyParsedResult(type="track", tracks=[track])
    elif url_type == "album":
        tracks = await _scrape_album(spotify_id)
        return SpotifyParsedResult(type="album", tracks=tracks)
    elif url_type == "playlist":
        tracks = await _scrape_playlist(spotify_id)
        return SpotifyParsedResult(type="playlist", tracks=tracks)
    else:
        raise ValueError(f"Unsupported Spotify URL type: {url_type}")


async def _fetch_page(url: str, user_agent: str = BROWSER_UA) -> str:
    client = await get_http_client()
    resp = await client.get(url, headers={"User-Agent": user_agent})
    resp.raise_for_status()
    return resp.text


async def _fetch_embed_page(path: str) -> str:
    return await _fetch_page(f"https://open.spotify.com/embed/{path}")


async def _fetch_meta_page(path: str) -> str:
    return await _fetch_page(f"https://open.spotify.com/{path}", user_agent=GOOGLEBOT_UA)


def _extract_entity(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        raise ValueError("Could not find __NEXT_DATA__ in embed page")
    data = json.loads(script.string)
    try:
        return data["props"]["pageProps"]["state"]["data"]["entity"]
    except (KeyError, TypeError) as e:
        raise ValueError(f"Unexpected embed page structure: {e}")


def _get_cover_url(entity: dict) -> str:
    vi = entity.get("visualIdentity", {})
    images = vi.get("image", [])
    if images:
        largest = max(images, key=lambda i: i.get("maxHeight", 0))
        return largest.get("url", "")
    return ""


def _extract_spotify_id_from_uri(uri: str) -> str:
    parts = uri.split(":")
    return parts[-1] if parts else ""


def _parse_meta_tags(html: str) -> dict[str, str | list[str]]:
    """Parse OG/music meta tags from a Googlebot-fetched page."""
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, str | list[str]] = {}
    songs: list[str] = []

    for meta in soup.find_all("meta"):
        prop = meta.get("property", "") or meta.get("name", "")
        content = meta.get("content", "")
        if not content or not prop:
            continue
        if prop == "music:song":
            songs.append(content)
        elif prop not in result:
            result[prop] = content

    if songs:
        result["music:songs"] = songs
    return result


def _parse_og_description_track(desc: str) -> tuple[str, str, int | None]:
    """Parse og:description like 'Rick Astley · Whenever You Need Somebody · Song · 1987'
    Returns (artist, album, year)."""
    parts = [p.strip() for p in desc.split("·")]
    artist = parts[0] if len(parts) > 0 else ""
    album = ""
    year = None

    if len(parts) >= 4:
        album = parts[1]
        try:
            year = int(parts[-1])
        except ValueError:
            pass
    elif len(parts) == 3:
        # Could be "Artist · Album · Year" or "Artist · Song · Year"
        if parts[1] in ("Song", "Podcast"):
            try:
                year = int(parts[2])
            except ValueError:
                pass
        else:
            album = parts[1]
            try:
                year = int(parts[2])
            except ValueError:
                pass
    elif len(parts) == 2:
        try:
            year = int(parts[1])
        except ValueError:
            album = parts[1]

    return artist, album, year


async def _scrape_track(spotify_id: str) -> SpotifyTrackMeta:
    """Scrape a single track using embed page (for duration) + meta page (for album/year)."""
    embed_html, meta_html = await asyncio.gather(
        _fetch_embed_page(f"track/{spotify_id}"),
        _fetch_meta_page(f"track/{spotify_id}"),
    )

    # From embed page: title, artists, duration, cover
    entity = _extract_entity(embed_html)
    title = entity.get("name", "") or entity.get("title", "")
    artists_list = entity.get("artists", [])
    artist = ", ".join(a.get("name", "") for a in artists_list) if artists_list else "Unknown"
    duration_ms = entity.get("duration", 0)
    cover_art_url = _get_cover_url(entity)

    # From meta page: album name, year, release_date
    meta = _parse_meta_tags(meta_html)
    og_desc = meta.get("og:description", "")
    _, album, year = _parse_og_description_track(str(og_desc))

    # Prefer music:release_date for year if available
    release_date = str(meta.get("music:release_date", ""))
    if release_date and len(release_date) >= 4:
        try:
            year = int(release_date[:4])
        except ValueError:
            pass

    # Cover from meta if embed didn't have it
    if not cover_art_url:
        cover_art_url = str(meta.get("og:image", ""))

    return SpotifyTrackMeta(
        title=title,
        artist=artist,
        album=album,
        year=year,
        duration_ms=duration_ms,
        cover_art_url=cover_art_url,
        spotify_id=spotify_id,
    )


async def _scrape_track_meta_only(spotify_id: str) -> tuple[str, int | None]:
    """Fetch only the meta page for a track to get album name and year.
    Returns (album, year). Used for enriching playlist tracks."""
    try:
        html = await _fetch_meta_page(f"track/{spotify_id}")
        meta = _parse_meta_tags(html)
        og_desc = meta.get("og:description", "")
        _, album, year = _parse_og_description_track(str(og_desc))
        release_date = str(meta.get("music:release_date", ""))
        if release_date and len(release_date) >= 4:
            try:
                year = int(release_date[:4])
            except ValueError:
                pass
        return album, year
    except Exception as e:
        logger.warning(f"Failed to fetch track meta for {spotify_id}: {e}")
        return "", None


async def _scrape_album(spotify_id: str) -> list[SpotifyTrackMeta]:
    """Scrape an album using embed page (for track list with durations) + meta page (for year)."""
    embed_html, meta_html = await asyncio.gather(
        _fetch_embed_page(f"album/{spotify_id}"),
        _fetch_meta_page(f"album/{spotify_id}"),
    )

    entity = _extract_entity(embed_html)
    album_name = entity.get("name", "") or entity.get("title", "")
    album_artist = entity.get("subtitle", "") or "Unknown"
    cover_art_url = _get_cover_url(entity)

    track_list = entity.get("trackList", [])
    if not track_list:
        raise ValueError("Album embed page returned no tracks")

    # Get year from meta page
    meta = _parse_meta_tags(meta_html)
    year: int | None = None
    release_date = str(meta.get("music:release_date", ""))
    if release_date and len(release_date) >= 4:
        try:
            year = int(release_date[:4])
        except ValueError:
            pass

    # Also try cover from meta page if embed didn't have it
    if not cover_art_url:
        cover_art_url = str(meta.get("og:image", ""))

    tracks: list[SpotifyTrackMeta] = []
    for item in track_list:
        track_uri = item.get("uri", "")
        track_id = _extract_spotify_id_from_uri(track_uri)
        title = item.get("title", "")
        artist = item.get("subtitle", "") or album_artist
        duration_ms = item.get("duration", 0)

        tracks.append(SpotifyTrackMeta(
            title=title,
            artist=artist,
            album=album_name,
            year=year,
            duration_ms=duration_ms,
            cover_art_url=cover_art_url,
            spotify_id=track_id or track_uri,
        ))

    return tracks


async def _scrape_playlist(spotify_id: str) -> list[SpotifyTrackMeta]:
    """Scrape a playlist: embed page for track list, then batch-fetch each track's
    meta page for album name and year."""
    embed_html = await _fetch_embed_page(f"playlist/{spotify_id}")
    entity = _extract_entity(embed_html)

    playlist_cover = _get_cover_url(entity)
    track_list = entity.get("trackList", [])
    if not track_list:
        raise ValueError("Playlist embed page returned no tracks")

    # Build initial track list from embed (has title, artist, duration)
    track_ids: list[str] = []
    base_tracks: list[dict] = []
    for item in track_list:
        track_uri = item.get("uri", "")
        track_id = _extract_spotify_id_from_uri(track_uri)
        track_ids.append(track_id)
        base_tracks.append({
            "title": item.get("title", ""),
            "artist": item.get("subtitle", "") or "Unknown",
            "duration_ms": item.get("duration", 0),
            "spotify_id": track_id or track_uri,
        })

    # Batch-fetch individual track meta pages for album + year (with concurrency limit)
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_limit(tid: str) -> tuple[str, int | None]:
        async with semaphore:
            return await _scrape_track_meta_only(tid)

    enrichments = await asyncio.gather(
        *(fetch_with_limit(tid) for tid in track_ids)
    )

    tracks: list[SpotifyTrackMeta] = []
    for base, (album, year) in zip(base_tracks, enrichments):
        tracks.append(SpotifyTrackMeta(
            title=base["title"],
            artist=base["artist"],
            album=album,
            year=year,
            duration_ms=base["duration_ms"],
            cover_art_url=playlist_cover,
            spotify_id=base["spotify_id"],
        ))

    return tracks
