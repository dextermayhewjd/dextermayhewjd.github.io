---
title: "01 · async def：定义之后，什么时候执行？"
description: "用一个例子分清协程函数、协程对象、执行入口和返回值。"
weight: 10
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="coroutine-definition"></span>

## 1. 先看问题和例子

**调用了 `generate(10)`，函数体就执行了吗？** 普通函数调用后就会执行函数体。把定义改成 `async def` 后，这一点会改变。

先猜下面的输出：**`created` 和 `run 10`，哪一个先出现？**

<span id="run-entry"></span>

```python
import asyncio

async def generate(rollout_id):
    print("run", rollout_id)
    return rollout_id

def main():
    coro = generate(10)
    print("created")
    result = asyncio.run(coro)
    print("result", result)

if __name__ == "__main__":
    main()
```

[下载 example.py](example.py) · 运行：`python3 example.py`

先认清脚本入口：

1. `main` 是这里选用的函数名。第 01 课用普通 `def main()` 组织主流程，调用 `main()` 就会执行里面的代码。
2. `if __name__ == "__main__":` 表示文件被直接运行时，才调用下面的 `main()`；被其他文件导入时不自动运行主流程。

实际输出：

```text
created
run 10
result 10
```

## 2. 沿同一次调用，分清三个阶段

1. **定义时：`async def generate(...)`**
   - 建立协程函数 `generate` 和普通函数 `main`，此时都还没有执行函数体。
   - 函数体里的 `print` 和 `return` 还不执行。

2. **调用时：`coro = generate(10)`**
   - 入口先调用普通函数 `main()`，再在其中创建这一次 `generate(10)` 的协程对象，保存在 `coro` 中。
   - `generate` 的函数体仍未执行，`coro` 也不是数字 10。
   - 脚本继续下一行，先打印 `created`。

3. **运行时：`result = asyncio.run(coro)`**
   1. `run` 接过这份协程，开始执行函数体，打印 `run 10`。
   2. 函数执行 `return 10`，这份协程正常结束。
   3. `run` 返回这个 10，赋给 `result`；脚本继续打印 `result 10`。

对应到三个名字：

1. **`generate`**：定义出来的协程函数。
2. **`coro`**：调用后创建的协程对象。
3. **`result`**：运行结束后取得的返回值。

## 3. 读完带走这五条知识

1. **`async def` 定义协程函数。**
2. **调用协程函数，会创建协程对象。**
3. **创建协程对象，不会执行函数体。**
4. **`asyncio.run(coro)` 运行传入的协程，等待它结束。**
5. **正常结束时，`run` 返回该协程的返回值。**

试着不看上面的解释，回答：

1. 执行完 `coro = generate(10)` 时，函数体里的 `print` 执行过了吗？
2. `coro` 和 `result` 分别是什么？

下一课只增加一个问题：**已经在协程内部时，怎样执行另一份协程并取得结果？** 到[第 02 课](../02-await/)再引入 `await`。

{{< python-async-slime >}}

语义核对：[协程](https://docs.python.org/3.12/library/asyncio-task.html#coroutines)、[asyncio.run](https://docs.python.org/3.12/library/asyncio-runner.html#asyncio.run)。

## 4. 按需回到 Slime

原测试用 `generate(rollout_id)` 创建两份工作，再交给 `gather`。现在只需要认出函数定义与调用，下一节再读 `await`，第 05 课再展开 `gather`。

<details>
<summary>展开 Slime 源码：generate / exercise</summary>

{{< source-reference id="source-1" >}}

</details>

{{< python-async-coverage lesson="01-async-def" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [下一节：02 · await：等待结果，不等于自动并发](../02-await/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
