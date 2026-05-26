from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Task, Track
from app.schemas import TaskCreate, TaskResponse, TaskListItem
from app.services.spotify_scraper import scrape_spotify, SpotifyTrackMeta
from app.services.task_queue import task_queue

router = APIRouter()


@router.post("", response_model=TaskResponse)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await scrape_spotify(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to scrape Spotify: {str(e)[:200]}")

    if not result.tracks:
        raise HTTPException(status_code=404, detail="No tracks found at this URL")

    task = Task(
        spotify_url=body.url,
        type=result.type,
        format=body.format,
        quality=body.quality,
        status="pending",
        track_count=len(result.tracks),
    )
    db.add(task)

    track_models: list[Track] = []
    for meta in result.tracks:
        track = Track(
            task_id=task.id,
            spotify_id=meta.spotify_id,
            title=meta.title,
            artist=meta.artist,
            album=meta.album,
            year=meta.year,
            duration_ms=meta.duration_ms,
            cover_art_url=meta.cover_art_url,
            status="pending",
        )
        db.add(track)
        track_models.append(track)

    await db.commit()
    await db.refresh(task)
    for t in track_models:
        await db.refresh(t)

    task.tracks = track_models

    await task_queue.submit(task.id, result.tracks, body.format, body.quality)

    return task


@router.get("", response_model=list[TaskListItem])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).order_by(Task.created_at.desc()).limit(50)
    )
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.id == task_id).options(selectinload(Task.tracks))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    cancelled = task_queue.cancel(task_id)
    if cancelled:
        task.status = "cancelled"
        await db.commit()
    return {"success": cancelled}
