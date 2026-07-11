
from __future__ import annotations

import threading
from collections import deque

from core.downloader import Downloader
from core.history import HistoryStore
from core.models import DownloadJob, JobStatus


class DownloadQueue:
    def __init__(
        self,
        downloader: Downloader,
        history: HistoryStore,
        workers: int = 1,
    ) -> None:
        self.downloader = downloader
        self.history = history
        self.workers = max(1, workers)
        self._jobs: dict[str, DownloadJob] = {}
        self._pending: deque[str] = deque()
        self._lock = threading.Lock()
        self._active = 0
        self._cv = threading.Condition(self._lock)

        for _ in range(self.workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()

    def list_jobs(self) -> list[dict]:
        with self._lock:
            jobs = list(self._jobs.values())
        order = {
            JobStatus.RUNNING: 0,
            JobStatus.QUEUED: 1,
            JobStatus.ERROR: 2,
            JobStatus.CANCELLED: 3,
            JobStatus.DONE: 4,
        }
        jobs.sort(key=lambda j: (order.get(j.status, 9), j.title))
        return [j.to_dict() for j in jobs]

    def add(self, job: DownloadJob) -> dict:
        with self._cv:
            self._jobs[job.id] = job
            self._pending.append(job.id)
            self._cv.notify()
        return job.to_dict()

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.status == JobStatus.QUEUED:
                job.status = JobStatus.CANCELLED
                job.error = "İptal edildi"
                try:
                    self._pending.remove(job_id)
                except ValueError:
                    pass
                return True
            if job.status == JobStatus.RUNNING:
                self.downloader.request_cancel(job_id)
                return True
        return False

    def clear_finished(self) -> None:
        with self._lock:
            remove = [
                jid
                for jid, j in self._jobs.items()
                if j.status in (JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED)
            ]
            for jid in remove:
                self._jobs.pop(jid, None)

    def _worker(self) -> None:
        while True:
            job: DownloadJob | None = None
            with self._cv:
                while not self._pending:
                    self._cv.wait()
                job_id = self._pending.popleft()
                job = self._jobs.get(job_id)
                if not job or job.status == JobStatus.CANCELLED:
                    continue
                self._active += 1

            assert job is not None
            self.downloader.download(job, on_progress=None)
            if job.status in (JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED):
                self.history.add(job.to_dict())

            with self._cv:
                self._active -= 1
