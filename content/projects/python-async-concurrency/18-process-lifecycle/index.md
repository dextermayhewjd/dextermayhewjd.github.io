---
title: "20 · 进程生命周期：从队列工作到超时回收"
description: "沿 Slime 的生成器、服务进程和命令解释器，分清完成消息、进程退出与资源回收。"
weight: 200
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 问题：收到了结果，工作进程就已经退出了吗？

第 12 讲用 `Pool.starmap` 收集返回值。本讲把这一层拆开：一个生产者把题目送进队列，一个工作进程生成答案，父进程收集结果。最后还要确认两者退出。随后换成外部命令，观察超时以后谁负责清理。

阅读顺序是：**创建进程 → Queue 交接 → 完成消息 → 等待退出 → 超时升级清理**。这里不启动模型、Ray 或网络服务；实验只创建自己的短命子进程。

<span id="process-start"></span>
## 1. 先创建执行边界，再启动工作


教学程序使用同一种启动方式，但把模型服务换成生成固定答案的 `worker_process`：

```python
ctx = multiprocessing.get_context("spawn")
task_queue, done_queue = ctx.Queue(maxsize=4), ctx.Queue(maxsize=4)
process = ctx.Process(
    target=worker_process,
    args=(task_queue, done_queue, query_single_turn, get_rule_based_math_reward, None, {}),
)
process.start()
```

`Process(...)` 先建立进程对象；`start()` 才安排子进程执行 `target(*args)`。`spawn` 会启动新解释器，因而把入口放在 `if __name__ == "__main__":` 下，worker 放在模块顶层，传递可序列化的参数。子进程不会共享父进程里的普通列表。

这里 `multiprocessing.get_context("spawn")` 返回具有 `Process`、`Queue`、`Pool` 工厂的上下文，相关对象统一从它创建。库式代码通常更适合局部上下文。不要在任意导入位置反复设置全局启动方式，也不要混用不同上下文创建的同步对象。[Python 3.12 启动方式](https://docs.python.org/3.12/library/multiprocessing.html#contexts-and-start-methods)

创建者负责清理自己创建的进程。`multiprocessing.active_children()` 返回当前进程仍活着的 multiprocessing 子进程，不是全系统进程表。实验只检查已经握有的 worker 是否在其中，不遍历并杀掉其他任务的子进程。


<span id="process-queue"></span>
## 2. 从题目队列走到完成消息

输入交给 `task_queue.put(item)`，worker 用 `task_queue.get()` 取出。计算结束后，把含 `messages`、`reward`、`instance_id`、`extra_info` 的结果交给 `done_queue.put(output_item)`。这是真实生成器使用的字段和交接方向。

```python
def worker_process(task_queue, done_queue, rollout_func, reward_func, client, sampling_params):
    for item in iter(task_queue.get, "STOP"):
        messages, finish_reason = rollout_func(client, item["prompt"], sampling_params)
        item["messages"] = messages
        output_item = {
            "messages": messages,
            "reward": reward_func(item),
            "instance_id": item["instance_id"],
            "extra_info": {"finish_reason": finish_reason},
        }
        done_queue.put(output_item)
    done_queue.put("COMPLETE")
```

这是**教学裁剪**：保留原 `worker_process` 的签名、两条 Queue 和 `STOP/COMPLETE` 协议；只启动一个 worker，固定返回答案 `4`，删去 HTTP 调用、UUID、采样统计、JSON 字符串输入和结果上报。`extra_info` 只保留一个字段，真实实现放入更多题目与采样信息。生产者 `read_data_into_queue` 从原来的局部函数移到模块顶层，显式接收队列，以便用 `spawn` 导入；真实实现还读文件、打乱数据并重复投递。


每个 worker 需要自己的停止消息。一个 `STOP` 只能被一个消费者取走；父进程也要收齐 worker 数量的 `COMPLETE`，不能因为暂时没收到结果就判断整个生成任务完成。

`multiprocessing.Queue.empty()` 和 `qsize()` 只适合诊断，不能拿来决定“接下来 `get()` 一定不会阻塞”或“所有生产者已经结束”。`put()` 后还有后台线程把数据送进管道，观察值也会被其他进程立即改变；`qsize()` 在 macOS 等平台还可能不可用。实验用明确的结束消息，父进程用 `done_queue.get(timeout=10)` 给异常路径留出口，超时抛出标准库 `queue.Empty`。[Queue 的传输与限制](https://docs.python.org/3.12/library/multiprocessing.html#pipes-and-queues)

<span id="process-join"></span>
## 3. COMPLETE 以后，还要 join

运行 [example.py](example.py)：

```bash
python3 -W error example.py
```

Python 3.12 输出：

```text
owned worker True
results [(10, 1), (11, 1)]
joined True
join timed out True
process reaped True
pool [4, 9]
```

前半段先消费结果，再对生产者和 worker 分别 `join(timeout=5)`。收到 `COMPLETE` 是业务协议；`join` 等待的是操作系统进程结束。`join(timeout=...)` 的返回值不表示成功与否，要再看 `is_alive()` 和 `exitcode`。退出后的 `Process.close()` 释放进程对象的句柄，不能用它代替停止仍活着的进程。

后半段刻意创建一个睡眠 60 秒的进程，`join(timeout=0.01)` 返回时它仍活着，随后按照 Slime 路由器的顺序处理：

```python
if process.is_alive():
    process.terminate()
    process.join(timeout=5)
if process.is_alive():
    process.kill()
    process.join()
```

`terminate()` 在 POSIX 发送 `SIGTERM`，`kill()` 在 POSIX 使用 `SIGKILL`；Windows 的行为不同，不能把它们都理解成可执行 Python 清理逻辑的通知。它们也不自动终止后代进程。源码把等待限制在剩余清理预算内；教学例子只处理自己的单个无后代睡眠进程，因此最后的 `join()` 不另设置预算。[Process 生命周期](https://docs.python.org/3.12/library/multiprocessing.html#multiprocessing.Process)


强制终止正在写 Queue 或持锁的进程，可能留下损坏的管道或让其他进程永久等锁。正常路径优先 `STOP`；异常路径停止本轮进程后，放弃本轮通信对象。实验最后对两条 Queue 调用 `close()`、`join_thread()`，释放本进程的队列资源并等待发送线程完成。不要在消费者还没取走大量结果时先 `join` 生产者，否则生产者可能卡在刷新队列，父进程又卡在等它退出。[进程与 Queue 的清理注意事项](https://docs.python.org/3.12/library/multiprocessing.html#programming-guidelines)

<span id="process-pool"></span>
## 4. Pool 替你分派任务，仍需要关闭边界

现在回到第 12 讲：`ctx.Pool(...)` 管理多个 worker，`pool.starmap(conversion_worker, ...)` 分派参数元组并等待返回值。本讲例子把生命周期显式写出：成功后 `pool.close()` 停止接收新任务；随后 `pool.join()` 等待 worker 退出；失败时改为 `pool.terminate()` 放弃尚未完成的工作，再 `join()`。


<span id="subprocess-communicate"></span>
## 5. 外部命令超时：异常发生了，进程还活着

`Process` 执行 Python callable；`subprocess.Popen` 启动命令并立即交回控制对象。超过期限会抛 `subprocess.TimeoutExpired`，但这一调用不会自动杀进程。

```python
try:
    stdout, stderr = proc.communicate(timeout=0.05)
except subprocess.TimeoutExpired:
    print("timeout still running", proc.poll() is None)
    proc.kill()
    stdout, stderr = proc.communicate()
```

第二次 `communicate()` 才完成输出读取、管道收尾和退出等待。不能只记一条“超时”日志就丢掉 `proc`。这是本例直接保留的源码顺序；命令替换成当前 Python 解释器的 `time.sleep(60)`，没有调用真实模型或工具服务。[communicate 超时合同](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen.communicate)


`proc.poll()` 不阻塞：仍运行返回 `None`，结束返回退出码。`proc.wait(timeout=...)` 等待退出但不读取输出。给 stdout/stderr 配了 `PIPE` 却一直只 `wait`，孩子可能写满管道后等父进程读取；父进程同时等孩子退出。本例因此对捕获输出的进程使用 `communicate`，对丢弃输出的进程才直接 `terminate()`、`wait()`，超时再 `kill()`、`wait()`。[Popen 等待与终止](https://docs.python.org/3.12/library/subprocess.html#popen-objects)


<span id="subprocess-output"></span>
## 6. 输出送到哪里，决定父进程怎样等待

运行 [subprocess_example.py](subprocess_example.py)，依次观察合并输出、超时回收、停止睡眠进程和检查命令结果：

```text
merged ['out', 'err']
timeout still running True
killed and reaped True
terminated and waited True
command failed 7
check_call 0
check_output probe
```

`subprocess.PIPE` 建立父子进程间的管道；`stderr=subprocess.STDOUT` 把错误输出合并进标准输出，此时 `communicate()` 返回的第二项为 `None`；`subprocess.DEVNULL` 丢弃相应输出。示例用 `-u` 消除子 Python 的输出缓冲影响，先写 `out` 再写 `err`。[subprocess 输出参数](https://docs.python.org/3.12/library/subprocess.html#frequently-used-arguments)


<span id="subprocess-failure"></span>
## 7. 命令失败和命令超时是两条分支


`TimeoutExpired` 表示等待期限耗尽；`CalledProcessError` 表示受检查的命令已经以非零状态结束。普通 `Popen` 收到非零退出码不会自动抛后者。`run(timeout=...)` 超时会先杀死并等待直接子进程，再重新抛出异常；`Popen.communicate(timeout=...)` 则把后续清理留给调用方，不能仅凭参数都叫 `timeout` 就套用同一段代码。[run 的超时合同](https://docs.python.org/3.12/library/subprocess.html#subprocess.run)

<details><summary>《流畅的 Python》核对：相似接口与不同执行边界</summary>

**书上怎么说**：`Process` 的基本用法与 `Thread` 相似。

**我的判断（本书未覆盖）**：本讲的 Slime 完成协议和失败清理顺序来自上述固定源码；Python 3.12 的具体方法合同以链接中的官方文档为准，不能从接口相似推导出共享内存或相同取消行为。

**依据**：第 19 章，`spinner-with-processes`。英文 `corpus/en/ch19.md:245–294`；中文 `corpus/zh/ch19.md:233–282`。书籍为第 2 版、基于 Python 3.10；示例验证环境为 Python 3.12.3。

原文：“Basic usage of the `Process` class is similar to `Thread`.”

对照：“❹ `Process` 类的基本用法与 `Thread` 相似。”

</details>

<details><summary>复述与小实验</summary>

先说明结果消息、进程退出、资源释放分别由哪个动作确认，再动手：把生产者的 `STOP` 暂时去掉，观察父进程怎样从带期限的 `get()` 进入清理；随后恢复。不要用 `empty()` 替代结束协议。

第二个问题：若一个服务进程又启动了其他进程，为什么对直接孩子调用一次 `kill()` 还不能证明服务已全部退出？下一讲沿这个问题进入进程组与信号。

</details>

<details><summary>展开本节完整可运行实验</summary>

```python
"""Teaching cut: STOP/COMPLETE protocol, then process and Pool cleanup."""

import multiprocessing
import time


def query_single_turn(client, messages, sampling_params):
    return messages + [{"role": "assistant", "content": "4"}], "stop"


def get_rule_based_math_reward(item):
    return int(item["messages"][-1]["content"] == item["label"])


def worker_process(task_queue, done_queue, rollout_func, reward_func, client, sampling_params):
    for item in iter(task_queue.get, "STOP"):
        messages, finish_reason = rollout_func(client, item["prompt"], sampling_params)
        item["messages"] = messages
        output_item = {
            "messages": messages,
            "reward": reward_func(item),
            "instance_id": item["instance_id"],
            "extra_info": {"finish_reason": finish_reason},
        }
        done_queue.put(output_item)
    done_queue.put("COMPLETE")


def read_data_into_queue(task_queue):
    for instance_id in (10, 11):
        task_queue.put({"instance_id": instance_id, "prompt": [], "label": "4"})
    task_queue.put("STOP")


def conversion_worker(value):
    return value * value


def main():
    ctx = multiprocessing.get_context("spawn")
    task_queue, done_queue = ctx.Queue(maxsize=4), ctx.Queue(maxsize=4)
    processes = []
    try:
        process = ctx.Process(
            target=worker_process,
            args=(task_queue, done_queue, query_single_turn, get_rule_based_math_reward, None, {}),
        )
        process.start()
        processes.append(process)
        print("owned worker", process.pid in {child.pid for child in multiprocessing.active_children()})

        producer = ctx.Process(target=read_data_into_queue, args=(task_queue,))
        producer.start()
        processes.append(producer)
        results = []
        while True:
            item = done_queue.get(timeout=10)
            if item == "COMPLETE":
                break
            results.append((item["instance_id"], item["reward"]))
        print("results", sorted(results))
        for process in processes:
            process.join(timeout=5)
            if process.is_alive() or process.exitcode != 0:
                raise RuntimeError("worker did not exit successfully")
        print("joined", all(not process.is_alive() for process in processes))
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()
        for queue in (task_queue, done_queue):
            queue.close()
            queue.join_thread()

    process = ctx.Process(target=time.sleep, args=(60,))
    process.start()
    try:
        process.join(timeout=0.01)
        print("join timed out", process.is_alive())
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()
        print("process reaped", not process.is_alive())
        process.close()

    pool = ctx.Pool(2)
    try:
        print("pool", pool.starmap(conversion_worker, [(2,), (3,)]))
        pool.close()
    except BaseException:
        pool.terminate()
        raise
    finally:
        pool.join()


if __name__ == "__main__":
    main()
```

</details>

{{< python-async-slime >}}

Slime 的 `launch_server_process` 为模型服务选择 `spawn`，创建 `multiprocessing.Process`，调用 `start()`，然后检查服务健康。在健康检查中，`is_alive()` 只能回答“进程是否还活着”，不能回答“HTTP 服务已经可用”。

<details><summary>源码入口：launch_server_process 的启动和健康检查交接</summary>

{{< source-reference id="source-1" >}}

</details>

源码用 `multiprocessing.set_start_method("spawn", force=True)` 改全局选择；

Slime 在启动前后取差集记录新路由器；

<details><summary>源码入口：ServingCluster 保存本轮启动的子进程</summary>

{{< source-reference id="source-2" >}}

</details>

<details><summary>源码入口：worker_process 接收题目、生成结果、发送 COMPLETE</summary>

{{< source-reference id="source-3" >}}

</details>

<details><summary>源码入口：BaseGenerator.run 创建 Queue、投递 STOP、启动进程并消费结果</summary>

{{< source-reference id="source-4" >}}

</details>

<details><summary>源码入口：ServingCluster.dispose 对路由器 terminate → join → kill → join</summary>

{{< source-reference id="source-5" >}}

</details>

真实转换工具使用 `with ctx.Pool(num_workers) as pool:`。要注意，Pool 的上下文退出调用 `terminate()`；不是所有上下文管理器都承诺等完未完成工作。此处 `starmap` 已经同步返回，结果才进入后续权重汇总。如果改成后台提交后立刻离开 `with`，就不能沿用“所有任务都做完了”的推断。[Pool 关闭合同](https://docs.python.org/3.12/library/multiprocessing.html#multiprocessing.pool.Pool)

<details><summary>源码入口：转换工具在 Pool 内收集结果，退出后汇总</summary>

{{< source-reference id="source-6" >}}

</details>

Slime 的 `SubprocessInterpreter.run_file` 用 `Popen` 跑文件，再用 `communicate(timeout=...)` 收集输出并等待退出。

<details><summary>源码入口：SubprocessInterpreter.run_file 的超时回收</summary>

{{< source-reference id="source-7" >}}

</details>

<details><summary>源码入口：GPU 命令包装器检查运行状态并等待退出</summary>

{{< source-reference id="source-8" >}}

</details>

Slime 的流式训练测试用 `STDOUT` 合并日志，边读 `proc.stdout` 边显示，再 `wait()`；启动训练前探测 `ray status` 则把输出丢到 `DEVNULL`，只检查状态码。两者都是同步代码，管道存在不表示正在使用 asyncio。

<details><summary>源码入口：合并训练日志，读完再 wait</summary>

{{< source-reference id="source-12" >}}

</details>

<details><summary>源码入口：只关心 ray status 的返回码</summary>

{{< source-reference id="source-13" >}}

</details>

Slime 的 `exec_command` 用 `subprocess.run(..., check=True)`，非零退出时收到 `subprocess.CalledProcessError`；异常携带 `returncode`，捕获了输出时还可检查 stdout/stderr。`check_call()` 同样在非零退出时抛异常，成功返回 `0`；`check_output()` 成功返回捕获的 stdout。这些接口已完成等待，返回值合同不同于立即返回控制对象的 `Popen`。[检查退出状态](https://docs.python.org/3.12/library/subprocess.html#subprocess.CalledProcessError)

<details><summary>源码入口：exec_command 保留命令失败的退出码与输出</summary>

{{< source-reference id="source-9" >}}

</details>

<details><summary>源码入口：check_call 检查命令是否存在</summary>

{{< source-reference id="source-10" >}}

</details>

<details><summary>源码入口：check_output 获取网卡查询结果</summary>

{{< source-reference id="source-11" >}}

</details>

{{< python-async-coverage lesson="18-process-lifecycle" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../17-executor-results/) · [下一节：21 · 信号、进程组与文件锁：退出以后谁释放资源？](../19-signals-locks/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
