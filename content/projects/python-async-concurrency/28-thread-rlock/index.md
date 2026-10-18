---
title: "28.2 · threading.RLock：允许同一线程嵌套加锁"
description: "外层函数已经持锁，内层函数也需要同一把锁时，用 RLock 配对处理同一线程的重复获取与释放。"
weight: 282
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [28.1 的 Lock](../28-thread-lock/)保护线程共享状态；进入 `with lock` 时获取锁，离开时释放锁。
>
> **本节新增的问题：** 外层函数已经取得一把锁，调用的内层函数也要取得同一把锁。同一线程怎样完成这次嵌套调用？

## 1. 已经持锁，为什么还会再次获取？

<span id="rlock-use-case"></span>

### 1.1. 普通 Lock 保护的是一整段共享数据操作

你的理解方向是对的：线程锁用于协调不同线程对共享数据的访问。更准确地说，**多个线程约定使用同一把锁，使受保护的操作不交错**。锁不会自动绑定到某个列表、变量或函数；绕过这把锁访问数据的代码仍能执行。

例如，两条线程都要把同一个计数加一。如果它们都先读到 0，再各自写回 1，最后只增加了一次。把完整的“读取 → 计算 → 写回”放在同一把锁保护的范围内，才是我们要保护的操作。

### 1.2. 为什么一个线程里会出现两次获取？

想象一个购物车有两个操作，约定所有增删和查看都遵守同一把锁：

| 函数 | 使用场景 | 为什么获取锁 |
| --- | --- | --- |
| `add_item(name)` | 单独加入一个商品 | 它可能被不同线程直接调用，需要保护更新 |
| `add_bundle()` | 一次加入键盘和鼠标组成的套装 | 两件都加入之前，不让其他遵守锁的操作看到半套商品 |

`add_bundle()` 可以复用 `add_item()` 加入两件商品。于是，外层函数持锁时调用内层函数，内层也会执行获取锁的代码。**函数调用没有切换线程：仍是同一个线程，走到了另一处 `with lock`。**

### 1.3. 用同一个购物车看实际代码

这是独立的标准库场景示例，不是 Slime 源码。[下载 scenario.py](scenario.py)，运行 `python3 -W error scenario.py`。

```python
import threading


cart = []
lock = threading.RLock()  # 约定购物车的访问都遵守这同一把锁。


def add_item(name):
    with lock:  # 单独调用 add_item 时，也要保护购物车更新。
        cart.append(name)


def add_bundle():
    with lock:  # 把加入两个商品视为一次完整更新。
        add_item("keyboard")  # 当前线程进入 add_item，再次取得同一把锁。
        add_item("mouse")  # 上一次内层已退出；外层仍持锁，再完成第二次添加。


if __name__ == "__main__":
    add_bundle()
    print(cart)
```

Python 3.12.3 下的实际输出：

```text
['keyboard', 'mouse']
```

本例只运行一个线程，先验证两个可组合函数的嵌套调用。多个线程共同使用时，其他线程仍须通过同一把锁访问购物车。

沿着当前线程走一次：

1. 进入 `add_bundle()` 的 `with lock`，第一次取得锁，开始加入整套商品。
2. 调用 `add_item("keyboard")`，仍在当前线程内，但走到了里面的 `with lock`，因此第二次获取同一把锁。
3. RLock 允许这次重入；加入键盘后，内层退出并释放一次，外层仍持锁。
4. 添加鼠标时重复内层的获取与释放。最后退出 `add_bundle()` 的外层 `with`，其他线程才有机会取得锁。

### 1.4. 换成普通 Lock 会怎样？

只把上例的 `threading.RLock()` 改成 `threading.Lock()`：外层第一次获取成功；进入第一次 `add_item()` 时，内层发现锁已锁定，开始等待。外层要等内层返回才会释放锁，内层却在等这把锁被释放，于是这条线程会卡住。不要把这个版本当作会自行结束的运行练习；第 4 节使用非阻塞获取来安全观察区别。

RLock 的规则是：**其他线程仍要等；已经拥有这把锁的线程可以再次进入。** 它没有让两条线程同时进入，也没有创建第二把锁。

也可以重新组织函数，把持锁集中到外层，让不加锁的内层实现只供外层调用。RLock 适合这里希望保留 `add_item()` 独立调用能力、同时复用它组成外层完整操作的场景；并非遇到嵌套函数就必须使用 RLock。

## 2. RLock：先看同一线程的两层 with

[下载 example.py](example.py)，运行 `python3 -W error example.py`。把刚才两个函数的调用展开，只留下锁的进入与退出，就得到下面的两层 `with`；仍然只运行一条线程。

```python
import threading


def main():
    lock = threading.RLock()  # 同一线程可以重复取得这把锁。
    with lock:  # 第一次取得；退出外层时才完成最后一次释放。
        print("outer acquired")
        with lock:  # 当前线程第二次取得同一把锁，不会等待自己。
            print("inner acquired")
        print("inner released; outer still holds lock")
    print("outer released")


if __name__ == "__main__":
    main()
```

Python 3.12.3 下的实际输出：

```text
outer acquired
inner acquired
inner released; outer still holds lock
outer released
```

## 3. 获取与释放怎样配对？

RLock 记录拥有它的线程和重复获取的层数。这里的层数用于解释配对关系，不需要读取私有属性。

| 执行到哪里 | 当前线程尚未配对释放的获取次数 | 其他线程能否取得这把锁 |
| --- | ---: | --- |
| 进入外层 with | 1 | 不能 |
| 进入内层 with | 2 | 不能 |
| 退出内层 with | 1 | 不能，外层仍持锁 |
| 退出外层 with | 0 | 可以竞争获取 |

1. 内层能够进入，是因为它仍在拥有锁的同一线程中执行。
2. 内层退出只配对释放一次，外层的获取仍然有效。
3. 最后一次释放之后，其他线程才有机会取得锁；不保证哪一条等待线程先取得。

使用 `with` 会在退出对应代码块时释放，包括异常导致的退出。如果手动调用 `acquire()` / `release()`，每次成功获取都要由拥有锁的线程配对释放。

## 4. Lock 与 RLock 的第二次获取有什么差别？

[下载 compare.py](compare.py)。它在**同一线程**中尝试获取两次，并使用 `blocking=False`：取不到就返回 `False`，不会让演示程序卡住。

```python
import threading


def main():
    for name, lock in [("Lock", threading.Lock()), ("RLock", threading.RLock())]:
        first = lock.acquire(blocking=False)  # 不等待；空闲锁第一次获取成功。
        second = False
        try:
            second = lock.acquire(blocking=False)  # 同一线程再次尝试，不等待，避免演示卡住。
            print(f"{name}: first={first}, second={second}")
        finally:
            if second:
                lock.release()  # 只有第二次也成功，才释放第二次获取。
            if first:
                lock.release()  # 配对释放第一次获取。


if __name__ == "__main__":
    main()
```

实际输出：

```text
Lock: first=True, second=False
RLock: first=True, second=True
```

`True` 表示本次获取成功，`False` 表示本次未取得锁。第二行最后需要释放两次，因为两次获取都成功了。

## 5. 本节带走什么？

1. 普通 Lock 锁住以后，同一线程再次获取也会等待；RLock 允许拥有它的线程重复获取。
2. RLock 每次成功获取都要配对释放；最后一次释放后，其他线程才能取得。
3. 重入按**线程**判断。同一事件循环线程中的多个 Task 不能靠 RLock 互相排斥；跨 `await` 的任务共享状态应回看[第 19 课的 asyncio.Lock](../19-async-lock/)。
4. 多把锁获取顺序冲突仍可能死锁；RLock 只处理同一线程对同一把锁的重入。

自查：外层与内层各取得一次 RLock，内层退出后，另一条线程能立刻取得它吗？如果手动获取两次却只释放一次，锁会怎样？

<details>
<summary>核对答案</summary>

内层退出后，外层仍持锁，另一条线程不能取得。只释放一次会留下一个尚未配对的获取，其他线程仍无法取得这把锁。

</details>

<details>
<summary>按需阅读：Slime 为什么使用 RLock，以及旧教材入口</summary>

Slime 固定版本 `22a89f96835969a47055a659c588f46151f8b07a` 的核心包中，`threading.RLock()` 有 **5 个显式构造位置**。以下是一条实际需要嵌套获取的路径：

1. [`get_accelerator()`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/accelerator/__init__.py#L311-L319) 在尚未缓存设备时，取得 `_SELECTION_LOCK`，随后调用 `_register_builtin_backends()`。
2. [`_register_builtin_backends()`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/accelerator/__init__.py#L246-L259) 在后端尚未登记时调用 `register_accelerator()`。
3. [`register_accelerator()`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/accelerator/__init__.py#L53-L70) 再次取得同一把 `_SELECTION_LOCK`，更新登记表。

锁在[第 39 行](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/accelerator/__init__.py#L39)创建为 RLock。这条调用链仍在同一线程内，内层返回后，外层继续保护设备选择过程。

其他四处构造保护归档写入、训练状态、读者租约和存储写入，位置见[Slime 原生并发用法索引](../usage-index/threading/)。上述次数是源码位置数，不是运行次数。

[旧版 Condition、RLock、Timer 综合教材](../16-thread-coordination/#rlock-reentrancy)保留原例子、下载和源码回查；Condition 与 Timer 在需要它们时再读。

语义依据：[Python 3.12 RLock 文档](https://docs.python.org/3.12/library/threading.html#rlock-objects)。

</details>

[Lock ↔ RLock：关系摘要](../comparisons/lock-vs-rlock/)

---

[上一节：28.1 · threading.Lock](../28-thread-lock/) · [下一节：29 · threading.Event](../29-thread-event/) · [返回学习路线](../learning-route/)
