# 53 项 API 选题清单的调用位置覆盖与缺口

由 `tools/build_learning_coverage.py` 生成；选题与 API 清单维护在 [learning-scope.json](learning-scope.json)。

这是**阶段性选题清单覆盖了多少已识别静态调用位置**，不是课程完成度、运行频率或实际场景覆盖率。核算对应 [learning-plan.md](learning-plan.md) 第 4.2 节；当前具体 API 以 [当前 API 清单](current-api-plan.md)为准，本页 53 项保留为历史基线。

## 1. 同一统计口径下的前后变化

原清单明确列出 33 个 API 名称，补充 20 个。构造对象与调用对象的方法分别匹配，不因列了 `Thread` 就自动算上 `Thread.start`。

| 仓库 | 原清单 / 全部相关调用 | 补充后 / 全部相关调用 | 原清单 / asyncio 调用 | 补充后 / asyncio 调用 |
| --- | ---: | ---: | ---: | ---: |
| Slime | 141/229（61.6%） | 174/229（76.0%） | 87/112（77.7%） | 92/112（82.1%） |
| AReaL | 538/756（71.2%） | 595/756（78.7%） | 208/249（83.5%） | 210/249（84.3%） |
| verl | 233/377（61.8%） | 279/377（74.0%） | 167/192（87.0%） | 172/192（89.6%） |

1. 分母是固定清单中 `scope=core` 且 `kind` 为 `api_call` 或 `inferred_method` 的去重记录；包括已识别但尚未映射到官方文档的调用。
2. 分子按 `report.json` 的 API → occurrence ID 映射与分母取交集，沿用别名和继承方法的文档映射；不按网页计数相加。
3. 导入、单纯引用、语法节点、类型不明的候选不计入分子或分母。`TimeoutError` 本组次数来自异常构造调用，`except TimeoutError` 等引用另计。
4. 仅覆盖本资料夹选定的标准库异步与并发范围；Ray、HTTP 客户端、torch.distributed 及业务编排不在这个百分比里。
5. 原清单是此前估算百分比时的显式 API 集合，不是全部现有课程索引。补充项可能在旧课中已有内容，仍需按学习规划核对深度。原生异步与并发路线中未列入该清单的内容，不能沿用此比例声称已经覆盖。

## 2. 补充的操作与新增调用位置

表格按概念位置排列；同一行可拆成多个最小学习单元，不表示要新加一整章。

| 补充内容 | API | Slime | AReaL | verl | 官方入口 |
| --- | --- | ---: | ---: | ---: | --- |
| 判断完成并取结果或异常 | `asyncio.Task.done`、`asyncio.Task.result`、`asyncio.Task.exception`、`asyncio.Future.done`、`asyncio.Future.result`、`asyncio.Future.exception` | 5 | 2 | 5 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#task-object)、[文档 2](https://docs.python.org/3.16/library/asyncio-future.html#future-object) |
| 超时的报告与处理 | `builtins.TimeoutError` | 7 | 30 | 7 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#asyncio.wait_for)、[文档 2](https://docs.python.org/3.16/library/exceptions.html#TimeoutError) |
| 启动线程、通知与等待退出 | `threading.Thread.start`、`threading.Thread.join`、`threading.Thread.is_alive`、`threading.Event.set`、`threading.Event.wait`、`threading.Event.clear` | 12 | 25 | 4 | [文档 1](https://docs.python.org/3.16/library/threading.html#thread-objects)、[文档 2](https://docs.python.org/3.16/library/threading.html#event-objects) |
| 退出时恢复上下文 | `contextvars.ContextVar.reset` | 3 | 0 | 5 | [文档 1](https://docs.python.org/3.16/library/contextvars.html#contextvars.ContextVar.reset) |
| 启动、检查与回收 Python 子进程 | `multiprocessing.Process`、`multiprocessing.Process.start`、`multiprocessing.Process.is_alive`、`multiprocessing.Process.join`、`multiprocessing.Process.terminate`、`multiprocessing.Process.kill` | 6 | 0 | 25 | [文档 1](https://docs.python.org/3.16/library/multiprocessing.html#process-and-exceptions) |

零调用的方法仍可能是解释生命周期的必要配套，例如 `Thread.join` 与 `Event.clear`；它们不增加该仓库的分子。低频配套只讲必要关系，不扩大为完整模块导读。

<details>
<summary>按需核对：各补充组的源码例子</summary>

### 判断完成并取结果或异常

Task 的 done/result 随 wait 展开；Future 对应方法放到后面的 Future 衔接。

- Slime：[slime/data/transport.py:383](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L383)，`asyncio.Task.done`。
- AReaL：[areal/experimental/openai/proxy/proxy_rollout_server.py:1128](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_rollout_server.py#L1128)，`asyncio.Task.done`。
- verl：[verl/experimental/fully_async_policy/detach_utils.py:443](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/fully_async_policy/detach_utils.py#L443)，`asyncio.Task.result`。

### 超时的报告与处理

补入取消与超时主题，先接 wait_for，再看手动截止时间检查。

- Slime：[slime/backends/megatron_utils/server/megatron_server.py:398](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/server/megatron_server.py#L398)，`builtins.TimeoutError`。
- AReaL：[areal/dataset/swe_sft/pipeline.py:958](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/dataset/swe_sft/pipeline.py#L958)，`builtins.TimeoutError`。
- verl：[verl/experimental/fully_async_policy/fully_async_rollouter.py:1388](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/fully_async_policy/fully_async_rollouter.py#L1388)，`builtins.TimeoutError`。

### 启动线程、通知与等待退出

补入线程主题；创建与启动、事件通知、退出与回收分别作为最小单元。

- Slime：[slime/agent/aiohttp_threaded.py:80](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/aiohttp_threaded.py#L80)，`threading.Event.set`。
- AReaL：[areal/engine/awex/sglang_plugin.py:819](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/engine/awex/sglang_plugin.py#L819)，`threading.Thread.start`。
- verl：[verl/single_controller/base/worker_group.py:178](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/single_controller/base/worker_group.py#L178)，`threading.Thread.start`。

### 退出时恢复上下文

补入 ContextVar 主题，与 set 返回的 token 和 try/finally 连起来。

- Slime：[slime/observability/trace_utils.py:419](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L419)，`contextvars.ContextVar.reset`。
- AReaL：本组没有新增调用位置。
- verl：[verl/utils/rollout_trace.py:155](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/utils/rollout_trace.py#L155)，`contextvars.ContextVar.reset`。

### 启动、检查与回收 Python 子进程

在 subprocess.run 后补 multiprocessing.Process；生命周期独立于异步任务讲解。

- Slime：[slime/backends/sglang_utils/deployment.py:53](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L53)，`multiprocessing.Process`。
- AReaL：本组没有新增调用位置。
- verl：[verl/experimental/reward_loop/router/inner_sglang_router.py:49](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/reward_loop/router/inner_sglang_router.py#L49)，`multiprocessing.Process`。

</details>

## 3. 补充后仍留下什么

以下展示每库剩余调用最多的前 8 项，用于按需回查；不自动纳入必读路线。次数按原始规范名显示。

| 仓库 | 剩余位置 | 主要剩余调用（次数） |
| --- | ---: | --- |
| Slime | 55 | `os.getpid`（12）、`threading.RLock`（5）、`asyncio.AbstractEventLoop.time`（4）、`asyncio.AbstractEventLoop.create_future`（3）、`asyncio.AbstractEventLoop.run_until_complete`（2）、`asyncio.current_task`（2）、`asyncio.new_event_loop`（2）、`asyncio.set_event_loop`（2） |
| AReaL | 161 | `os.getpid`（12）、`signal.signal`（10）、`subprocess.Popen`（9）、`concurrent.futures.Future`（8）、`queue.Queue`（8）、`subprocess.check_output`（8）、`concurrent.futures.ThreadPoolExecutor.map`（7）、`asyncio.AbstractEventLoop.create_future`（5） |
| verl | 98 | `signal.alarm`（17）、`inspect.iscoroutinefunction`（12）、`os.getpid`（10）、`signal.setitimer`（4）、`signal.signal`（4）、`asyncio.Event.set`（3）、`asyncio.Task.add_done_callback`（3）、`asyncio.new_event_loop`（3） |

Slime 的后续按需范围包括可重入锁/条件变量、手动事件循环、同步队列与信号。verl 的信号超时和 AReaL 的进程/执行器配套也保留为源码驱动的后续补充。`os.getpid` 等辅助调用计入分母，但无需为提高比例单独开课。

## 4. 固定来源与复算

- Slime：`22a89f96835969a47055a659c588f46151f8b07a`，[逐条清单](repositories/slime/inventory.json)。
- AReaL：`298412a40f5b84ae6b2042987e81777e6dd0f284`，[逐条清单](repositories/areal/inventory.json)。
- verl：`1d367a4f459a43768f76312c0d3430a99ec46b8c`，[逐条清单](repositories/verl/inventory.json)。

```bash
python3 python-async-reference/tools/build_learning_coverage.py
python3 python-async-reference/tools/build_learning_coverage.py --check
```
