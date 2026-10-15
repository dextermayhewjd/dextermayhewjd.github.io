---
title: "30 · queue.Queue：在线程之间交接数据"
description: "普通工作线程怎样逐项取数据，并在没有数据时等待？"
weight: 300
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
hideInProjectNav: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 18 课](../07-queues/)用队列保存待处理的数据；[第 27–29 课](../29-thread-event/)已能启动线程并等待退出。
>
> **本课新增的问题：** 普通工作线程怎样逐项取数据，并在没有数据时等待？

## 1. queue.Queue：普通线程中的数据交接

`queue.Queue` 用于线程间同步交接，直接调用 put/get。它们需要等待时会阻塞调用线程；这里不用 await，也不把 `asyncio.Queue` 直接拿来跨线程共享。

## 2. put / get：有界队列、数据与结束消息

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import queue
import threading


def consumer(inbox):
    while True:
        item = inbox.get()
        if item is None:
            print("consumer stopped")
            return
        print("received", item)


def main():
    inbox = queue.Queue(maxsize=1)
    inbox.put(10)
    try:
        inbox.put(11, block=False)
    except queue.Full:
        print("queue full")
    thread = threading.Thread(target=consumer, args=(inbox,))
    thread.start()
    inbox.put(None)
    thread.join()
    print("consumer joined")
    try:
        inbox.get_nowait()
    except queue.Empty:
        print("queue empty")


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
queue full
received 10
consumer stopped
consumer joined
queue empty
```

## 3. Queue：按填入、消费、结束读

1. 容量是 1，主线程先放入 10。消费者还没启动，第二次非阻塞 put 没有空位，抛出 Full。
2. 启动消费者后，它通过 get 取出 10，打印 received。get 遇到空队列会等待后续数据。
3. 主线程放入 None；必要时先等消费者腾出空间。None 是本例约定的结束消息，消费者取到它就返回。
4. join 确认消费者结束，再做 get_nowait；此时队列为空，抛出 Empty。

None 的含义由这份程序约定；若业务数据允许 None，就应另选不会和数据混淆的结束标记。

## 4. get_nowait / Empty / Full：直接尝试，再处理结果

`get_nowait()` 相当于不等待地取一项：有数据就返回，没数据就抛 Empty。主例子的 `put(..., block=False)` 同理，满了就抛 Full。

普通 `put()` / `get()` 也可以传 timeout，超时仍放不进去或取不到时抛对应异常。不要把“暂时为空”当作“生产已经结束”；结束需要明确消息或其他协议。

## 5. Queue：带走两条结论

1. 数据可以保存在队列中；get 取走一项，空了才需要等待。
2. 工作结束消息与线程真正退出是两个步骤，最后用 join 确认。

自查：只把队列里的数据取完，消费者一定会退出吗？

<details><summary>查看解释</summary>

不会。本例消费者会继续 get，空队列上等待；必须收到约定的结束消息，才返回。

</details>

<details><summary>按需阅读：项目对照与标准库依据</summary>

主例子是独立标准库实验。[与已经学过的 asyncio.Queue 对照](../07-queues/)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/queue.html#queue-objects)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[上一节：29 · threading.Event：通知线程合作退出](../29-thread-event/) · [下一节：31.1 · ThreadPoolExecutor / submit：把工作提交到线程池](../31-threadpool-submit/) · [返回学习路线](../learning-route/)
