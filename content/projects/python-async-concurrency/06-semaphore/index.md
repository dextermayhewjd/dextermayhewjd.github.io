---
title: "06 · Semaphore：限制同时进入的工作数量"
description: "把并发许可与任务总量区分开。"
weight: 60
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="semaphore-permits"></span>

## 已经会创建任务，为什么还需要限流

创建 100 个 Task，不代表下游服务就适合同时处理 100 个请求。`Semaphore(n)` 给一段工作 n 个许可，进入前获取，离开时归还。

```python
import asyncio

async def generate(rollout_id, semaphore, state):
    async with semaphore:
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        try:
            await asyncio.sleep(0)
            return rollout_id
        finally:
            state["active"] -= 1

async def exercise():
    semaphore = asyncio.Semaphore(2)
    state = {"active": 0, "peak": 0}
    results = await asyncio.gather(*(generate(i, semaphore, state) for i in range(5)))
    print("results", results)
    print("peak", state["peak"])

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
results [0, 1, 2, 3, 4]
peak 2
```

这段独立实验把生成逻辑替换为一次异步等待；`peak` 记录许可区域里的最大任务数。`async with semaphore` 让进入和离开配对，异常退出也会执行释放。

从方法层面看，进入时相当于 `await semaphore.acquire()`，退出时执行 `semaphore.release()`。`acquire()` 在没有许可时让当前任务等待；`release()` 归还许可，使等待者有机会继续。`async with` 自动把成功进入与退出配对，避免异常路径漏掉释放。它不是创建或启动任务的接口。

## 在 Slime 中找到许可的作用范围

`GenerateState` 创建信号量；`generate_and_rm` 在调用生成器的区域使用它。不要只读创建时的数字：许可从哪一行开始持有、在哪一行释放，才决定限制了什么工作。

<details>
<summary>展开 Slime 源码：GenerateState.__init__</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：generate_and_rm</summary>

{{< source-reference id="source-2" >}}

</details>

`generation_pacer` 是另一种安排启动节奏的工具。它不等同于信号量，也不能单独保证在途请求数不超上限，第 13 节再解释。

## 两个常见误解

- 限制许可数，不会阻止调用方提前创建很多正在等待的 Task；任务对象本身仍会占用内存。
- 许可只约束 `async with` 内的区域。区域外的评分或结果处理，不会自动被同一个上限限制。

<details><summary>复述检查</summary>

把许可从 2 改成 1，实验的 `peak` 变成 1；任务总数依然是 5。许可数与工作总数是两回事。

</details>

语义核对：[Semaphore](https://docs.python.org/3.12/library/asyncio-sync.html#semaphore)。

{{< python-async-coverage lesson="06-semaphore" >}}

---

[专题首页](../) · [上一节](../05-cancellation/) · [下一节：07 · Queue：把生产速度和消费速度接起来](../07-queues/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
