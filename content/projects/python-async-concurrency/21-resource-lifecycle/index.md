---
title: "21.1 · try/finally：分清准备、使用和关闭"
description: "第 21 单元拆分学习的第 1 步：try/finally：分清准备、使用和关闭。"
weight: 211
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 09 课的清理责任](../09-task-cancellation/#cancel-cleanup-responsibility)说明，退出已经进入的 `try` 时，会执行 `finally` 中的清理代码。这里继续把关闭资源的代码放在 `finally` 中。
>
> **本课新增的问题：** 一次资源使用包含准备、使用和关闭三个阶段。这三段代码分别应该放在哪里，哪一段可以换成调用方自己的工作？

## 1. try/finally：先把一次沙箱使用分成三个阶段

本节先观察正常完成的一次资源使用：**准备好沙箱，使用它，使用结束后关闭它。** 沿用已经学过的 `await`、字典和 `try/finally`，先把这三件事的位置分清。

真实 Slime 沙箱需要启动服务与安装工具。这里沿用同一套教学替身：`sleep(0)` 代表异步等待，字典的 `open` 代表沙箱是否打开；不会启动真实沙箱。

## 2. try/finally：运行同一份最小例子

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    image, instance_id = "demo-image", "case-1"
    print("boot", image, instance_id)
    await asyncio.sleep(0)
    sandbox = {"open": True}
    try:
        print("inside", sandbox["open"])
        await asyncio.sleep(0)
    finally:
        print("closing", instance_id)
        await asyncio.sleep(0)
        sandbox["open"] = False
        print("closed", instance_id)
    print("outside", sandbox["open"])


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
boot demo-image case-1
inside True
closing case-1
closed case-1
outside False
```

## 3. try/finally：哪一段可以由使用者自由替换？

| 阶段 | 本例做什么 | 执行后是什么状态 |
| --- | --- | --- |
| 准备 | 打印 boot、等待，再创建 sandbox | `open` 为 True |
| 使用 | try 内打印 inside、等待；这里可以改成自己的工作 | 使用的是已经打开的 sandbox |
| 关闭 | finally 内打印 closing、等待，再把 open 改为 False | 打印 closed，随后才到 outside |

`outside False` 说明：变量仍能指向同一个字典，但它记录的资源状态已经关闭。关闭资源与删除变量是两件事。

这份代码已经能完成一次资源使用。若许多地方都需要沙箱，使用区各不相同，准备和关闭却需要重复安排。我们后面希望把这两段规则放到同一个入口中，调用方只提供自己的使用代码。

## 4. try/finally：本节只带走两件事

1. **准备、使用、关闭是三个阶段。** 使用必须在准备完成以后开始，关闭完成后才执行本例的 outside。
2. **使用代码与资源管理规则可以分开考虑。** 改变沙箱内要做的工作，不必改变沙箱怎样准备和关闭。

自查：如果把 inside 后面的工作换成自己的代码，哪两段仍然需要保留？

<details><summary>查看解释</summary>

保留准备与关闭；try 内的使用代码可以换。这个观察是后面封装资源管理规则的动机。

</details>

下一节先补一个小零件：函数怎样交出一个值，并暂停在原来的位置。

---

[上一节：20.5 · Future 的状态与异常](../20-future-state/) · [下一节：21.2 · yield：交出一个值，并暂停在原处](../21-yield-pause/) · [返回学习路线](../learning-route/)
