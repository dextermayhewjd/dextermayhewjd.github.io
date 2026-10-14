---
title: "10.2 · return_exceptions=True：收齐结果与异常"
description: "有任务失败时仍等完整组，把返回值和异常对象按传入顺序放进结果列表。"
weight: 101
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. gather：这次希望一份失败，也收齐每份情况

[10.1](../15-gather-failures/)已经看清：默认 gather 先报告任务 11 的错误，任务 10 继续运行，随后由调用方单独等完。

现在增加一个要求：**两份工作彼此独立，希望一次等到它们都结束，再分别知道成功了什么、失败了什么。** 逐个等待并处理异常也能做到；这一节让 gather 负责一次收齐。

本课用一句话理解：**`return_exceptions=True` 让 gather 把普通任务异常也作为列表元素收集，等整组结束后一起返回。**

<span id="gather-return-exceptions"></span>

## 2. return_exceptions=True：改变收集方式，任务本身不变

仍然使用 10.1 的 `generate`：任务 10 正常返回，任务 11 抛出 `ValueError`。收集时增加这个参数：

```python
results = await asyncio.gather(task_10, task_11, return_exceptions=True)
```

下面是完整实验。其中最后的循环只负责把列表里的成功值与异常分别打印出来。

```python
import asyncio


async def generate(rollout_id, fail=False):
    print("start", rollout_id)
    try:
        if fail:
            raise ValueError(f"generation {rollout_id} failed")
        await asyncio.sleep(0.1)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def main():
    task_10 = asyncio.create_task(generate(10))
    task_11 = asyncio.create_task(generate(11, fail=True))
    results = await asyncio.gather(task_10, task_11, return_exceptions=True)
    print("results", results)
    for result in results:
        if isinstance(result, BaseException):
            print("error", type(result).__name__, result)
        else:
            print("result", result)


if __name__ == "__main__":
    asyncio.run(main())
```

[下载 example.py](example.py) · 运行：`python3 example.py`。本机 CPython 3.12.3 默认调度下的实际输出：

```text
start 10
start 11
cleanup 11
finished 10
cleanup 10
results [10, ValueError('generation 11 failed')]
result 10
error ValueError generation 11 failed
```

## 3. gather 的结果列表：成功值和异常各放在哪里？

沿着这次收集看三步：

1. **任务 11 失败：** gather 记下它的异常，继续等待任务 10。
2. **任务 10 也结束：** gather 现在可以返回完整列表，`results` 取得这个列表。
3. **调用方检查列表：** 成功值和异常都在里面，逐项判断并处理。

| 位置 | 对应哪个参数 | 保存什么 |
| --- | --- | --- |
| `results[0]` | 第一个参数 `task_10` | 正常返回值 `10` |
| `results[1]` | 第二个参数 `task_11` | `ValueError` 异常对象 |

**列表仍按传入顺序排列，和谁先结束没有关系。** 任务 11 虽然先失败，异常仍在第二个位置。

### 3.1 isinstance：拿到异常对象以后，还要检查它

例子用 `isinstance(result, BaseException)` 判断一个元素是不是异常对象，用 `type(result).__name__` 显示它的类型名。`BaseException` 也能识别子任务取消时收集到的 `CancelledError`。

打印列表里的 `ValueError('...')` 只是在显示对象，不会再次抛出异常。**它仍然表示任务失败，不能因为 gather 返回了列表，就把每一项都当成成功结果。**

这里讨论普通子任务错误；如果外层取消传到仍在等待的 gather，它仍会取消未结束的子任务。`return_exceptions=True` 不会阻止这次外层取消；如何有选择地隔开传播会在后面的取消传播单元学习。

## 4. return_exceptions：和上一节只差哪一件事？

| 收集方式 | 任务 11 失败以后 |
| --- | --- |
| 默认 `return_exceptions=False` | 这次等待先抛出异常，拿不到完整结果列表；任务 10 不因此取消 |
| `return_exceptions=True` | 继续等任务 10，最后返回包含成功值和异常的列表 |

改变的是**错误怎样交给调用方**。它没有重新启动任务，也没有让任务 11 变成成功。

## 5. return_exceptions=True：带走三条结论

1. **一份任务出现普通异常，也可以继续收齐整组情况。** 使用 `return_exceptions=True`。
2. **返回列表中既可能有正常值，也可能有异常对象。** 位置仍与传入参数对应。
3. **收集异常以后，还要判断和处理失败。** 收齐结果不等于所有工作都成功。

自查：任务 11 先失败，为什么异常放在列表第二项？看到 gather 正常返回列表，能否认定两份任务都成功？

下一节新增的问题是：如果这些任务必须共同结束，一份失败就应该取消其他任务，怎样由 TaskGroup 统一收尾？见[11.1 · TaskGroup 的失败处理](../11-taskgroup-failures/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## abort_servers_until_idle：收齐之后，再检查失败

主例子是独立标准库实验。下面是 Slime 固定快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的原代码。

这里上层交来一组服务地址，函数等待每个服务完成自己的排空检查，再判断能否正常返回。本节只看整组结果与失败处理。

{{< source-reference id="source-1" >}}

1. `return_exceptions=True` 收齐每个服务的成功或失败情况。
2. 结果与 `urls` 按传入顺序对应，随后检查哪些结果是异常对象。
3. 发现失败就抛出 `RuntimeError`。收集异常是为了拿齐信息，随后仍向上报告失败。

<section id="source-usage-locations">

## 本节对应的源码位置

[server_control.py:237–254](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/sglang_utils/server_control.py#L237-L254)：`abort_servers_until_idle` 收集异常后检查并报告失败。

</section>

语义核对：[Python 3.12 asyncio.gather](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)。全部调用位置仍见[第 06 单元的源码索引](../05-gather/#source-usage-locations)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：10.1 · asyncio.gather：收集报错，任务仍可继续](../15-gather-failures/) · [下一节：11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾](../11-taskgroup-failures/) · [完整学习路线](../learning-route/)
