---
title: "31.2 · ThreadPoolExecutor.map：批量提交并按输入顺序取结果"
description: "对一组输入调用同一个函数时，结果按输入顺序，还是按实际完成顺序交回来？"
weight: 312
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [31.1](../31-threadpool-submit/)已经会提交多份调用并取回结果；[第 29 课](../29-thread-event/)的 `set()`、`wait()` 让两份工作通过同一个通知配合。
>
> **本课新增的问题：** 对一组输入调用同一个函数时，结果按输入顺序，还是按实际完成顺序交回来？

## 1. map：输入一组值，取回一组结果

本课要完成的事：**对 10、11 调用同一个 `generate()`，再按输入顺序依次取回结果。**

31.1 的逐次 `submit()` 也能完成这件事；`map()` 帮我们组织同一个函数的一组调用，并给出按输入顺序取结果的入口。本课只增加这个批量关系。

`executor.map(generate, [10, 11])` 安排 `generate(10)` 和 `generate(11)`，返回一个结果迭代器，保存在 `results` 中。`results` 不是结果列表，也不是某一个 Future；普通 `for` 每次从它取得一个结果，必要时会阻塞等待。

## 2. map：先看到 11 的完成日志，再观察结果顺序

本例用已经学过的 Event，让调用 10 等到调用 11 打印日志后才能继续。`second_finished` 只表示“11 已打印完成日志”，不表示全部工作结束。线程数固定为 2，不靠调整 sleep 长短制造顺序。

主线程负责提交与取结果，工作线程负责执行 `generate()`；Event 只是为了在这个实验中控制日志先后。

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
from concurrent.futures import ThreadPoolExecutor
import threading


# 两份工作共用的通知：11 打印完成日志后，才允许 10 继续。
second_finished = threading.Event()


def generate(rollout_id):
    if rollout_id == 10:
        second_finished.wait()  # 执行 10 的工作线程在这里等通知。
    # 这是工作线程打印的日志；函数还要继续到下面的 return。
    print("finished", rollout_id)
    if rollout_id == 11:
        second_finished.set()  # 11 已打印，通知 10 可以继续。
    return rollout_id  # 交给 map 保存，随后由主线程取出。


def main():
    second_finished.clear()  # 每次运行实验前，先把通知复位为 False。
    # 本例需要两个工作线程，让 10 等待时，11 仍能执行。
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交 generate(10)、generate(11)，返回结果迭代器。
        results = executor.map(generate, [10, 11])
        # 主线程按输入顺序取结果：先取 10，再取 11；必要时等待。
        for result in results:
            print("received", result)


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
finished 11
finished 10
received 10
received 11
```

<span id="3-map完成顺序与交付顺序分别看"></span>

## 3. map：工作线程的日志与主线程的取值分别看

1. 两份调用先交给线程池。10 等 second_finished；11 打印 finished 并设置通知。
2. 10 收到通知后才打印 finished。完成日志的顺序因此是 11、10；日志位置在 return 前面。
3. for 首先索取输入 10 对应的结果，所以要等 10 完成；随后才交付 11 的结果。

两条顺序要分开：**工作线程打印日志是 11 → 10；主线程得到结果是 10 → 11。** 日志出现在函数返回之前，因此不把日志顺序当作两个函数的严格返回顺序。

**map 按输入顺序交付结果，工作本身仍可并发执行。** 取第一项时主线程等的是 10 对应的结果，不会因为 11 先有进展就自动改取 11。

本例的 Event 只用来验证先后。不要将线程数改成 1：10 占住唯一线程等 11，11 却没机会开始，会互相等待。

## 4. map：工作异常在取对应结果时出现

这是一个独立对照，[下载带注释的 failure.py](failure.py)。保持输入 10、11，只把 `generate(11)` 的行为改为抛出 ValueError：

```text
received 10
iteration raised failed 11
```

能取出 10，不代表后续都成功；for 索取 11 的结果时收到异常。不要只在调用 map 的那一行外处理错误，而漏掉后面的迭代过程。

脚本把 `try` 放在 `for` 外面，因为主线程执行到“取下一项结果”时才会收到这份工作保存的错误。工作线程抛错与主线程读取错误，是两个位置。

本课按 Python 3.12 验证，map 会收集输入并提交工作。不要把结果迭代器理解为“每取一项才提交一项”，也不能据此认为在途工作数量自动受限。

## 5. map：带走两条结论

1. 结果交付顺序跟输入顺序一致，不保证实际工作也按此顺序完成。
2. 错误可能在读取结果迭代器时出现，异常处理要覆盖消费过程。

自查：为什么看到 finished 11 后，不能立刻拿到 map 的第一项结果？

<details><summary>查看解释</summary>

第一项对应输入 10；即使 11 已完成，也要等 10 的结果先交付。

</details>

## 6. Executor.map：本课接口速查

<div class="async-api-reference">

| 调用或动作 | 用途与结果 |
| --- | --- |
| `executor.map(...)` | 对每项输入安排同一个函数，返回结果迭代器 |
| `for result in results` | 按输入顺序逐个取结果；取到未完成的一项时，当前线程等待 |

</div>

`map()` 不是每消费一项才提交一项；这里按 Python 3.12 的行为理解。`second_finished` 的通知方法复用第 29 课，它们只控制本例日志，不负责决定 map 的结果顺序。

<details><summary>按需阅读：项目对照与标准库依据</summary>

主例子是独立标准库实验。[旧版 submit 与 map 对照](../17-executor-results/#executor-submit-map)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/concurrent.futures.html#concurrent.futures.Executor.map)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[上一节：31.1 · ThreadPoolExecutor / submit](../31-threadpool-submit/) · [下一重点：33.1 · get_running_loop](../33-current-loop/) · [重点续学路线](../learning-route/#priority-reading)
