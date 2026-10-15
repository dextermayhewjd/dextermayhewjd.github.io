---
title: "21.2 · yield：交出一个值，并暂停在原处"
description: "第 21 单元拆分学习的第 2 步：yield：交出一个值，并暂停在原处。"
weight: 212
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [21.1](../21-resource-lifecycle/)已经把资源使用分成准备、使用和关闭三个阶段，使用代码可以替换，准备和关闭仍需保留。
>
> **本课新增的问题：** 如果准备代码先把资源交给外部使用，能否在交出值以后暂停，并保留后面代码的执行位置？

## 1. yield：交出值时，函数必须立刻结束吗？

为了以后把准备与关闭放到同一个函数里，先单独观察中间的交接：**函数交出一个值以后，外部先继续执行，函数保留暂停的位置。**

本节先用普通 `def` 观察这个动作。这里没有异步等待，也不创建沙箱。

## 2. yield / next：创建对象，再推进一次

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
def resource_steps():
    print("before yield")
    yield "sandbox"
    print("after yield")


def main():
    steps = resource_steps()
    print("generator created")
    value = next(steps)
    print("value", value)
    print("back in caller")


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
generator created
before yield
value sandbox
back in caller
```

## 3. yield：沿四条输出分清创建、推进与暂停

1. `steps = resource_steps()` 创建生成器对象，函数体还没开始，所以先打印 `generator created`。
2. `next(steps)` 推进这份对象，才进入函数体，打印 `before yield`。
3. `yield "sandbox"` 交出字符串，并暂停在这里；`next(steps)` 取得这个值，赋给 value。
4. 调用方继续打印 `value sandbox` 和 `back in caller`。此时没有再次推进，所以没有打印 `after yield`。

这里的字符串只用来观察交接。**yield 不等于 return：交出一个值以后，生成器仍保存着暂停的位置。** 本节只调用一次 next；后续由上下文管理器接手推进，不需要现在展开整套迭代协议。

## 4. yield：本节只带走两件事

1. 调用这个函数，只创建生成器；第一次 next 才推进函数体。
2. yield 交出值并暂停，随后先由调用方继续执行。

自查：`after yield` 没出现，能说明函数已经按顺序跑完了吗？

<details><summary>查看解释</summary>

不能。它停在 yield，后面的语句还没有被这次 next 推进到。

</details>

下一节再补另一个小零件：怎样把一个函数本身交给另一个函数。

---

[上一节：21.1 · try/finally：分清准备、使用和关闭](../21-resource-lifecycle/) · [下一节：21.3 · @ 装饰器：把函数交给另一个函数处理](../21-decorators/) · [返回学习路线](../learning-route/)
