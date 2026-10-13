"""POSIX only: bounded alarm and signal escalation for our own process group."""

import os
import sys

if os.name != "posix":
    raise SystemExit("This example requires POSIX signals and process groups.")

import select
import signal
import subprocess
import time


class timeout:
    def __init__(self, seconds=1, error_message="Timeout"):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        self.previous_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, value, traceback):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.previous_handler)


if __name__ == "__main__":
    previous_alarm = signal.getsignal(signal.SIGALRM)
    try:
        with timeout(seconds=1):
            time.sleep(60)
    except TimeoutError:
        print("alarm timeout")
    print("alarm handler restored", signal.getsignal(signal.SIGALRM) == previous_alarm)

    child_code = "\n".join([
        "import signal, sys, time",
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
        "print('ready', flush=True)",
        "while True: time.sleep(1)",
    ])
    with subprocess.Popen(
        [sys.executable, "-u", "-c", child_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    ) as child:
        previous_handlers = {}

        def terminate_child(signum, _frame):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=0.05)
                    return
                except subprocess.TimeoutExpired:
                    pass
                try:
                    os.killpg(child.pid, signum)
                    child.wait(timeout=0.05)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()

        try:
            if not select.select([child.stdout], [], [], 5)[0] or child.stdout.readline() != b"ready\n":
                raise TimeoutError("child did not become ready")
            for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
                previous_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, terminate_child)
            # Call the handler directly: no signal is sent to the invoking shell.
            terminate_child(signal.SIGTERM, None)
            print("group reaped", child.returncode == -signal.SIGKILL)
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate()
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)
        print("handlers restored", all(signal.getsignal(signum) == handler for signum, handler in previous_handlers.items()))

    print("shell status", os.system("exit 0"))
