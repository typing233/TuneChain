import asyncio
import logging
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models import Task, Track
from app.services.spotify_scraper import SpotifyTrackMeta
from app.services.youtube_search import search_youtube_music
from app.services.downloader import download_audio, DownloadError
from app.services.metadata import embed_metadata
from app.ws.progress import manager as ws_manager

logger = logging.getLogger(__name__)


class TaskQueue:
    def __init__(self, max_concurrent: int | None = None):
        self._max = max_concurrent or settings.max_concurrent_downloads
        self._semaphore = asyncio.Semaphore(self._max)
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(self, task_id: str, tracks_meta: list[SpotifyTrackMeta], audio_format: str, quality: str):
        task = asyncio.create_task(self._process_task(task_id, tracks_meta, audio_format, quality))
        self._tasks[task_id] = task

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    async def _process_task(self, task_id: str, tracks_meta: list[SpotifyTrackMeta], audio_format: str, quality: str):
        async with self._semaphore:
            async with async_session() as db:
                task = await db.get(Task, task_id)
                if task:
                    task.status = "processing"
                    await db.commit()

            total = len(tracks_meta)
            for idx, meta in enumerate(tracks_meta):
                if asyncio.current_task().cancelled():
                    break
                await self._process_track(task_id, meta, idx, total, audio_format, quality)

            async with async_session() as db:
                task = await db.get(Task, task_id)
                if task:
                    if task.failed_count == task.track_count:
                        task.status = "failed"
                    else:
                        task.status = "completed"
                    await db.commit()

            await ws_manager.broadcast(task_id, {
                "type": "task_complete",
                "task_id": task_id,
                "status": "completed",
            })

    async def _process_track(
        self, task_id: str, meta: SpotifyTrackMeta, idx: int, total: int,
        audio_format: str, quality: str
    ):
        async with async_session() as db:
            result = await db.execute(
                select(Track).where(Track.task_id == task_id, Track.spotify_id == meta.spotify_id)
            )
            track = result.scalar_one_or_none()
            if not track:
                return

            track.status = "searching"
            await db.commit()

        await ws_manager.broadcast(task_id, {
            "type": "progress",
            "task_id": task_id,
            "current_track": idx + 1,
            "total_tracks": total,
            "track_title": meta.title,
            "percent": 0,
            "overall_percent": (idx / total) * 100,
            "status": "searching",
        })

        yt_match = await search_youtube_music(meta.title, meta.artist, meta.duration_ms)

        if not yt_match:
            async with async_session() as db:
                track = await db.get(Track, track.id)
                track.status = "failed"
                track.error_message = "No YouTube match found"
                task_obj = await db.get(Task, task_id)
                task_obj.failed_count += 1
                await db.commit()
            await ws_manager.broadcast(task_id, {
                "type": "error",
                "task_id": task_id,
                "current_track": idx + 1,
                "track_title": meta.title,
                "status": "failed",
                "error": "No YouTube match found",
            })
            return

        async with async_session() as db:
            track_obj = await db.get(Track, track.id)
            track_obj.youtube_id = yt_match.video_id
            track_obj.status = "downloading"
            await db.commit()

        safe_title = re.sub(r'[<>:"/\\|?*]', '_', f"{meta.artist} - {meta.title}")

        async def on_progress(percent: float):
            overall = ((idx + percent / 100) / total) * 100
            await ws_manager.broadcast(task_id, {
                "type": "progress",
                "task_id": task_id,
                "current_track": idx + 1,
                "total_tracks": total,
                "track_title": meta.title,
                "percent": percent,
                "overall_percent": overall,
                "status": "downloading",
            })

        try:
            file_path = await download_audio(
                video_id=yt_match.video_id,
                output_dir=settings.download_dir,
                audio_format=audio_format,
                quality=quality,
                filename=safe_title,
                progress_callback=on_progress,
            )
        except DownloadError as e:
            async with async_session() as db:
                track_obj = await db.get(Track, track.id)
                track_obj.status = "failed"
                track_obj.error_message = str(e)[:500]
                task_obj = await db.get(Task, task_id)
                task_obj.failed_count += 1
                await db.commit()
            await ws_manager.broadcast(task_id, {
                "type": "error",
                "task_id": task_id,
                "current_track": idx + 1,
                "track_title": meta.title,
                "status": "failed",
                "error": str(e)[:200],
            })
            return

        async with async_session() as db:
            track_obj = await db.get(Track, track.id)
            track_obj.status = "embedding"
            await db.commit()

        try:
            await embed_metadata(file_path, meta)
        except Exception as e:
            logger.warning(f"Metadata embedding failed for {meta.title}: {e}")

        file_size = file_path.stat().st_size if file_path.exists() else 0

        async with async_session() as db:
            track_obj = await db.get(Track, track.id)
            track_obj.status = "completed"
            track_obj.file_path = str(file_path)
            track_obj.file_size = file_size
            task_obj = await db.get(Task, task_id)
            task_obj.completed_count += 1
            await db.commit()

        await ws_manager.broadcast(task_id, {
            "type": "track_complete",
            "task_id": task_id,
            "current_track": idx + 1,
            "total_tracks": total,
            "track_title": meta.title,
            "percent": 100,
            "overall_percent": ((idx + 1) / total) * 100,
            "status": "completed",
        })


task_queue = TaskQueue()
