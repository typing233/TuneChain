import logging
from pathlib import Path

import httpx
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover

from app.services.spotify_scraper import SpotifyTrackMeta

logger = logging.getLogger(__name__)


async def _download_cover_art(url: str) -> bytes | None:
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.warning(f"Failed to download cover art: {e}")
        return None


async def embed_metadata(file_path: Path, meta: SpotifyTrackMeta) -> None:
    suffix = file_path.suffix.lower()
    cover_data = await _download_cover_art(meta.cover_art_url)

    if suffix == ".mp3":
        _embed_mp3(file_path, meta, cover_data)
    elif suffix == ".flac":
        _embed_flac(file_path, meta, cover_data)
    elif suffix == ".m4a":
        _embed_m4a(file_path, meta, cover_data)
    else:
        logger.warning(f"Unsupported format for metadata embedding: {suffix}")


def _embed_mp3(file_path: Path, meta: SpotifyTrackMeta, cover_data: bytes | None) -> None:
    audio = MP3(str(file_path))
    if audio.tags is None:
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=[meta.title]))
    audio.tags.add(TPE1(encoding=3, text=[meta.artist]))
    if meta.album:
        audio.tags.add(TALB(encoding=3, text=[meta.album]))
    if meta.year:
        audio.tags.add(TDRC(encoding=3, text=[str(meta.year)]))
    if cover_data:
        audio.tags.add(APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=cover_data,
        ))
    audio.save()


def _embed_flac(file_path: Path, meta: SpotifyTrackMeta, cover_data: bytes | None) -> None:
    audio = FLAC(str(file_path))
    audio["title"] = meta.title
    audio["artist"] = meta.artist
    if meta.album:
        audio["album"] = meta.album
    if meta.year:
        audio["date"] = str(meta.year)
    if cover_data:
        pic = Picture()
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.desc = "Cover"
        pic.data = cover_data
        audio.clear_pictures()
        audio.add_picture(pic)
    audio.save()


def _embed_m4a(file_path: Path, meta: SpotifyTrackMeta, cover_data: bytes | None) -> None:
    audio = MP4(str(file_path))
    audio["\xa9nam"] = [meta.title]
    audio["\xa9ART"] = [meta.artist]
    if meta.album:
        audio["\xa9alb"] = [meta.album]
    if meta.year:
        audio["\xa9day"] = [str(meta.year)]
    if cover_data:
        audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
    audio.save()
