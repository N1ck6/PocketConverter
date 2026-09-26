"""
Cross-process job queue so a multi-file selection becomes one batch.

Explorer starts one converter.exe per selected file. Each process drops its
job into QUEUE_DIR and then tries to take WORKER_LOCK; the one that gets it
converts everything in the queue, the others exit immediately.

Why no job is ever lost: a process only gives up after its lock attempt
failed, which means the worker still held the lock *after* the job file was
written. The worker re-checks the queue after releasing the lock, so it sees
that file (or hands over to whoever grabs the lock next).
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import List, Tuple

from converter_app.utils import DATA_DIR

QUEUE_DIR = DATA_DIR / 'queue'
LOCK_PATH = DATA_DIR / 'worker.lock'
STALE_SECONDS = 600  # jobs left behind by a crashed worker are dropped, not run days later


def submit(path, mode: str) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{time.time_ns()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    tmp = QUEUE_DIR / f"{name}.tmp"
    tmp.write_text(json.dumps({'path': str(path), 'mode': mode, 'time': time.time()}), encoding='utf-8')
    os.replace(tmp, QUEUE_DIR / f"{name}.job")  # atomic: the worker never sees half a job


def take_all() -> List[Tuple[str, str]]:
    jobs = []
    for f in sorted(QUEUE_DIR.glob('*.job')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            f.unlink()
        except (OSError, ValueError):
            f.unlink(missing_ok=True)
            continue
        if time.time() - data.get('time', 0) < STALE_SECONDS:
            jobs.append((data['path'], data['mode']))
    return jobs


def has_jobs() -> bool:
    return QUEUE_DIR.exists() and any(QUEUE_DIR.glob('*.job'))


class WorkerLock:
    """Non-blocking inter-process lock; the OS releases it if the process dies."""

    def __init__(self, path: Path = None):
        self.path = path or LOCK_PATH
        self._fh = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, 'a+')
        try:
            fh.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self._fh = fh
        return True

    def release(self) -> None:
        if not self._fh:
            return
        try:
            self._fh.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            self._fh.close()
            self._fh = None
