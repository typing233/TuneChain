from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Track

router = APIRouter()


@router.get("/{track_id}/stream")
async def stream_file(track_id: str, db: AsyncSession = Depends(get_db)):
    track = await db.get(Track, track_id)
    if not track or not track.file_path:
        raise HTTPException(status_code=404, detail="Track file not found")

    file_path = Path(track.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File does not exist on disk")

    media_types = {
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
    }
    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
    )


@router.get("/{track_id}/download")
async def download_file(track_id: str, db: AsyncSession = Depends(get_db)):
    track = await db.get(Track, track_id)
    if not track or not track.file_path:
        raise HTTPException(status_code=404, detail="Track file not found")

    file_path = Path(track.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File does not exist on disk")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )
