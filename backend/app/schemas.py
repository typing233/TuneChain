from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    url: str
    format: str = "mp3"
    quality: str = "320"


class TrackResponse(BaseModel):
    id: str
    spotify_id: str
    title: str
    artist: str
    album: str | None = None
    year: int | None = None
    duration_ms: int | None = None
    cover_art_url: str | None = None
    youtube_id: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: str
    spotify_url: str
    type: str
    format: str
    quality: str
    status: str
    track_count: int
    completed_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime
    tracks: list[TrackResponse] = []

    model_config = {"from_attributes": True}


class TaskListItem(BaseModel):
    id: str
    spotify_url: str
    type: str
    format: str
    status: str
    track_count: int
    completed_count: int
    failed_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LibraryTrack(BaseModel):
    id: str
    title: str
    artist: str
    album: str | None = None
    year: int | None = None
    cover_art_url: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    duration_ms: int | None = None

    model_config = {"from_attributes": True}


class ProgressMessage(BaseModel):
    type: str
    task_id: str
    current_track: int = 0
    total_tracks: int = 0
    track_title: str = ""
    percent: float = 0
    overall_percent: float = 0
    status: str = ""
