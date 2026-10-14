---
title: "21 · 信号、进程组与文件锁：退出以后谁释放资源？"
description: "从 Slime 的 checkpoint 所有权和 GPU 命令包装器，理解文件锁、信号和进程组清理。"
weight: 210
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 问题：持有文件锁的进程被杀死，后来者还能启动吗？

第 18 讲区分了“结果已到达”和“进程已退出”。现在沿 Slime 的另一个失败场景继续：一个控制器独占 checkpoint 目录；控制器突然退出后，新控制器应该能接管，而同时存活的两个控制器不能一起写。

阅读顺序是：**取得锁 → 报告就绪 → 检查竞争者 → 终止持有者 → 再次取得锁**。然后进入 CI 包装器：收到终止信号时，怎样把退出责任传给自己启动的命令。

本讲示例适用于 Linux/macOS 等 POSIX 系统，使用 `fcntl`、Unix 信号和管道上的 `select`；Windows 不能原样运行。实验只锁临时目录文件，只操作本程序创建的进程或进程组。

<span id="lock-readiness"></span>
## 1. 锁保护的是目录所有权，就绪消息确认锁已取得

`fcntl.LOCK_EX` 请求独占锁；与 `fcntl.LOCK_NB` 按位或表示立即尝试，失败就抛异常，不在这里一直等。源码把锁竞争转换成“另一个训练任务已经拥有目录”的错误，然后停止启动。需要共享锁时标准库还提供 `fcntl.LOCK_SH`，本场景为了独占写入选择 `LOCK_EX`。文件本身存在不等于锁仍被持有；检查文件名是否存在不能代替加锁。


实验的子进程取得相同种类的锁，输出 `ready` 和自己的 PID/父 PID，再等标准输入。父进程不能先睡固定秒数就假设它已经拿到锁，而是等待 stdout 变得可读：

```python
if not select.select([process.stdout], [], [], 5)[0]:
    raise TimeoutError("lock holder did not become readable")
fields = process.stdout.readline().split()
```

`select.select(rlist, wlist, xlist, timeout)` 返回三个列表，这里只关心第一个“可读列表”。超时返回空列表；可读可能是数据，也可能是 EOF，因此还要检查读到的内容。它不等价于“拿到完整一行”，一般协议仍需处理部分数据；本例的孩子一次输出短行并立即 flush，而且此前没有其他 stdout 数据。[select 的返回合同](https://docs.python.org/3.12/library/select.html#select.select)


<span id="lock-release"></span>
## 2. 不依赖被杀进程运行 finally

运行 [example.py](example.py)：

```bash
python3 -W error example.py
```

```text
ready True
lock blocked True
child killed True
lock reacquired True
```

父进程打开同一个临时文件，尝试 `LOCK_EX | LOCK_NB`，确认竞争失败。然后向自己创建的孩子发送 `SIGKILL`，`wait()` 收回退出状态，再对同一个文件句柄重新加锁成功，最后 `fcntl.flock(lock, fcntl.LOCK_UN)` 主动解锁。文件保持存在，锁的所有权却已经变化。[flock 与锁操作](https://docs.python.org/3.12/library/fcntl.html#fcntl.flock)

这是对真实测试的**教学裁剪**：用一个临时文件替换 checkpoint 目录与控制器，删去 Ray、数据队列和 pickle；保留先就绪、再竞争、再杀进程、最后重新加锁的顺序。`SIGKILL` 不能运行子进程的 Python `finally`。这里锁被释放，是持有它的文件描述符随进程结束关闭，而不是孩子“成功执行了清理”。若其他进程仍持有相关继承描述符，锁生命周期还要继续追踪。

这是协作式文件锁：所有写入者都要遵守加锁协议，它不会自动禁止绕过协议的普通文件写入。`LOCK_NB` 失败时应处理平台返回的锁竞争错误；例子同时检查 `EACCES` 和 `EAGAIN`。[文件锁平台说明](https://docs.python.org/3.12/library/fcntl.html)


<span id="process-identity"></span>
## 3. 先知道信号发给谁

`os.getpid()` 返回当前进程的 PID；`os.getppid()` 返回当前父进程的 PID。本例的就绪消息核对“孩子报告的 PID 等于 `Popen.pid`，孩子报告的父 PID 等于本进程 PID”，不把机器上的任意 PID 当成自己的孩子。


`os.kill(pid, sig)` 是给进程发指定信号，并不总意味着杀死；效果由信号和接收端处置决定。本讲改成让父进程杀自己刚创建的孩子，因此不会终止你的调用 shell。[os 的进程接口](https://docs.python.org/3.12/library/os.html#os.kill)


<span id="signal-handlers"></span>
## 4. 包装器收到信号，怎样安排自己的孩子退出

`signal.getsignal()` 读当前处理方式，`signal.signal()` 安装新处理器；离开包装器的 `finally` 用保存值恢复它们。Python 处理器运行在主解释器的主线程，也只能在该主线程安装。不能用它让某条工作线程替你执行回调。[信号与线程](https://docs.python.org/3.12/library/signal.html#signals-and-threads)


信号语义有平台边界。POSIX 的 `Popen` 返回码为负数时可表示由信号终止，不要把 Python 的负返回码直接当成 shell 状态码。[信号常量](https://docs.python.org/3.12/library/signal.html#module-contents)、[Popen.returncode](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen.returncode)

<span id="process-group"></span>
## 5. 直接孩子和一组进程是不同范围


`start_new_session=True` 在 POSIX 为孩子创建新会话；刚启动时它也是新进程组的组长，因此这里可用 `child.pid` 当组 ID。这个前提不能省略，更不能对调用 shell 的进程组照搬。进程组可以覆盖留在同组的后代；自行创建新会话或迁出组的后代不受这一组信号覆盖，`wait()` 也只等待该 `Popen` 直接管理的孩子。[新会话参数](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen)、[os.killpg](https://docs.python.org/3.12/library/os.html#os.killpg)

运行 [signals_example.py](signals_example.py)：

```text
alarm timeout
alarm handler restored True
group reaped True
handlers restored True
shell status 0
```

进程组部分保留原 `terminate_child(signum, _frame)` 名称与“直接孩子 → 组信号 → SIGKILL → wait”的顺序，等待缩短为 0.05 秒。孩子在输出 `ready` 前用 `signal.signal(signal.SIGTERM, signal.SIG_IGN)` 忽略 TERM，以稳定进入升级分支；`SIG_IGN` 是本实验补充的标准库处置常量，不是 Slime 固定快照中的用法。

实验直接调用处理器函数来模拟收到 TERM，**没有向父进程或 shell 发信号**，也没有创建孙进程。它证明信号升级和直接孩子回收，不声称覆盖复杂服务的所有后代。真实源码还捕获 `ProcessLookupError`，处理目标在发信号前已经退出的竞态。进程组部分若正常收到孩子退出，会提前返回；原函数还安排包装器自身退出，教学例子为了继续核对处理器恢复，改成普通返回。

<span id="signal-alarm"></span>
## 6. alarm 限制的是当前进程的一段同步工作


`signals_example.py` 保留类名、`handle_timeout` 和三个上下文方法，增加了旧处理器的保存与恢复。它在独立脚本的主线程中给睡眠设置 1 秒期限。源码的 `__exit__` 只取消闹钟，没有恢复旧处理器；这处教学补充不是原实现已经具备的行为。

一个进程只有一份 `alarm` 计时状态。本例前提是没有旧闹钟，也不嵌套使用；保存处理器不等于保存旧定时任务。长时间执行的某些 C 代码也可能延迟 Python 处理器运行，所以不能把它当成任何计算都会精确中断的硬截止。它既不会给单独的 asyncio Task 计时，也不能直接移进 `asyncio.to_thread` 的工作线程。[alarm](https://docs.python.org/3.12/library/signal.html#signal.alarm)、[Python 信号处理规则](https://docs.python.org/3.12/library/signal.html#execution-of-python-signal-handlers)

<span id="shell-boundary"></span>
## 7. os.system 是同步 shell 边界


这里保留这个用途是为了认出源码边界，不是照搬字符串拼接策略。若命令包含外部输入或需要可靠取得 stdout、stderr 和退出码，应回到第 18 讲的参数列表与 `subprocess` 合同；示例不会执行真实复制或修改源仓库。

<span id="cancellation-boundary"></span>
## 8. 把四种“停止”放回各自的责任范围

| 执行对象 | 停止怎样发生 | 仍要由谁收尾 |
| --- | --- | --- |
| asyncio Task | 取消请求在协作式暂停点传入 `CancelledError` | await 任务，让它运行清理；取消不自动停止外部进程 |
| Python 线程 | 通过约定的标志或队列协作退出，没有通用的安全强杀接口 | 线程自己结束工作，所有者 `join`；Task 的取消不强杀线程 |
| 直接子进程 | 发信号或调用 `terminate/kill` | 创建者读完必要输出、`wait/join` 并释放句柄 |
| POSIX 进程组 | 给确定属于本次任务的组发信号 | 跟踪直接孩子和资源；组信号不证明所有后代都在该组 |

文件锁和 Python `finally` 也分别判断：被 `SIGKILL` 的孩子不会执行 Python 清理，但其文件描述符会由系统关闭；父进程自己持有的锁仍要等父进程释放。回到本讲起点，新控制器是否能接管，必须用真实加锁结果来确认。

<details><summary>复述与小实验</summary>

先解释为什么 `ready` 不能仅靠固定睡眠替代。再把实验中的 `SIGKILL` 改成父进程向孩子 stdin 写一个字节并 flush，调用 `communicate()` 等它正常退出，检查能否再次取得文件锁。两条路径的共同结果与不同清理机制分别是什么？

最后复述：取消正在等待外部命令的 Task，为什么不等于该命令已经退出？哪个对象记录命令 PID，谁保留它并执行最后一次等待？

</details>

<details><summary>展开本节完整可运行实验</summary>

```python
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
```

</details>

{{< python-async-slime >}}

Slime 的 `RolloutQueueController` 打开 `rollout/session.lock`，在写 checkpoint 分支之前调用：

```python
fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
```

<details><summary>源码入口：控制器先锁定 checkpoint 目录再发布分支</summary>

{{< source-reference id="source-1" >}}

</details>

Slime 的 checkpoint 回归测试也先 `select`，再检查 `b"ready\n"`，才尝试创建第二个控制器。这份测试证明的是该控制器锁的失败与释放路径，不是实际训练性能。

<details><summary>源码入口：等待 ready、验证排他、杀进程后重新取得所有权</summary>

{{< source-reference id="source-2" >}}

</details>

Slime 的 GPU 包装器也把锁的生命周期绑定到打开的文件，命令结束后在父进程 `finally` 里关闭句柄。完整退出必须同时处理孩子和父进程持有的资源。

<details><summary>源码入口：FdLock 的打开、非阻塞加锁和关闭</summary>

{{< source-reference id="source-8" >}}

</details>

Slime 启动模型服务时，把父 PID 作为 `_launch_server` 的参数传下去；孩子安装外部库提供的父进程死亡监测后，再比较 `os.getppid()` 和传入 PID，避免在父进程已经变化的情况下继续启动模型服务。不能把这个比较本身说成持续监测器：持续行为由导入的 SGLang 函数承担。

<details><summary>源码入口：_launch_server 检查父进程身份</summary>

{{< source-reference id="source-5" >}}

</details>

Slime 故障注入测试的 `os.kill(os.getpid(), signal.SIGKILL)` 刻意让当前测试角色立即退出。

<details><summary>源码入口：恢复测试故意模拟进程突然死亡</summary>

{{< source-reference id="source-6" >}}

</details>

CI 的 `gpu_lock_exec._run_command` 用 `subprocess.Popen(..., start_new_session=True)` 启动命令，记录旧处理器，再对 `SIGINT`、`SIGTERM`、`SIGHUP` 安装 `terminate_child`。它不是在创建一个新 Task；这是操作系统通知与 Python 主线程之间的入口。

```python
previous_handlers[signum] = signal.getsignal(signum)
signal.signal(signum, terminate_child)
```

<details><summary>源码入口：保存处理器、转发终止、恢复处理器</summary>

{{< source-reference id="source-3" >}}

</details>

这些常量在源码中的职责是：

| 信号 | 此处的使用语境 |
| --- | --- |
| `signal.SIGINT` | 终端中断，包装器为它安排清理 |
| `signal.SIGTERM` | 请求进程终止，可被处理；先给孩子一次有期限的退出机会 |
| `signal.SIGHUP` | 挂断通知，包装器同样转入清理 |
| `signal.SIGKILL` | 最后强制停止，不能捕获或忽略 |
| `signal.SIGALRM` | 下一节中给当前进程设置的定时通知 |

源码用 `128 - returncode` 转换成 shell 惯例；

源码先 `child.terminate()` 并有期限地 `wait()`。孩子仍不退出时，再用 `os.killpg(child.pid, signum)` 作用于该新会话中的进程组，超时升级为 `os.killpg(child.pid, signal.SIGKILL)`，最后等待直接孩子。

`math_dapo_utils.timeout` 在进入时安装 `SIGALRM` 处理器并调用 `signal.alarm(seconds)`；到期时处理器抛 `TimeoutError`；离开时 `signal.alarm(0)` 撤销尚未触发的闹钟。

<details><summary>源码入口：数学答案处理使用的同步超时上下文</summary>

{{< source-reference id="source-4" >}}

</details>

权重转换脚本里的 `os.system("cp -rf ...")` 用 shell 命令复制配置等文件。这是同步等待 shell，不是创建可 `await` 的工作。POSIX 返回编码后的等待状态；不能一概与 `Popen.returncode` 混用。实验只执行固定的 `os.system("exit 0")`，因此打印 `shell status 0`。[os.system](https://docs.python.org/3.12/library/os.html#os.system)

<details><summary>源码入口：转换工具把若干文件复制交给 shell</summary>

{{< source-reference id="source-7" >}}

</details>

{{< python-async-coverage lesson="19-signals-locks" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../18-process-lifecycle/) · [下一节：22 · asyncio Streams：接收、分帧与连接收尾](../20-async-streams/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
