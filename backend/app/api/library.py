from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Track
from app.schemas import LibraryTrack

router = APIRouter()


@router.get("/tracks", response_model=list[LibraryTrack])
async def list_tracks(
    search: str = Query(default="", description="Search by title, artist, or album"),
    artist: str = Query(default="", description="Filter by artist"),
    album: str = Query(default="", description="Filter by album"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Track).where(Track.status == "completed", Track.file_path.isnot(None))

    if search:
        pattern = f"%{search}%"
        query = query.where(
            (Track.title.ilike(pattern)) |
            (Track.artist.ilike(pattern)) |
            (Track.album.ilike(pattern))
        )
    if artist:
        query = query.where(Track.artist.ilike(f"%{artist}%"))
    if album:
        query = query.where(Track.album.ilike(f"%{album}%"))

    query = query.order_by(Track.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/albums")
async def list_albums(
    search: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Track.album,
        Track.artist,
        Track.cover_art_url,
        Track.year,
        func.count(Track.id).label("track_count"),
    ).where(
        Track.status == "completed",
        Track.file_path.isnot(None),
        Track.album.isnot(None),
        Track.album != "",
    ).group_by(Track.album, Track.artist)

    if search:
        query = query.where(Track.album.ilike(f"%{search}%"))

    query = query.order_by(Track.album)
    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "album": r.album,
            "artist": r.artist,
            "cover_art_url": r.cover_art_url,
            "year": r.year,
            "track_count": r.track_count,
        }
        for r in rows
    ]


@router.get("/artists")
async def list_artists(db: AsyncSession = Depends(get_db)):
    query = select(
        Track.artist,
        func.count(Track.id).label("track_count"),
    ).where(
        Track.status == "completed",
        Track.file_path.isnot(None),
    ).group_by(Track.artist).order_by(Track.artist)

    result = await db.execute(query)
    rows = result.all()
    return [{"artist": r.artist, "track_count": r.track_count} for r in rows]
