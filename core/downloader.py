
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

from yt_dlp import YoutubeDL

from core.models import DownloadJob, JobStatus
from core.utils import sanitize_filename

ProgressCb = Callable[[DownloadJob], None]


class Downloader:
    def __init__(self) -> None:
        self._cancel_flags: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def request_cancel(self, job_id: str) -> None:
        with self._lock:
            flag = self._cancel_flags.get(job_id)
            if flag:
                flag.set()

    def download(self, job: DownloadJob, on_progress: ProgressCb | None = None) -> DownloadJob:
        cancel = threading.Event()
        with self._lock:
            self._cancel_flags[job.id] = cancel

        out_dir = Path(job.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = sanitize_filename(job.title)
        outtmpl = str(out_dir / f"{safe}.%(ext)s")

        def hook(d: dict[str, Any]) -> None:
            if cancel.is_set():
                raise Exception("cancelled")
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                if total:
                    job.progress = round(downloaded / total * 100, 2)
                speed = d.get("speed")
                eta = d.get("eta")
                job.speed = _fmt_speed(speed)
                job.eta = _fmt_eta(eta)
                if on_progress:
                    on_progress(job)
            elif status == "finished":
                job.progress = 100.0
                job.speed = ""
                job.eta = ""
                if on_progress:
                    on_progress(job)

        opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "format": job.format_id or "bv*+ba/b",
            "merge_output_format": "mp4",
            "noprogress": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook],
            "retries": 5,
            "fragment_retries": 5,
        }

        job.status = JobStatus.RUNNING
        if on_progress:
            on_progress(job)

        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(job.url, download=True)
                if cancel.is_set():
                    job.status = JobStatus.CANCELLED
                    job.error = "İptal edildi"
                else:
                    path = ydl.prepare_filename(info) if info else ""
                    # merge may change ext to mp4
                    candidate = Path(path)
                    if not candidate.exists():
                        mp4 = candidate.with_suffix(".mp4")
                        if mp4.exists():
                            candidate = mp4
                    job.filepath = str(candidate) if candidate.exists() else path
                    job.status = JobStatus.DONE
                    job.progress = 100.0
        except Exception as e:
            msg = str(e)
            if cancel.is_set() or "cancelled" in msg.lower():
                job.status = JobStatus.CANCELLED
                job.error = "İptal edildi"
            else:
                job.status = JobStatus.ERROR
                job.error = msg
        finally:
            with self._lock:
                self._cancel_flags.pop(job.id, None)
            if on_progress:
                on_progress(job)

        return job


def _fmt_speed(speed: float | None) -> str:
    if not speed:
        return ""
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    v = float(speed)
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    return f"{v:.1f} {units[i]}"


def _fmt_eta(eta: int | None) -> str:
    if eta is None:
        return ""
    m, s = divmod(int(eta), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
