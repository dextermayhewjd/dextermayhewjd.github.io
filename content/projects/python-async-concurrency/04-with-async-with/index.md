---
title: "04 · with / async with：进入、执行与退出"
description: "从打开文本文件、读取内容、自动关闭，理解 with 的进入与退出，再认识异步形式。"
weight: 40
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 读完一个文件以后，谁来关闭它？

前面三课已经会调用函数、接收返回值，再继续执行下一行。现在用一件具体的事情认识代码块的进入和退出：**打开一个文本文件，读出内容，用完后关闭它。**

这个例子只需要认出几个普通文件操作：

| 写法 | 做什么 |
| --- | --- |
| `open("message.txt", encoding="utf-8")` | 打开文本文件，返回一个文件对象；默认用于读取 |
| `file.read()` | 读取这个文件的文字，返回字符串 |
| `file.close()` | 关闭文件，释放它占用的文件资源 |
| `file.closed` | 查看文件是否已经关闭，结果是 `True` 或 `False` |

沿用逐行调用的方式，正常路径可以写成：

```python
file = open("message.txt", encoding="utf-8")
text = file.read()
file.close()
```

这样可以完成读取，但每次使用文件，都要记得在用完后调用 `close()`。现在的要求是：**把“用完后关闭”绑定到这段使用文件的代码，不在每次读取之后单独安排关闭。**

<span id="async-with-basics"></span>

## 2. with open：读取文件，离开代码块后自动关闭

先准备一个内容为 `hello` 的文本文件 `message.txt`。下面是完整可运行的脚本：

```python
def main():
    with open("message.txt", encoding="utf-8") as file:
        text = file.read()
        print("content", text)
        print("inside closed", file.closed)

    print("outside closed", file.closed)


if __name__ == "__main__":
    main()
```

下载 [example.py](example.py) 和 [message.txt](message.txt)，放在同一个目录，在该目录运行 `python3 -W error example.py`。程序只读取文本文件，不改写它。

本机 Python 3.12.3 的实际输出：

```text
content hello
inside closed False
outside closed True
```

先看这个变化：**代码没有直接调用 `file.close()`，但走到块外时，文件已经关闭了。** `False` 表示在使用它时仍然打开；`True` 表示离开代码块以后已经关闭。

## 3. with / as：沿打开、读取、关闭走一遍

1. **取得文件对象。** `open(...)` 打开文件并返回文件对象。
2. **进入文件的使用范围。** `with` 执行这个对象提供的进入操作。本例的进入操作返回文件对象，`as file` 把它交给变量 `file`。
3. **执行缩进里的代码。** `read()` 读出 `hello`，赋给 `text`；此时 `file.closed` 还是 `False`。
4. **退出使用范围。** 到达缩进末尾，`with` 执行文件对象提供的退出操作。本例的退出操作会关闭文件。
5. **继续块外代码。** 退出完成后，执行最后一行，看到 `file.closed` 是 `True`。

`file` 只是我们选择的变量名。`as` 接收的是**进入操作的返回值**；这个文件例子返回自身，但其他对象可以提供不同的值。

文件自动关闭的行为由文件对象提供。不要把它记成“所有 `with` 都会关闭文件”：共同的结构是**进入 → 使用 → 退出**，具体的进入和退出操作要看使用的对象。

本课只先观察正常读取。读取失败等异常路径，等学到异常与清理时再展开。

## 4. async with：如果进入和退出本身需要等待

现在已经看到了具体的进入和退出：在文件例子里，是进入使用范围、用完后关闭文件。

后面还会遇到进入或退出需要异步等待的对象。`async with` 就是允许这两个阶段异步等待的写法，写在 `async def` 函数内部。

它的正常顺序仍然是：

**进入 → 接收进入结果 → 执行缩进代码 → 退出 → 继续后面的代码。**

结合第 02 课理解：进入和退出都可能先等待，完成以后再继续。因此，走到缩进末尾，不一定马上执行块外的下一行。

这不表示把上面的 `with open(...)` 直接改写成 `async with open(...)` 就可以；普通文件对象不提供这种异步进入和退出。下一单元会使用真实支持 `async with` 的 TaskGroup，通过完整实验观察退出时的等待。

**`async with` 也不会让块内语句自动并发。** 块内仍遵循已经学过的调用和等待规则，需要另行安排任务时仍然要创建 Task。

## 5. 带走三条结论，再做自查

1. **`with` 把进入和退出绑定到一段代码。** 本例读完文件、离开代码块时，由退出操作关闭文件。
2. **`as` 接收进入操作的返回值。** 本例交给 `file` 的是文件对象。
3. **`async with` 允许进入和退出异步等待。** 它不让块内语句自动并发，也不适用于任意普通对象。

试着回答：

1. 例子没有直接调用 `file.close()`，文件为什么会关闭？
2. 到达缩进末尾时，要先做什么，才能继续执行块外的打印？
3. 能不能把普通文件的 `with open(...)` 直接换成 `async with open(...)`？

<details>
<summary>查看自查解释</summary>

1. 离开 `with` 代码块时，文件对象的退出操作关闭了它。
2. 先执行退出操作，完成后再继续块外的代码。
3. 不能。对象必须提供对应的异步进入和退出操作。

</details>

下一步用[第 05 单元的 TaskGroup 实验](../04-taskgroup/)观察：退出操作需要等待组内任务时，块外的代码什么时候执行。

语义核对：[Python 3.12 的 open](https://docs.python.org/3.12/library/functions.html#open)、[文件对象作为上下文管理器](https://docs.python.org/3.12/library/io.html#io.IOBase)及 [async with](https://docs.python.org/3.12/reference/compound_stmts.html#the-async-with-statement)。

---

[专题首页](../) · [上一节：03 · create_task：先安排工作，再等待结果](../03-tasks/) · [下一节：05 · TaskGroup：离开代码块前，等任务结束](../04-taskgroup/) · [完整学习路线](../learning-route/)
