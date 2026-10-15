---
title: "21.5 · finally：使用区报错后怎样关闭"
description: "第 21 单元拆分学习的第 5 步：finally：使用区报错后怎样关闭。"
weight: 215
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [21.4](../21-async-contextmanager/)已经走通正常退出：先关闭资源，再执行块外代码。[第 09 课](../09-task-cancellation/#cancel-cleanup-responsibility)还说明，`finally` 负责清理，本身不会捕获并消除异常。
>
> **本课新增的问题：** 使用沙箱时抛出异常，外层收到异常以前，资源是否已经关闭？

## 1. finally：已经进入沙箱以后，使用代码报错了

本节只改变使用区：**打印 inside 后抛出 ValueError。** 然后沿着异常经过的位置，观察关闭和外层异常处理的先后顺序。

本例的 boot_agent_sandbox 与 21.4 相同；完整下载保留该函数，新增变化在 exercise。字典仍然只是沙箱状态的教学替身。

## 2. ValueError / finally：先运行一次异常退出

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def boot_agent_sandbox(image, instance_id):
    print("boot", image, instance_id)
    await asyncio.sleep(0)
    sb = {"open": True}
    try:
        yield sb
    finally:
        print("closing", instance_id)
        await asyncio.sleep(0)
        sb["open"] = False
        print("closed", instance_id)


async def exercise():
    try:
        async with boot_agent_sandbox("demo-image", "case-error") as sandbox:
            print("inside", sandbox["open"])
            raise ValueError("work failed")
    except ValueError as error:
        print("error", error)
    print("outside", sandbox["open"])


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
boot demo-image case-error
inside True
closing case-error
closed case-error
error work failed
outside False
```

## 3. finally：沿错误经过的位置读

从上往下看执行顺序，`L` 对应上方代码行号；等待和交接位置已标在图中。

<div class="async-context-lanes" id="async-context-error-swimlanes">

```text
# L = example.py 行号；从上往下读，每行只在一列执行。
# CALLER 与 RESOURCE 属于同一个 Task。
# WAIT(loop) = 等下一轮调度；YIELD(sb) = 交出资源。
# +------+------------------------------+------------------------------------+----------------------------+
# | STEP | CALLER (exercise)            | RESOURCE (boot_agent_sandbox)      | OUTPUT                     |
# +------+------------------------------+------------------------------------+----------------------------+
# | T01  | L20-21 ENTER -> T02          |                                    |                            |
# | T02  |                              | L7 print; L8 WAIT(loop)            | boot demo-image case-error |
# | T03  |                              | L8 RESUME; L9-10 prepare           |                            |
# | T04  |                              | L11 YIELD(sb) -> T05               |                            |
# | T05  | L21 as sandbox; L22 print    |                                    | inside True                |
# | T06  | L23 raise; L21 EXIT -> T07   |                                    |                            |
# | T07  |                              | L11 ValueError; L13 print          | closing case-error         |
# | T08  |                              | L14 WAIT(loop)                     |                            |
# | T09  |                              | L14 RESUME; L15-16 close           | closed case-error          |
# | T10  | L24 except; L25 print        |                                    | error work failed          |
# | T11  | L26 print                    |                                    | outside False              |
# +------+------------------------------+------------------------------------+----------------------------+
# T04-T07: 生成器停在 L11；使用区报错后，ValueError 被送回这里。
# T08: 清理停在 L14 等待；调用方还不能进入 L24 的 except。
# T09-T10: 先关闭资源，再让外层 except 处理原来的 ValueError。
```

</div>

[下载注释泳道图 execution-flow.py](execution-flow.py)。

关键证据是：**closed 在 error 前面。** finally 处理资源清理；外层 except 决定怎样处理业务错误。

本例讨论的是已经成功进入的资源。准备阶段尚未交出资源时就失败，使用区不会开始；若准备中途创建了部分资源，应在准备代码中安排相应清理，真实源码见 21.4 文末。

## 4. finally：本节只带走两件事

1. 使用区报错会触发退出；包住 yield 的 finally 提供清理机会。
2. 这份管理器先完成关闭，再让调用方收到原来的 ValueError。

自查：如果删除 exercise 外面的 except，沙箱关闭完成后还会收到 ValueError 吗？

<details><summary>查看解释</summary>

会。管理器执行清理没有把错误变成成功；没有外层 except 时，异常继续向外传播。

</details>

下一节只把使用区的 ValueError 换成任务取消，观察谁等待关闭结束。

---

[上一节：21.4 · asynccontextmanager：把准备和关闭接到 async with](../21-async-contextmanager/) · [下一节：21.6 · Task.cancel：使用区被取消后怎样关闭](../21-context-cancellation/) · [返回学习路线](../learning-route/)
