# run_in_executor 与 wrap_future 的关联

**核心关联：run_in_executor 提交工作后接好可 await 的 Future；wrap_future 接回已经提交的工作。**

| 接口 | 手上有什么，以及它做什么 |
| --- | --- |
| `loop.run_in_executor(reader, func, *args)` | 手上是函数和参数；向 reader 提交工作，并返回可 await 的 asyncio Future |
| `asyncio.wrap_future(executor_future)` | 手上已经有执行器 Future；把它接成可 await 的 asyncio Future，不再提交工作 |

两者得到的都是可 await 的结果对象，区别是**这次工作是否已经提交**。

在本课使用的 **CPython 3.12.3** 中，显式传入 reader 时，run_in_executor 的内部就是先调用 reader.submit，再通过 wrap_future 包装结果。供以后画图时保留这条关系：

```text
run_in_executor
    ├─ submit：提交工作，取得执行器 Future
    └─ wrap_future：包装为 asyncio Future

已有执行器 Future
    └─ wrap_future：直接接上 await，无需再次提交
```

[关系数据（JSON）](run-in-executor-and-wrap-future.json)。
