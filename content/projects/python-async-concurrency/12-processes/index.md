---
title: "12 · 进程池、子进程与系统边界"
description: "从 spawn 和 Pool.starmap 出发，区分进程、线程与 asyncio。"
weight: 120
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="process-intro"></span>

## 进程与线程的关键区别

线程共享进程内的 Python 对象；独立进程有自己的地址空间。进程之间交换工作和结果，需要相应的传输机制，不能把一个普通全局列表当作天然共享列表。

实验沿用转换脚本的 `conversion_worker` 名称，把模型转换替换成平方计算，只观察 `spawn`、`Pool` 和 `starmap`。

```python
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
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
pool [4, 9]
subprocess child
```

`starmap` 把每一项参数元组展开传给 worker，并收集结果。入口保护让 spawn 启动的子解释器导入模块时，不会再次无限创建进程池。worker 放在模块顶层，也便于新进程按名称找到它。

## Slime 里的对应职责

转换工具把权重分片交给进程池；部署代码用 `multiprocessing.Process` 启动路由或模型服务；`subprocess` 启动已有外部程序。它们都创建进程，但调用合同不同。

<details>
<summary>展开 Slime 源码：模型转换进程池</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：_start_router</summary>

{{< source-reference id="source-2" >}}

</details>

| 机制 | 执行什么 | 结果怎样回来 |
| --- | --- | --- |
| `Pool.starmap` | Python worker 函数 | 进程池收集 Python 返回值 |
| `Process(target=...)` | 一个指定的 Python 入口 | 需要另行安排 Queue、Pipe、文件或其他通信 |
| `subprocess.run/Popen` | 外部命令 | 返回码、stdout、stderr 等 |

## 超时与退出不能混用

`Popen.communicate(timeout=...)` 超时不会自动替你杀死子进程；后续要明确终止、等待和收集输出。信号与进程组操作属于系统边界，也不能当作 asyncio Task.cancel 的同义词。

Slime 的 `signal.alarm` 超时和 `fcntl.flock` 文件锁是其他配套机制，平台适用范围需要单独核对。完整位置在用法索引中。

<details><summary>复述检查</summary>

`await` 不会把任务变成独立进程。进程池有自己的启动、通信和回收成本；同步的 `starmap` 等待也不能直接放进事件循环里就称为非阻塞。

</details>

语义核对：[multiprocessing](https://docs.python.org/3.12/library/multiprocessing.html)、[subprocess](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen.communicate)。

{{< python-async-coverage lesson="12-processes" >}}

---

[专题首页](../) · [上一节](../11-contextvars/) · [下一节：13 · Future、回调与跨线程事件循环](../13-event-loop/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
