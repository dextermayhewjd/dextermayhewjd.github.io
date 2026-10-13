"""POSIX only: kill our own lock holder, wait, and acquire the same lock."""

import errno
import os
import sys

if os.name != "posix":
    raise SystemExit("This example requires POSIX signals, flock, and pipe select.")

import fcntl
from pathlib import Path
import select
import signal
import subprocess
import tempfile


if __name__ == "__main__" and len(sys.argv) > 1:
    with open(sys.argv[1], "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("ready", os.getpid(), os.getppid(), flush=True)
        sys.stdin.buffer.read(1)
elif __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "session.lock"
        with subprocess.Popen(
            [sys.executable, "-u", __file__, str(path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        ) as process:
            try:
                if not select.select([process.stdout], [], [], 5)[0]:
                    raise TimeoutError("lock holder did not become readable")
                fields = process.stdout.readline().split()
                ready = fields == [b"ready", str(process.pid).encode(), str(os.getpid()).encode()]
                if not ready:
                    raise RuntimeError("lock holder did not report the expected identity")
                print("ready", ready)
                with path.open("a") as lock:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except OSError as error:
                        if error.errno not in (errno.EACCES, errno.EAGAIN):
                            raise
                        print("lock blocked", True)
                    else:
                        raise AssertionError("the child should own the lock")
                    os.kill(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
                    print("child killed", process.returncode == -signal.SIGKILL)
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    print("lock reacquired", True)
                    fcntl.flock(lock, fcntl.LOCK_UN)
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate()
