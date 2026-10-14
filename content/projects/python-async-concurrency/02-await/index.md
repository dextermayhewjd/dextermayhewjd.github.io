---
title: "02 · await：等待结果，不等于自动并发"
description: "先回顾协程的创建与运行，再对比脚本入口和协程内部的等待。"
weight: 20
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 先回顾：第 01 课已经能做什么

1. **定义**：`async def generate(...)` 定义一个协程函数。
2. **创建**：`coro = generate(10)` 只创建协程对象，函数体还不执行。
3. **运行**：普通脚本用 `result = asyncio.run(coro)` 运行它，正常结束后取得返回值。

沿用第 01 课的 `generate`，我们已经会这样写：

```python
coro = generate(10)
result = asyncio.run(coro)
```

这两行位于第 01 课的普通 `def main()` 里；脚本入口先调用 `main()`，再由 `asyncio.run()` 进入异步执行。

## 2. 在协程里面，还能继续用 run 吗？

1. **上一节已经会了：** 在普通代码中，用 `asyncio.run(coro)` 执行协程，取得返回值。
2. **现在多一层调用：** 一份正在运行的协程，也需要调用另一份协程，并取得它的返回值。
3. **先尝试原来的办法：** 能不能在里面再写一次 `asyncio.run()`？看下面这段代码。

<div class="async-await-comparison" id="await-call-context">
<figure class="async-call-context" aria-label="外部代码通过 run 启动外层协程，外层协程还需要执行并等待内层协程">
  <figcaption>调用关系</figcaption>
  <div class="async-call-context__step async-call-context__external"><strong>外部代码</strong></div>
  <div class="async-call-context__connector">
    <code>asyncio.run(main())</code>
    <span aria-hidden="true">↓</span>
  </div>
  <div class="async-call-context__scope">
    <p class="async-call-context__label">事件循环已经运行</p>
    <div class="async-call-context__step"><strong>外层协程正在执行</strong><span>本例中的 main</span></div>
    <div class="async-call-context__gap">
      <span class="async-call-context__question" aria-hidden="true">？</span>
      <span>怎样执行它，并等到结果？</span>
      <span class="async-call-context__arrow" aria-hidden="true">↓</span>
    </div>
    <div class="async-call-context__step"><strong>内层协程对象</strong><span>本例中的 generate(10)<br>已创建，尚未执行</span></div>
  </div>
</figure>
<figure class="async-call-code" aria-label="错误尝试：在已运行的协程内部再次调用 asyncio.run">
  <figcaption>对应代码：内层再次 run 的错误尝试</figcaption>

  <pre><code>import asyncio

async def generate(rollout_id):
    return rollout_id

async def main():
    coro = generate(10)
<span class="async-call-code__blocked">    result = asyncio.run(coro)</span>

if __name__ == "__main__":
<span class="async-call-code__entry">    asyncio.run(main())</span></code></pre>

  <p class="async-call-code__note async-call-code__note--blocked"><strong>内层这一行不能再用 asyncio.run。</strong><br>main 已在事件循环中执行，同一线程不能再启动一轮 run。</p>
  <p class="async-call-code__note async-call-code__note--entry"><strong>底部是脚本入口。</strong><br>直接运行这个文件时，先由这里的 run 启动 main，再执行 main 内部的代码。</p>
</figure>
</div>

在这个已经运行的外层协程里：

1. 调用协程函数只创建协程对象，不会自动执行函数体。
2. 同一线程的事件循环已经在运行，不能再调用 `asyncio.run()`。

**所以，本课要解决：已经在协程里面，怎样执行另一份协程并取得结果？**

<span id="await-execution"></span>

## 3. 新增 await：在协程内部执行并等待结果

<details id="previous-lesson-example">
<summary>展开第 01 课的代码，对比 run 和 await</summary>

第 01 课先由脚本入口调用普通函数 `main()`，再在其中用 `asyncio.run(coro)` 运行 `generate`：

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

[打开第 01 课](../01-async-def/) · [下载这份代码](../01-async-def/example.py)

</details>

> **在 `async def` 函数内部，`result = await coro` 执行并等待这份协程，取得返回值后，再继续下一行。**

先只改主流程，`generate` 仍然和第 01 课一样：

1. 第 01 课直接调用普通函数 `main()`，在它内部用 `asyncio.run(coro)` 运行 `generate`。
2. 第 02 课的 `main` 是协程函数；脚本入口 `asyncio.run(main())` 先求出 `main()` 返回的协程对象，再由 `run` 运行它。
3. 进入 `main` 后，再用 `await coro` 执行并等待内部的 `generate`。

```python
import asyncio

async def generate(rollout_id):
    print("run", rollout_id)
    return rollout_id

async def main():
    coro = generate(10)
    print("created")
    result = await coro
    print("result", result)

if __name__ == "__main__":
    asyncio.run(main())
```

[下载 await_example.py](await_example.py) · 运行：`python3 await_example.py`

实际输出仍然是：

```text
created
run 10
result 10
```

沿执行顺序看两层如何交接：

1. **脚本入口**：先由 `main()` 创建外层协程对象，再由 `asyncio.run(...)` 开始运行它。
2. **内部创建**：`generate(10)` 只创建对象；`main` 接着打印 `created`。
3. **内部等待**：`await coro` 进入这份 `generate`，打印 `run 10`，然后 `return 10`。
4. **接回结果**：`await` 得到 10，交给 `result`；`main` 继续打印 `result 10`。

## 4. 把旧写法和新写法放在一起

1. **第 01 课：普通脚本运行一份协程。**
   - 写法：`result = asyncio.run(coro)`。
   - 这份协程结束后，返回普通脚本，继续脚本的下一行。

2. **第 02 课：已经运行的协程，等待内部另一份协程。**
   - 写法：`result = await coro`。
   - 内部协程结束后，返回外层协程，继续外层的下一行。
   - 最外面的 `asyncio.run(main())` 仍然保留，负责脚本入口。

两种写法对应不同的调用层级：外层保留 `run` 作为执行入口，内部通过 `await` 等待 `generate` 并接回结果。

**两种写法得到的数字都是 10；新增 await 是为了解决“已经在协程里面，怎样继续等另一份协程”的问题。**

## 5. 本课带走的最小结论

1. **外层协程开始运行，不代表它创建的内部协程会自动执行。**
2. **`await` 可以写在 `async def` 函数内部，等待另一份协程。**
3. **`await coro` 得到的是该协程的返回值，不是协程对象。**
4. **这份调用返回后，外层协程才继续执行 await 后面的代码。**
5. **同一线程已有运行中的事件循环时，不能再调用 `asyncio.run()`。本例在协程内部用 `await` 等待另一份协程。**

试着回答：

1. 刚执行完 `coro = generate(10)`，`coro` 里面是数字 10 吗？
2. 哪一行让 `generate` 的函数体开始执行？它返回后，又回到谁的下一行？
3. 为什么不能把 `main` 内部的 `await coro` 直接换成 `asyncio.run(coro)`？

## 6. 再观察：内部操作需要等待时

正文里的 `generate` 可以直接返回，`await` 并不保证中途发生任务切换。如果它内部还有 `await asyncio.sleep(...)` 这样的等待，当前执行链会暂停，恢复后从原处继续；**内部暂停不代表外面的 await 已经等完。**

下面保留原有的暂停、恢复与两次顺序调用实验，理解上述两层调用后再展开。

<details>
<summary>补充实验：内部暂停后，从哪里继续？</summary>

## 本节新增：等待期间暂停，之后从原处继续

> **`await` 要等当前操作完成；如果等待需要暂停，当前执行链会先挂起，恢复后继续执行尚未完成的代码。**

正文的 `generate` 只有打印和返回，没有中途的异步等待。现在再给它增加 `await asyncio.sleep(0)`：这个操作会让当前执行链暂停一次。这里用 0 秒，是为了观察一次暂停与恢复；等待本身不必很长。

一个协程里面写了两次 `await`，两份工作会自动同时开始吗？先运行，再判断。

```python
import asyncio

async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id

async def main():
    first = await generate(10)
    second = await generate(11)
    print("results", [first, second])

if __name__ == "__main__":
    asyncio.run(main())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
start 10
end 10
start 11
end 11
results [10, 11]
```

`main()` 要等第一份结果返回，才会走到第二个 `generate`。本节先读清这一条执行链：**进入协程 → 等待 → 恢复 → 返回**。

## 跟着第一份调用走一次

```text
main()
  │
  ├─ await generate(10)：进入 generate 的函数体
  │    ├─ 打印 start 10
  │    ├─ await asyncio.sleep(0)：当前执行链暂停一次
  │    ├─ 恢复后打印 end 10
  │    └─ return 10
  │
  ├─ 第一份调用返回后，才进入 generate(11)
  └─ 最后打印 results
```

`await generate(10)` 要等待整个 `generate(10)` 返回。内部的 `await asyncio.sleep(0)` 则是它执行过程中的一次等待；恢复后，先继续这一份 `generate` 剩下的代码。

因此，**内部暂停过，不代表外层已经执行完这一行**。第二行 `await generate(11)` 仍然要等第一行结束。

## 对比：保留赋值与去掉赋值

两组都使用本补充实验中含 `await asyncio.sleep(0)` 的同一个 `generate()`。

保留赋值：

```python
async def with_assignment():
    first = await generate(10)
    second = await generate(11)
```

去掉赋值：

```python
async def without_assignment():
    await generate(10)
    await generate(11)
```

两组输出完全相同：

```text
A: with assignment
start 10
end 10
start 11
end 11
B: without assignment
start 10
end 10
start 11
end 11
```

`first =` 和 `second =` 只保存返回值。即使不保存，`await` 也要等这份调用返回后，才能继续下一行。

[下载 comparison.py，运行这两组对比](comparison.py)。这是独立的标准库语言实验，不是 Slime 原始源码。

## 暂停之后，为什么还是先完成 10

当前实验只有这一条执行链。第二个 `generate` 还没开始，不能因为第一份内部暂停，就自动提前运行第二行。

这里的 `sleep(0)` 让出一次后可以很快恢复；如果换成 `sleep(1)`，即使没有其他工作，也要等计时条件满足。**没有别的工作可运行，不等于这次等待被跳过。**

<span id="sleep-time-and-execution"></span>

### 等待时间与代码执行要分开看

> **对于 `await asyncio.sleep(...)`，等待时间继续流逝，但当前协程的代码暂时不向下执行。**

```python
await asyncio.sleep(2)
print("继续执行")
```

这两秒里，协程停在 `await`，还不会执行后面的 `print`。这叫挂起，不是退出或终止；也不是函数体在后台继续跑。

两秒到了，只是满足了继续执行的条件。还要轮到这个协程获得执行机会，后面的 `print` 才会运行。其他代码执行所消耗的时间，不会让这次 sleep 的等待重新计时。

下一节再学习怎样安排另一份工作。在学到那里之前，先不要求从本实验中看出交错执行。

## 不只有 sleep 才能暂停

关键是等待的操作是否需要暂停，而不是函数名叫不叫 `sleep`。`asyncio.sleep()` 本身也是协程；网络读取等异步操作也可能需要等待。反过来，协程如果一路执行到 `return`，没有遇到需要暂停的操作，也可以直接返回。

因此，看见 `await` 时先问两件事：

1. 这一行要等谁的返回结果？
2. 被等待的代码内部，在哪里需要暂停？

## 本节带走的最小结论

- **等待完成，才继续下一行**：`await generate(10)` 要等这份 `generate` 返回。
- **中途暂停，不等于整次调用已经返回**：恢复后先执行这份协程剩下的代码。
- **两行直接 `await` 仍有先后顺序**：第一份返回后，才执行第二行；赋值只保存结果，不改变这个顺序。

下一节再增加一种组织方式：先把多份工作安排好，再等待它们的结果。

## 用自己的话回答

第一份 `generate` 内部等待过，为什么第二份还没有开始？去掉 `first =` 会改变顺序吗？

<details><summary>查看解释</summary>

内部等待只是第一份调用执行过程中的暂停。第一份还没返回，外层就还没执行到第二行。赋值只保存结果，去掉它不改变直接 `await` 的先后顺序。

</details>

语义核对：[协程](https://docs.python.org/3.12/library/asyncio-task.html#coroutines)、[sleep](https://docs.python.org/3.12/library/asyncio-task.html#sleeping)。

</details>

{{< python-async-slime >}}

## 回到 Slime：等待完成标记

`_await_done_marker()` 会先等待一段时间，再读取外部命令的完成标记。如果标记还没出现，就继续下一轮；读取成功时才返回退出码。

这里只关注三处顺序：`await asyncio.sleep(5)`、`await sb.exec(...)`、`return`。`sb.exec` 是执行环境提供的异步操作，具体实现在后续源码阅读时展开。

<details>
<summary>展开 Slime 源码：_await_done_marker 的等待与返回</summary>

{{< source-reference id="source-1" >}}

</details>

{{< python-async-coverage lesson="02-await" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../01-async-def/) · [下一节：03 · create_task：先安排工作，再等待结果](../03-tasks/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
