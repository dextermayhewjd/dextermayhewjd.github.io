import subprocess
import sys
from pathlib import Path


def main():
    worker = Path(__file__).with_name("worker.py")  # 定位与本文件放在一起的子程序。
    print("before run")
    completed = subprocess.run(  # 启动子进程；当前线程在此收集输出并等待它退出。
        [sys.executable, str(worker), "3"],  # Python 解释器、脚本路径、传给脚本的参数。
        capture_output=True,  # 将子进程的标准输出和标准错误保存下来。
        text=True,  # 保存为字符串，便于读取。
        check=True,  # 子进程退出码非零时，在这里抛出 CalledProcessError。
    )
    print("after run")  # run 已正常返回：本例子进程已经退出。
    print("returncode", completed.returncode)  # 0：子进程报告成功退出。
    print("stdout", completed.stdout.strip())  # 读取捕获的文字；strip 去掉末尾换行。
    print("stdout type", type(completed.stdout).__name__)  # str：得到的是文字，不是列表。


if __name__ == "__main__":
    main()
