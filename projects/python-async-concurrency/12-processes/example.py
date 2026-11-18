import multiprocessing
import subprocess
import sys

def conversion_worker(value):
    return value * value

if __name__ == "__main__":
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(2) as pool:
        print("pool", pool.starmap(conversion_worker, [(2,), (3,)]))
    result = subprocess.run(
        [sys.executable, "-c", "print('child')"],
        check=True, capture_output=True, text=True,
    )
    print("subprocess", result.stdout.strip())
