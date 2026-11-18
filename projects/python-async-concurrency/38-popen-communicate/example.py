import subprocess
import sys
from pathlib import Path


def main():
    worker = Path(__file__).with_name("worker.py")  # 沿用第 37 课的子程序。
    print("before Popen")
    proc = subprocess.Popen(  # 启动子进程，返回控制对象；不在这里等它完成全部工作。
        [sys.executable, str(worker), "3"],
        stdout=subprocess.PIPE,  # 用管道接住子进程的标准输出，稍后读取。
        stderr=subprocess.PIPE,  # 标准错误使用另一条管道，稍后一起读取。
        text=True,  # communicate 返回的输出采用字符串形式。
    )
    print("parent can continue")  # 父进程已经拿回执行权；不据此判断子进程是否结束。
    print("before communicate")
    stdout, stderr = proc.communicate()  # 读取两条输出管道并等子进程退出；当前线程在此等待。
    print("after communicate")  # 本例的输出已收齐，子进程已退出。
    print("returncode", proc.returncode)  # communicate 已更新退出码；本例 0 表示成功。
    print("stdout", stdout.strip())  # 子进程打印的文字，不是它内部的列表对象。
    print("stderr", repr(stderr))  # 本例没有错误输出，所以是空字符串 ''。


if __name__ == "__main__":
    main()
