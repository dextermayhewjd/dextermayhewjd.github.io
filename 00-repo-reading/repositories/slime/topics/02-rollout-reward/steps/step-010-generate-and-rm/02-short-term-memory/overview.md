# 02 · Step 010 的短期记忆

[本步范围](../01-scope.md) · [前序累计记忆](../03-long-term-memory/overview.md)

| 源码文件 | 函数或类记录 | 首次接触 | 个人表述状态 |
| --- | --- | --- | --- |
| `slime/rollout/sglang_rollout.py` | [generate_and_rm](functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) | Step 010，2026-10-25 正式展开 | 已表达获取 reward 并写回样本；补准筛选范围，批量评分卡已按用户指定展开，内部机制待反馈 |
| `slime/rollout/rm_hub/__init__.py` | [batched_async_rm](functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md) | Step 010 骨架已定位；2026-10-26 独立展开 | 已概括两条评分路径；函数加载、单样本自定义优先级及结果顺序待反馈 |
| `slime/rollout/sglang_rollout.py` | [_run_server_abort_generate](functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md) | Step 010，2026-10-26 从空卡展开 | 已初步概括控制与生成职责分离；计数及异常细节保留未知 |
| `slime/data/transport.py` | [inherit_queue_context](functions/slime/data/transport.py/inherit_queue_context.md) | Step 010 骨架已出现；2026-10-26 独立展开 | 已表达凭证与结果归属，粗略认可解释并转入 group_rm；字段细节仍可回查 |
| `slime/rollout/sample_hooks.py` | [apply_rollout_sample_hooks](functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md) | Step 010，2026-10-26 进入第三部分 | 已将第三部分概括为二次处理；hook 内部机制尚待反馈 |
| `slime/utils/async_utils.py` | [AsyncPacer.wait](functions/slime/utils/async_utils.py/AsyncPacer.wait.md) | 2026-10-25 讨论用途；2026-10-26 从空卡展开 | 已表达先建 Future，追问入队、共享队列与批次；校准待反馈 |
| `Lib/asyncio/locks.py`（CPython 3.12.3） | [asyncio.Semaphore.acquire](functions/Lib/asyncio/locks.py/Semaphore.acquire.md) | Step 010，2026-10-25 讨论用途；2026-10-26 独立建卡 | 保留此前初步提问；本轮机制解释待反馈 |
| `slime/rollout/sglang_rollout.py` | [GenerateState.dp_rank_context](functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md) | Step 010 控制骨架；2026-10-25 展开 | 已联系 DP 计数与进入退出分段，要求纳入 yield/try/finally 细化；选择规则及完整协议待展开 |
| `slime/utils/types.py` | [Sample（类）](classes/slime/utils/types.py/Sample.md) | 前一主题已接触；Step 010 建立独立类卡 | 已初步概括为单份样本的状态；数据范围补充与字段机制待核对 |
| `slime/rollout/sglang_rollout.py` | [GenerateState（类）](classes/slime/rollout/sglang_rollout.py/GenerateState.md) | Step 010 的执行骨架；2026-10-25 建卡 | 已初步概括为群体状态；进程内共享范围的校准待反馈 |
| `slime/agent/harness/common.py` | [HarnessContext（类，对照调取）](classes/slime/agent/harness/common.py/HarnessContext.md) | 沿用前序类卡的记录 | 本轮只比较数据对象与上下文管理器，原话与认识时间保留 |

函数卡片保存入口模型，类卡片保存对象职责、当前字段与用法；个人认识按真实反馈增量补充。[入口形成过程](../../step-010-generate-and-rm/04-flow.md#topic-two-start) · [两张类卡的建立](../../step-010-generate-and-rm/04-flow.md#sample-state-class-cards)。

## 待阅读的空白函数卡

2026-10-26 按用户要求先创建文件，暂不填写正文。其中 AsyncPacer.wait 和 _run_server_abort_generate 已于同日按用户指定展开并移入上方索引；以下剩余文件仅供定位，尚未展开，不代表已读或已掌握；实际阅读时再按函数卡格式补充。`acquire`、`dp_rank_context` 与父函数已有的内容保持原样。

| 对应部分 | 空白卡入口 | 状态 |
| --- | --- | --- |
| 名额归还 | [asyncio.Semaphore.release](functions/Lib/asyncio/locks.py/Semaphore.release.md) | 仅占位，待阅读时填写 |
| 加载生成函数 | [load_function](functions/slime/utils/misc.py/load_function.md) | 仅占位，待阅读时填写 |
| 本场景的生成实现 | [Coding Agent generate](functions/examples/coding_agent_rl/generate.py/generate.md) | 仅占位，待阅读时填写 |

`state.aborted` 是字段判断，继续保留在 GenerateState 类卡与 generate_and_rm 父卡，不创建虚构的函数文件。生成路径选择及各调用的组合仍由父卡承接；当前场景只预留服务端等待包装，不扩展另一种取消分支。
