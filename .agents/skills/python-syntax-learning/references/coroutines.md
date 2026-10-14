# 协程的最小边界

读者只知道普通函数时，第一课可先回答“调用之后，函数体执行了吗？”

```python
import asyncio

async def generate(rollout_id):
    print("run", rollout_id)
    return rollout_id

coro = generate(10)
print("created")
result = asyncio.run(coro)
print("result", result)
```

输出：

```text
created
run 10
result 10
```

阶段解释：

1. **定义时**：`generate` 是协程函数，定义尚不执行函数体。
2. **调用时**：`generate(10)` 创建协程对象，赋给 `coro`，函数体仍未执行；普通脚本继续打印 `created`。
3. **运行时**：本例用 `asyncio.run(coro)` 开始执行函数体，打印 `run 10`；协程返回后，`run` 将返回值交给 `result`。

本课的原子结论可以分别陈述“定义得到协程函数”“调用创建协程对象”“创建不会执行函数体”“run 运行传入的协程直到结束”“正常结束时返回协程的返回值”。不强制每条同样长，重点解释创建与执行的区别。

后续才分别引入：协程内部用 `await` 等结果；异步操作未完成时暂停与恢复；`create_task` 安排多份工作；`gather` 收集结果。不要写“协程只有被 await 才能执行”，也不要把 Slime 等项目自己的 `run()` 与标准库 `asyncio.run()` 混为一谈。
