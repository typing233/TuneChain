import re
import json
import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.utils.http_client import get_http_client

logger = logging.getLogger(__name__)

SPOTIFY_URL_PATTERN = re.compile(
    r"https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)"
)


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


async def _fetch_embed_page(path: str) -> str:
    client = await get_http_client()
    url = f"https://open.spotify.com/embed/{path}"
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.text


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


def _get_year_from_release_date(release_date: dict | None) -> int | None:
    if not release_date:
        return None
    iso = release_date.get("isoString", "")
    if iso and len(iso) >= 4:
        try:
            return int(iso[:4])
        except ValueError:
            return None
    return None


def _extract_spotify_id_from_uri(uri: str) -> str:
    parts = uri.split(":")
    return parts[-1] if parts else ""


async def _scrape_track(spotify_id: str) -> SpotifyTrackMeta:
    html = await _fetch_embed_page(f"track/{spotify_id}")
    entity = _extract_entity(html)

    title = entity.get("name", "") or entity.get("title", "")
    artists_list = entity.get("artists", [])
    artist = ", ".join(a.get("name", "") for a in artists_list) if artists_list else "Unknown"
    year = _get_year_from_release_date(entity.get("releaseDate"))
    duration_ms = entity.get("duration", 0)
    cover_art_url = _get_cover_url(entity)

    # Album name is not directly available in track embed pages.
    # We use the title field from the cover alt tag as a fallback, but it's the track title.
    # Album name cannot be reliably extracted from embed-only scraping for single tracks.
    album = ""

    return SpotifyTrackMeta(
        title=title,
        artist=artist,
        album=album,
        year=year,
        duration_ms=duration_ms,
        cover_art_url=cover_art_url,
        spotify_id=spotify_id,
    )


async def _scrape_album(spotify_id: str) -> list[SpotifyTrackMeta]:
    html = await _fetch_embed_page(f"album/{spotify_id}")
    entity = _extract_entity(html)

    album_name = entity.get("name", "") or entity.get("title", "")
    album_artist = entity.get("subtitle", "") or "Unknown"
    cover_art_url = _get_cover_url(entity)

    track_list = entity.get("trackList", [])
    if not track_list:
        raise ValueError("Album embed page returned no tracks")

    # Fetch the first track's embed page to get the release year
    year: int | None = None
    first_track_uri = track_list[0].get("uri", "")
    first_track_id = _extract_spotify_id_from_uri(first_track_uri)
    if first_track_id:
        try:
            first_track_html = await _fetch_embed_page(f"track/{first_track_id}")
            first_entity = _extract_entity(first_track_html)
            year = _get_year_from_release_date(first_entity.get("releaseDate"))
        except Exception as e:
            logger.warning(f"Could not fetch year from first track: {e}")

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
    html = await _fetch_embed_page(f"playlist/{spotify_id}")
    entity = _extract_entity(html)

    cover_art_url = _get_cover_url(entity)
    track_list = entity.get("trackList", [])
    if not track_list:
        raise ValueError("Playlist embed page returned no tracks")

    tracks: list[SpotifyTrackMeta] = []
    for item in track_list:
        track_uri = item.get("uri", "")
        track_id = _extract_spotify_id_from_uri(track_uri)
        title = item.get("title", "")
        artist = item.get("subtitle", "") or "Unknown"
        duration_ms = item.get("duration", 0)

        tracks.append(SpotifyTrackMeta(
            title=title,
            artist=artist,
            album="",
            year=None,
            duration_ms=duration_ms,
            cover_art_url=cover_art_url,
            spotify_id=track_id or track_uri,
        ))

    return tracks
