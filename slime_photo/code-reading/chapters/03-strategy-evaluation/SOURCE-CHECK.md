# Rollout 接入与奖励：源码核对

- 核对日期：2026-10-25。
- 本地仓库：`/home/fredkeira/projects/slime`。
- 本地 HEAD：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本次只读查询 `THUDM/slime main` 得到同一提交，没有更新本地源码。
- 本文只核对已展开的接入与返回边界；不将文件存在、静态关系或文档生成当作运行证据。

| 解释内容 | 固定源码 |
| --- | --- |
| 示例使用 fully-async rollout 与 Coding Agent 自定义生成 | [run_qwen38_27b_fully_async.sh:165–167](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L165-L167) |
| group 为单个待生成 Sample 创建任务 | [sglang_rollout.py:419–427](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L419-L427) |
| 输入 Sample 的数据字段、状态与生成路径 | [types.py:106–170](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L106-L170) |
| 选择函数、检查参数、创建异步调用并等待 | [sglang_rollout.py:338–349](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L349) |
| 由导入路径取得属性 | [misc.py:50–59](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L50-L59) |
| 被调用的 Coding Agent 包装与正常任务返回 | [generate.py:225–251](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251)、[300–358](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L300-L358) |
| hook、组评分边界、单样本与列表的奖励判断 | [sglang_rollout.py:353–380](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L380) |
| 空列表仍进入批量接口；自定义与默认处理 | [rm_hub/__init__.py:99–110](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L99-L110) |
| state 的共享实例及执行控制成员 | [GenerateState:84–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L84-L140)、[SingletonMeta:62–76](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L62-L76) |
| pacer 分批唤醒；区别于并发上限和手动暂停 | [AsyncPacer:8–42](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/async_utils.py#L8-L42) |
| 生成许可在 hook、RM 之前由 finally 释放 | [sglang_rollout.py:329–378](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L329-L378) |
| 两类包装登记共享状态，供中止逻辑使用 | [258–285](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L258-L285)、[442–465](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L442-L465) |
| 生成器和 hook 新建 Sample 时继承原任务上下文 | [transport.py:207–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L230) |
| aborted 为布尔值；DP 上下文选择最少计数并在退出减回 | [reset 与 DP 上下文:123–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L123-L140)、[abort:442–448](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L442-L448) |

本轮未执行生成或评分契约测试；并发、取消、评分插件、失败结果及真实环境仍需各自的行为证据。文档构建与链接检查只用于验证阅读材料。


## 2026-10-26 · Semaphore.acquire 补充核对

- Slime 本机 `/home/hongshi/projects/slime`，HEAD `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，工作区干净；没有改写上方历史核对时记录的路径。
- 标准库为本地 Python 3.12.3 的 `/usr/lib/python3.12/asyncio/locks.py`，Semaphore.acquire 在 363–397 行；对照 [CPython v3.12.3](https://github.com/python/cpython/blob/v3.12.3/Lib/asyncio/locks.py#L363-L397) 与 [Python 3.12 接口文档](https://docs.python.org/3.12/library/asyncio-sync.html#asyncio.Semaphore.acquire)。在线维护版文档与固定实现版本分开。
- 使用 Semaphore(1) 和两个本地任务确认等待、释放后取得、返回 True 与最终归还；没有执行真实 Slime 生成。等待者次序和取消分支没有完整实验验证。


## 2026-10-26 · AsyncPacer.wait 与放行回调

- 固定 Slime `18868a79`：`async_utils.py:24–31` 为 wait，`33–42` 为 `_release`；调用处为 `sglang_rollout.py:332`，返回后接到 `333`。
- 本地实验从真实源码 AST 提取 AsyncPacer 类，记录子类只观察回调前后队列长度：130 个等待调用按 `[64, 64, 2]` 放行，全部 wait 返回 None，全部任务仍停在下游 Event，队列清空且 scheduled=False。没有模型、网络或沙箱运行，取消及实际调度延迟未测试。
- 语义参考为 Python 3.12 的 call_soon、call_later 与 Future.set_result 官方文档；实验解释器为 Python 3.12.3。
