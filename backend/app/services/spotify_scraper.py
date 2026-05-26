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
    type: str  # "track" | "album" | "playlist"
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


def _extract_next_data(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        return json.loads(script.string)
    return None


def _extract_resource_from_html(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        if script.string and "Spotify.Entity" in script.string:
            match = re.search(r"Spotify\.Entity\s*=\s*(\{.+?\});", script.string, re.DOTALL)
            if match:
                return json.loads(match.group(1))
    resource_script = soup.find("script", {"type": "application/json"})
    if resource_script and resource_script.string:
        try:
            data = json.loads(resource_script.string)
            return data
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _parse_track_from_entity(entity: dict, fallback_album: str = "", fallback_year: int | None = None) -> SpotifyTrackMeta:
    title = entity.get("name", "Unknown")
    artists = entity.get("artists", [])
    artist = ", ".join(a.get("name", "") for a in artists) if artists else "Unknown"
    album_data = entity.get("album", {})
    album = album_data.get("name", fallback_album) if album_data else fallback_album
    year = None
    release_date = album_data.get("release_date", "") if album_data else ""
    if not release_date:
        release_date = entity.get("release_date", "")
    if release_date:
        try:
            year = int(release_date[:4])
        except (ValueError, IndexError):
            year = fallback_year
    else:
        year = fallback_year
    duration_ms = entity.get("duration_ms", 0)
    images = entity.get("album", {}).get("images", []) if entity.get("album") else entity.get("images", [])
    cover_art_url = images[0].get("url", "") if images else ""
    spotify_id = entity.get("id", entity.get("uri", "").split(":")[-1])
    return SpotifyTrackMeta(
        title=title,
        artist=artist,
        album=album,
        year=year,
        duration_ms=duration_ms,
        cover_art_url=cover_art_url,
        spotify_id=spotify_id,
    )


async def _scrape_track(spotify_id: str) -> SpotifyTrackMeta:
    html = await _fetch_embed_page(f"track/{spotify_id}")
    next_data = _extract_next_data(html)
    if next_data:
        try:
            entity = next_data["props"]["pageProps"]["state"]["data"]["entity"]
            return _parse_track_from_entity(entity)
        except (KeyError, TypeError):
            pass
    entity = _extract_resource_from_html(html)
    if entity:
        return _parse_track_from_entity(entity)
    return _parse_track_from_og_tags(html, spotify_id)


def _parse_track_from_og_tags(html: str, spotify_id: str) -> SpotifyTrackMeta:
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    artist = ""
    og_title = soup.find("meta", property="og:title")
    if og_title:
        content = og_title.get("content", "")
        title = str(content)
    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        artist = str(og_desc.get("content", ""))
    og_image = soup.find("meta", property="og:image")
    cover_art_url = str(og_image.get("content", "")) if og_image else ""
    return SpotifyTrackMeta(
        title=title or "Unknown",
        artist=artist or "Unknown",
        album="",
        year=None,
        duration_ms=0,
        cover_art_url=cover_art_url,
        spotify_id=spotify_id,
    )


async def _scrape_album(spotify_id: str) -> list[SpotifyTrackMeta]:
    html = await _fetch_embed_page(f"album/{spotify_id}")
    next_data = _extract_next_data(html)
    tracks: list[SpotifyTrackMeta] = []
    if next_data:
        try:
            entity = next_data["props"]["pageProps"]["state"]["data"]["entity"]
            album_name = entity.get("name", "")
            year = None
            rd = entity.get("release_date", "")
            if rd:
                try:
                    year = int(rd[:4])
                except (ValueError, IndexError):
                    pass
            images = entity.get("images", [])
            cover = images[0].get("url", "") if images else ""
            track_list = entity.get("tracks", {}).get("items", [])
            for t in track_list:
                track = _parse_track_from_entity(t, fallback_album=album_name, fallback_year=year)
                if not track.cover_art_url:
                    track.cover_art_url = cover
                if not track.album:
                    track.album = album_name
                tracks.append(track)
            return tracks
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to parse album next_data: {e}")
    entity = _extract_resource_from_html(html)
    if entity:
        album_name = entity.get("name", "")
        year = None
        rd = entity.get("release_date", "")
        if rd:
            try:
                year = int(rd[:4])
            except (ValueError, IndexError):
                pass
        images = entity.get("images", [])
        cover = images[0].get("url", "") if images else ""
        for t in entity.get("tracks", {}).get("items", []):
            track = _parse_track_from_entity(t, fallback_album=album_name, fallback_year=year)
            if not track.cover_art_url:
                track.cover_art_url = cover
            tracks.append(track)
    return tracks


async def _scrape_playlist(spotify_id: str) -> list[SpotifyTrackMeta]:
    html = await _fetch_embed_page(f"playlist/{spotify_id}")
    next_data = _extract_next_data(html)
    tracks: list[SpotifyTrackMeta] = []
    if next_data:
        try:
            entity = next_data["props"]["pageProps"]["state"]["data"]["entity"]
            track_list = entity.get("tracks", {}).get("items", [])
            for item in track_list:
                t = item.get("track", item)
                track = _parse_track_from_entity(t)
                tracks.append(track)
            return tracks
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to parse playlist next_data: {e}")
    entity = _extract_resource_from_html(html)
    if entity:
        for item in entity.get("tracks", {}).get("items", []):
            t = item.get("track", item)
            track = _parse_track_from_entity(t)
            tracks.append(track)
    return tracks
