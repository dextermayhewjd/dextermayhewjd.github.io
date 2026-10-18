---
title: "38 · subprocess.Popen / communicate：启动命令并收集管道输出"
description: "先启动子进程并取得控制对象，之后再读取输出和等待退出。"
weight: 380
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 37 课的 subprocess.run](../37-subprocess-run/)启动 worker.py，在一次调用里收集输出并等待退出；返回时，拿到的是 CompletedProcess 完成记录。
>
> **本节新增的需求：** 启动同一个子程序后，父进程希望先继续做自己的事情，稍后再集中读取输出、等待退出。
>
> **本节的解决方式：** 先用 Popen 启动并取得进程控制对象 proc；在需要收尾的位置调用 proc.communicate()。

## 1. Popen / communicate：把启动与等待放在两处

第 37 课的子程序保持不变，只调整父进程怎样调用它。沿父进程的执行顺序看：

```text
第 37 课：run
调用 run
  ↓
启动、收集输出、等待退出
  ↓
返回完成记录

第 38 课：Popen / communicate
调用 Popen → 启动并返回 proc
  ↓
父进程继续执行自己的代码
  ↓
调用 communicate
  ↓
收集输出、等待退出
  ↓
返回 stdout、stderr
```

这里仍然是两个进程，各有自己的内存。与[进程、线程和协程的关系图](../37-subprocess-run/#process-thread-coroutine-map)一致，本例父、子进程分别执行同步代码；调用方代码仍在原来的线程中继续。

先分清接下来三个名字：

<div class="async-api-reference">

| 名字 | 在本例中是什么 |
| --- | --- |
| proc | 父进程里的 Popen 对象，用来操作已经启动的那份子进程 |
| worker.py | 在子进程中执行的程序，负责调用 get_samples 并打印结果 |
| stdout、stderr | communicate 返回的两份输出内容，本例都是字符串 |

</div>

**Popen 返回的是控制对象，不能因为拿到了 proc，就认定子进程已经完成。** 子进程也可能执行得很快，在父进程调用 communicate 之前就结束；两种情况都可以使用同一个 communicate 收尾。

## 2. Popen：启动后，父进程可以继续向下执行

把 [example.py](example.py) 和 [worker.py](worker.py) 放在同一目录，运行 `python3 example.py`。worker.py 与第 37 课相同。

### 2.1. example.py：先启动，再决定何时收集

<div class="async-coordination-code">

```python
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
```

</div>

与上一课相比，启动命令 `[sys.executable, str(worker), "3"]` 不变。原本的 capture_output=True 换成两行明确的输出设置：

1. **stdout=subprocess.PIPE：** 建立接收标准输出的管道，接住子程序 print 的内容。
2. **stderr=subprocess.PIPE：** 建立另一条管道接收标准错误。
3. **text=True：** 沿用字符串模式，让输出采用 str 而非 bytes；它仍不会变成 Python 列表。

PIPE 是指定输出去向的常量。它不会创建新的 Python 线程，也不会主动把结果取回来；后面的 communicate 负责读取。

### 2.2. worker.py：仍然只负责计算、打印和退出

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

实际运行 example.py 的输出：

```text
before Popen
parent can continue
before communicate
after communicate
returncode 0
stdout [0, 1, 2]
stderr ''
```

这些行由父进程依次打印，顺序是确定的。它们说明父进程可以在 Popen 之后、communicate 之前执行代码；**不能用这些输出断言那一刻子进程一定还在运行。** 子进程自己的 print 被管道接住，到父进程第 20 行才显示到终端。

## 3. Popen / communicate：沿两条泳道看交接

下面是一种允许发生的交错：父进程已经进入 communicate，子进程才开始处理参数。实际运行时，子进程也可能更早完成；父进程会先执行第 15–16 行，然后才调用第 17 行，这一点不变。

```text
# 顺序  父进程主线程：example.py          子进程主线程：worker.py
# T01   L08：打印 before Popen
# T02   L09–14：启动子进程，拿到 proc
# T03   L15：打印 parent can continue
# T04   L16：打印 before communicate
# T05   L17：调用 communicate，读取并等待
# T06                                     L09：取得参数 3
# T07                                     L10：计算列表并写入输出管道
# T08                                     到达文件末尾，退出
# T09   L17：返回 stdout、stderr
# T10   L18–21：打印收尾后的结果
#
# T05 → T09：父进程的线程在 communicate 内等待；子进程仍可推进。
```

**communicate 不会重新启动 worker.py。** 它操作的是 proc 对应的同一份子进程。正常返回时，本例的管道输出已读取完，子进程也已退出，proc.returncode 已更新。

如果子进程在 T05 之前就完成了，第 17 行会收集已有的输出并确认退出；这不改变程序写法，也不保证本次等待一定耗时很长。

## 4. communicate：返回输出，同时完成退出等待

<span id="popen-communicate"></span>

`stdout, stderr = proc.communicate()` 返回一个二元组，本例将其中两项分别赋给 stdout 和 stderr。它们是输出内容，不是 Future，也不需要 await。

<div class="async-api-reference">

| 操作或字段 | 此时表示什么 |
| --- | --- |
| Popen(...) 返回 proc | 启动成功后，父进程取得控制对象 |
| proc.communicate() 返回 | 输出已读完，并已等到子进程退出 |
| stdout、stderr | 本次取得的两份字符串；没有错误输出时 stderr 为 "" |
| proc.returncode | communicate 更新的退出码，本例为 0 |

</div>

与上一课 `run(check=True)` 不同，communicate 不会仅因为退出码非零就自动抛出 CalledProcessError；需要根据 returncode 判断子程序是否成功。本课先看成功路径，超时和终止后的收尾留在第 39 课。

### 4.1. PIPE / communicate：为什么不能只等退出，不读输出？

管道能暂存的内容有限。如果子进程输出很多，写满后会等待父进程读取；此时父进程如果只等子进程退出，双方就可能互相等待。

communicate 会处理两条输出管道的读取，并等待退出，所以本课让它负责这次收尾。不要在这份例子里把它简单换成“只等退出”的操作。

本例只输出一小段文字。communicate 会把收集的输出放进内存；持续或非常大量的日志输出，需要另外设计读取方式。

## 5. Popen / communicate：分开调用，不等于变成异步接口

父进程可以选择何时调用 communicate，但一旦进入它，调用线程仍会同步等待，直到输出读取和退出等待完成。把它直接写在协程里，也会占住事件循环线程。

**这一课改变的是“什么时候开始等”，不是“等待时自动让其他协程运行”。** 需要把同步阻塞调用交给线程时，再回接[第 26 课的 to_thread](../26-to-thread/)。

如果只想一次运行并取回结果，继续使用第 37 课的 run 即可；需要在启动和收尾之间安排自己的代码时，再使用这一课的拆分方式。

## 6. Popen / communicate：带走三条结论

1. Popen 负责启动并交回控制对象，父进程可以先继续执行自己的代码。
2. communicate 负责读取输出并等待退出；正常返回后，再读取 returncode。
3. 启动与等待分开，不代表等待变成异步；communicate 仍会阻塞调用它的线程。

自查：把 communicate 放到很后面，是否意味着子进程也要等到那里才开始？如果在调用 communicate 前子进程已经结束，还能读取它的管道输出吗？

<details><summary>查看解释</summary>

子进程在 Popen 启动成功后就可以运行，不等 communicate 才开始。对于本例的小段输出，即使子进程先结束，communicate 仍可以读取尚在管道中的内容并完成收尾。

</details>

{{< python-async-slime title="按需阅读：源码用法与版本边界" >}}

主例子是独立标准库实验。以下是 Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中示例目录的 SubprocessInterpreter.run_file，不是核心包调用次数的新增统计。

{{< source-reference id="source-1" >}}

源码同样先创建 Popen 对象、设置两条管道，再调用 communicate。它还传入运行环境和超时，本课只复用“启动、读取和等待”这一条关系；超时之后如何终止并收尾留到第 39 课。

{{< python-async-coverage lesson="38-popen-communicate" >}}

依据：[Python 3.12：Popen](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen)、[communicate](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen.communicate)。主例子在 Python 3.12.3 运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[上一节：37 · subprocess.run](../37-subprocess-run/) · [下一规划：39 · Popen.wait / terminate / kill](../learning-route/#curriculum-stage-processes) · [当前续学路线](../learning-route/#priority-reading)

[当前短补：call_later 教学](../loop-call-later/) · [函数对比目录](../comparisons/)
