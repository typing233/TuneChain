import asyncio
import logging
import re
from pathlib import Path
from collections.abc import Callable, Awaitable

from app.config import settings

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    pass


async def download_audio(
    video_id: str,
    output_dir: Path | None = None,
    audio_format: str = "mp3",
    quality: str = "320",
    filename: str | None = None,
    progress_callback: Callable[[float], Awaitable[None]] | None = None,
) -> Path:
    if output_dir is None:
        output_dir = settings.download_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / (filename or "%(title)s"))
    if not output_template.endswith(f".{audio_format}"):
        output_template += f".{audio_format}"

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-x",
        "--audio-format", audio_format,
    ]

    if audio_format == "mp3":
        cmd.extend(["--audio-quality", f"{quality}k" if quality.isdigit() else "0"])
    elif audio_format == "flac":
        cmd.extend(["--audio-quality", "0"])
    elif audio_format == "m4a":
        cmd.extend(["--audio-quality", f"{quality}k" if quality.isdigit() else "0"])

    cmd.extend([
        "-o", output_template,
        "--progress-template", "%(progress._percent_str)s",
        "--newline",
        url,
    ])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    last_percent = 0.0
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode().strip()
        match = re.search(r"([\d.]+)%", text)
        if match and progress_callback:
            percent = float(match.group(1))
            if percent - last_percent >= 1.0:
                last_percent = percent
                await progress_callback(percent)

    await process.wait()

    if process.returncode != 0:
        stderr = await process.stderr.read()
        raise DownloadError(f"yt-dlp failed (code {process.returncode}): {stderr.decode()[:500]}")

    expected_path = Path(output_template)
    if expected_path.exists():
        return expected_path

    for f in output_dir.iterdir():
        if f.suffix == f".{audio_format}" and f.stem in output_template:
            return f

    files = sorted(output_dir.glob(f"*.{audio_format}"), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        return files[0]

    raise DownloadError(f"Download completed but output file not found in {output_dir}")
