"""Teaching cut of Popen/communicate and checked commands; no external programs."""

import subprocess
import sys


if __name__ == "__main__":
    with subprocess.Popen(
        [sys.executable, "-u", "-c", "import sys; print('out'); print('err', file=sys.stderr)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as proc:
        stdout, stderr = proc.communicate(timeout=5)
        print("merged", stdout.splitlines())
        assert stderr is None and proc.returncode == 0

    with subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=0.05)
        except subprocess.TimeoutExpired:
            print("timeout still running", proc.poll() is None)
            proc.kill()
            stdout, stderr = proc.communicate()
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()
        print("killed and reaped", proc.returncode is not None)

    with subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) as child:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        print("terminated and waited", child.poll() is not None)

    try:
        subprocess.run([sys.executable, "-c", "raise SystemExit(7)"], check=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        print("command failed", error.returncode)
    status = subprocess.check_call(
        [sys.executable, "-c", "pass"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print("check_call", status)
    output = subprocess.check_output([sys.executable, "-c", "print('probe')"], text=True)
    print("check_output", output.strip())
