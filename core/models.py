
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class FormatOption:
    format_id: str
    label: str
    ext: str
    height: int | None = None
    filesize: int | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VideoInfo:
    id: str
    title: str
    url: str
    thumbnail: str
    duration: int | None
    uploader: str
    formats: list[FormatOption] = field(default_factory=list)
    webpage_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "duration": self.duration,
            "uploader": self.uploader,
            "webpage_url": self.webpage_url,
            "formats": [f.to_dict() for f in self.formats],
        }


@dataclass
class DownloadJob:
    id: str
    url: str
    title: str
    format_id: str
    format_label: str
    output_dir: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    filepath: str = ""
    error: str = ""
    thumbnail: str = ""

    @staticmethod
    def create(
        url: str,
        title: str,
        format_id: str,
        format_label: str,
        output_dir: str,
        thumbnail: str = "",
    ) -> "DownloadJob":
        return DownloadJob(
            id=str(uuid4()),
            url=url,
            title=title,
            format_id=format_id,
            format_label=format_label,
            output_dir=output_dir,
            thumbnail=thumbnail,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "format_id": self.format_id,
            "format_label": self.format_label,
            "output_dir": self.output_dir,
            "status": self.status.value,
            "progress": self.progress,
            "speed": self.speed,
            "eta": self.eta,
            "filepath": self.filepath,
            "error": self.error,
            "thumbnail": self.thumbnail,
        }
