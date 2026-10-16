---
title: "37 · subprocess.run：运行并等待外部命令"
description: "分清启动外部进程、等待退出和取得输出；run 返回时工作已经结束。"
weight: 370
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 27 课](../27-thread-lifecycle/)用 Thread 启动工作，再用 join 等线程结束。本课继续区分“启动工作”和“等工作结束”，但执行对象换成外部程序。
>
> **本节新增的需求：** 运行另一个程序，等它退出后，拿到它打印的内容和退出状态。
>
> **本节的解决方式：** 调用 `subprocess.run(...)`，把启动、收集输出和等待退出放在同一次调用里；正常返回时拿到 CompletedProcess 完成记录。

## 1. subprocess.run：执行的是外部程序

### 1.1. 进程 / Thread / Task：先看它们各自在哪里

<span id="process-thread-coroutine-map"></span>

先把前面几课放到同一张位置关系图里，再看本课。图中的分支表示“在哪里运行”，本课的具体执行先后见第 3 节的泳道图。

```text
进程 A（自己的内存空间）
│
├─ 主线程：一条执行路线
│  │
│  └─ 事件循环（前面的 asyncio 例子）
│     ├─ Task A → 驱动协程 A
│     └─ Task B → 驱动协程 B
│
└─ 工作线程：另一条执行路线
   └─ 执行普通函数 get_samples()

   主线程与工作线程可共享进程 A 的对象。

进程 B（另一个内存空间）
│
└─ 主线程：执行这个进程里的代码

   进程 B 不会自动共享进程 A 的普通变量。
```

1. **进程是程序的一次运行实例。** 同一份 Python 程序也可以启动成多个进程；不同进程有各自的内存空间，不要求它们运行不同的代码。
2. **线程是进程内的一条执行路线。** 一个进程可以有主线程和多个工作线程，它们各自有执行位置，可以访问同一进程内的共同对象。工作线程并不需要事件循环，也不只负责简单工作。
3. **协程可以暂停和恢复。** 在前面的 asyncio 例子中，事件循环运行在主线程里，通过 Task 驱动协程；一个协程等待未完成的操作时，循环可以推进其他就绪任务。Task A 和 Task B 共用这里的线程。

因此，“线程”不意味着“自带事件循环”。图中的循环是前面使用 asyncio 时运行在该线程里的；本课两个脚本都直接运行同步代码。

### 1.2. Thread / await：分清阻塞线程与暂停协程

<div class="async-api-reference">

| 发生了什么 | 谁暂时不能继续 |
| --- | --- |
| 协程 await 一个未完成的异步操作 | 当前 Task 暂停；循环可以运行其他就绪任务 |
| 工作线程执行 time.sleep | 这个工作线程等待；事件循环线程仍可推进自己的工作 |
| 事件循环所在的线程执行阻塞调用 | 这个线程被占住；该循环上的其他任务也暂时无法得到调度 |

</div>

**阻塞是等待，不等于永久卡死。** 等待条件满足后，线程可以继续。单个线程在某一时刻执行一处代码，但协程可以暂停后轮换，多个线程也可以交错推进；不能把整个程序理解成一条固定的线性顺序。

这里复用的是[第 26 课的线程分工](../26-to-thread/#3-to_thread--await谁执行谁等待)和[第 33 课的协程交接](../33-await-handoff/)。若线程之间还依赖同一个锁或结果，一个线程的等待也可能间接让别的工作等待；共享内存不代表互不影响。

### 1.3. subprocess.run：本课启动的是另一个进程

之前 Thread 的 target 是当前程序里的一个函数。这里传给 run 的是**启动命令**：运行哪个程序、给它哪些参数。

本例仍然做 get_samples(3)，只是让另一个 Python 进程来执行它：

<div class="async-api-reference">

| 本例中的角色 | 做什么 |
| --- | --- |
| example.py：调用方，父进程 | 启动 worker.py，等待它退出，读取完成记录 |
| worker.py：子程序，在子进程中运行 | 计算样本列表，打印出来，然后退出 |

</div>

**子进程有自己的内存空间。** worker.py 中的列表不会因为函数 return 就直接成为父进程里的列表；本例通过打印文字来传回内容。

第 32 课暂未展开，这里只补它与本课相关的一点：**开始工作，不等于工作已经结束；还要有明确的等待结束位置。** 第 27 课的 join 放在启动之后；本例的 run 内部就包含了等待，不需要再补一行 join。线程池的取消与关闭继续留在[第 32 课](../32-threadpool-shutdown/)。

## 2. subprocess.run：启动、等待，再读取结果

把 [example.py](example.py) 和 [worker.py](worker.py) 下载到同一目录，运行 `python3 example.py`。这是一个只运行本地小程序的标准库实验。

### 2.1. example.py：调用方在 run 中等待

<div class="async-coordination-code">

```python
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
```

</div>

第 10 行的命令列表依次是：

1. sys.executable：当前 Python 解释器的路径，用它启动另一个 Python 进程。
2. str(worker)：要让这个解释器执行的脚本路径。
3. "3"：传给脚本的命令行参数，是字符串。

第 7 行只负责找到同目录的文件，方便从不同目录启动实验，不参与进程调度。

### 2.2. worker.py：子进程计算并打印

<div class="async-coordination-code">

```python
import sys


def get_samples(num_samples):
    return list(range(num_samples))


if __name__ == "__main__":
    num_samples = int(sys.argv[1])  # 接收调用方传来的字符串 "3"，转为整数。
    print(get_samples(num_samples))  # 把列表打印成文字，经标准输出交给调用方。
```

</div>

sys.argv[1] 就是命令列表中传来的 "3"。子进程调用自己的 get_samples，拿到列表后打印；运行到文件末尾，这个小程序就结束了。

实际运行 example.py 的输出：

```text
before run
after run
returncode 0
stdout [0, 1, 2]
stdout type str
```

这里的 `stdout [0, 1, 2]` 是父进程第 17 行打印的。子进程原先的 print 被 capture_output 捕获，因此没有直接出现在终端上。

## 3. subprocess.run：沿父进程与子进程的顺序看等待

下面的行号分别对应上面两个文件。父进程进入 run 后，先留在这次调用里，等子进程退出，才继续 after run。

本图两列各是一个进程中的主线程：父进程的线程等待时，子进程的线程仍能执行自己的代码。

```text
# 顺序  父进程的主线程：example.py        子进程的主线程：worker.py
# T01   L08：打印 before run
# T02   L09–14：调用 run，启动子进程
# T03                                     L09：取得参数 3
# T04                                     L10：计算列表，打印到标准输出
# T05                                     到达文件末尾，正常退出
# T06   L14：run 返回，赋值给 completed
# T07   L15：打印 after run
# T08   L16–18：读取退出码和捕获的文字
#
# T02 → T06：父进程在 run 内收集输出并等待；尚未执行 L15。
```

**这里没有协程之间的切换。** run 是同步调用：等待期间，调用它的线程不能继续执行自己的下一行；子进程则由操作系统安排运行。

## 4. CompletedProcess：拿到的是完成记录

<span id="subprocess-run"></span>

completed 是 run 正常返回的 CompletedProcess 对象，其中保存这次执行的结果。下面三个字段都从 completed 读取：

<div class="async-api-reference">

| 本例读取的内容 | 含义 |
| --- | --- |
| returncode | 子进程的退出码，本例为 0，表示正常成功退出 |
| stdout | 捕获的标准输出，本例是字符串 "[0, 1, 2]\n" |
| stderr | 捕获的标准错误，本例为空字符串 |

</div>

它与前面线程池返回的 Future 不同：**拿到 completed 时，这次子进程运行已经结束；直接读取字段即可，不需要 await 或 result()。**

列表只存在于子进程的 get_samples 中。父进程拿到的是它打印出来的文字，所以最后一行类型为 str；本课不额外引入文字与 Python 对象之间的转换。

### 4.1. capture_output / text / check：三个参数各管一件事

1. **capture_output=True：保存输出。** 同时捕获标准输出和标准错误，正常返回后分别从 stdout、stderr 读取。
2. **text=True：用字符串接收。** 否则捕获内容默认是 bytes。
3. **check=True：检查退出状态。** 退出码非零时，run 抛出 subprocess.CalledProcessError，后面的 after run 不会沿正常路径执行；未开启检查时，非零退出码也会保存在返回记录中。

check 不会让外部程序自动成功，也不会把子程序中的异常原样抛给父进程；父进程根据退出状态得知失败。具体的失败处理与超时收尾后续再展开。

## 5. subprocess.run：同步等待会占住调用线程

“另起了进程”不等于“调用方会自动异步等待”。如果直接在协程里调用 run，调用它的事件循环线程仍会被阻塞，其他协程也不能靠这段等待继续运行。

需要让事件循环继续调度时，可以回接[第 26 课的 asyncio.to_thread](../26-to-thread/)：把这个同步调用交给工作线程。这个组合没有出现在本课主例子中；先把 run 本身的等待行为看清楚。

## 6. subprocess.run：带走三条结论

1. run 接收启动命令，让外部程序在子进程中运行。
2. run 是同步接口，正常返回时子进程已退出，拿到的是完成记录。
3. 捕获的 stdout 是输出内容；本例通过 text=True 得到文字，不会直接收到子进程中的 Python 列表。

自查：after run 能出现在本例子进程退出之前吗？completed.stdout 看起来像列表，能否因此把它当作列表直接使用？

<details><summary>查看解释</summary>

不能。after run 要等 run 正常返回才执行。stdout 是 "[0, 1, 2]\n" 这段字符串；外观像列表，不代表它就是列表对象。

</details>

下一节的新增问题：如果希望**启动后先继续做别的事，再决定何时等待和收集输出**，就需要把这几个动作分开。这是第 38 课 Popen / communicate 的内容。

{{< python-async-slime title="按需阅读：源码用法与版本边界" >}}

主例子是独立标准库实验，并非 Slime 函数的裁剪。下面是 Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中 exec_command 对 run 的实际使用。

{{< source-reference id="source-1" >}}

源码启动的是 bash 命令，并按 capture_output 决定是否使用字符串捕获。本课改用一个本地 Python 脚本来观察同样的“启动、等待、读取输出”关系，不执行这里的项目命令，也不展开异常处理包装。

{{< python-async-coverage lesson="37-subprocess-run" >}}

依据：[Python 3.12：subprocess.run](https://docs.python.org/3.12/library/subprocess.html#subprocess.run)、[CompletedProcess](https://docs.python.org/3.12/library/subprocess.html#subprocess.CompletedProcess)。主例子在 Python 3.12.3 运行，适用本教程 Python 3.11 及以上版本。

位置关系与等待行为参见：[线程](https://docs.python.org/3.12/library/threading.html)、[进程间的数据交换](https://docs.python.org/3.12/library/multiprocessing.html#exchanging-objects-between-processes)、[事件循环与多线程](https://docs.python.org/3.12/library/asyncio-dev.html#concurrency-and-multithreading)。

{{< /python-async-slime >}}

---

[上一已读课：25 · inspect](../25-inspect-awaitable/) · [下一节：38 · Popen / communicate](../38-popen-communicate/) · [重点续学路线](../learning-route/#priority-reading)
