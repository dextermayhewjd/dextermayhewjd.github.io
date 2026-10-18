---
title: "35.2 · loop.create_future / Future.set_result / set_exception：复习结果交付与源码用法"
description: "复用第 20 单元的结果交付，理解源码中 set_result(None) 的放行作用。"
weight: 352
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> [20.3](../20-future-result/)讲过创建与保存结果，[20.4](../20-await-future/)已经让等待者和提供者分别执行，[20.5](../20-future-state/)补上失败交付。
>
> **本节是复习与源码应用：** 用短例子唤回同一对象的状态变化，再看源码为什么用 `set_result(None)` 放行等待者。创建、等待与完成仍沿用第 20 单元的规则。

## 1. create_future / set_result：用短例子复习同一个对象

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 33.1：取出当前事件循环。
    future = loop.create_future()  # 创建尚未完成的 Future，此时没有结果。
    print("created", future.done())  # False：还没有写入结果。
    future.set_result(7)  # 写入结果 7，同时把这个 Future 标记为完成。
    print("completed", future.done())  # True：现在已经完成。
    print("result", future.result())  # 读取已经写入的 7。
    print("await", await future)  # 已经完成，直接得到 7；这次不会挂起。


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
created False
completed True
result 7
await 7
```

`set_result(7)` 完成刚创建的 Future，后面的读取取得同一个 7。这次在 `await` 前已有结果，所以不会挂起。需要回顾“先等、另一处再写”的完整交接，见 [20.4](../20-await-future/)。

<span id="future-completion"></span>

## 2. set_result(None)：结果也可以只表达一次放行

第 20 单元的例子交付样本列表；源码也可能交付 `None`。`None` 仍是正常结果，表示这次等待已经完成。等待者恢复后继续运行，不必从 Future 取得业务数据。

1. 等待方创建 Future，保存它，并 `await future`。
2. 提供方取得同一个 Future，调用 `set_result(None)` 完成这次交付。
3. 循环随后恢复等待方，`await future` 返回 None。

`set_result` 不会直接执行等待者。若源码要周期性放行多批等待，每次独立交付需要独立的 Future，不能反复改写已完成的对象。

失败交付仍使用 `set_exception(error)`：它保存异常，后续 `await` / `result()` 才抛出。成功、失败或取消后再次完成同一 Future 都会报 `InvalidStateError`；这些边界见 [20.5](../20-future-state/)。

自查：把 `set_result(None)` 中的 None 换成 Task，是否会自动执行那个 Task？不会，这一参数是保存的结果值；Task 的执行由其自身调度管理。

{{< python-async-slime title="按需阅读：源码对照与适用范围" >}}

主例子是第 20 单元机制的顺序复习，不是 Slime 业务函数的裁剪版。Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 则把创建、等待与写入放在不同位置：

{{< source-reference id="source-1" >}}

对照 20.4 的交接，认出 wait 中创建、保存和等待 Future 的位置；批次队列与定时调度按源码主线继续展开。

{{< source-reference id="source-2" >}}

_release 取出之前保存的同一个 Future，确认尚未完成，再用 set_result(None) 完成它。这里的结果是 None，表示等待者可以继续；没有把 Task 填进 Future。

{{< python-async-coverage lesson="35-future-completion" >}}

依据：[Python 3.12：创建 Future](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.create_future)、[写入结果与异常](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future.set_result)。主例子在 Python 3.12.3 下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}


---

[上一节：35.1 · 复习结果读取](../35-future-results/) · [下一节：35.3 · 完成回调](../35-task-callbacks/) · [基础实验：20.4 · 等待交付](../20-await-future/)
