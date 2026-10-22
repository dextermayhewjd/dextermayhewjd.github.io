# Slime 到 Dressage 的阅读顺序

不用读完整个 slime 再读 Dressage。先吃透一条 Agent 执行与评测链路，再看 Dressage 怎样把这些能力组织成可扩展框架。 这最贴近 JD 的重点。

slime 按下面顺序读：

| 顺序 | 代码入口 | 读完应该能回答 |
|---|---|---|
| 1. 数据契约 | types.py：Sample (third_party/slime/slime/utils/types.py:107) | 一条任务最后交付什么？token、mask、reward、状态各表示什么？ |
| 2. 单题生命周期 | coding_agent_rl/generate.py (third_party/slime/examples/coding_agent_rl/generate.py:203) | 谁准备环境、启动 Agent、评分、收集轨迹和清理资源？这是最重要的主线。 |
| 3. 执行器与沙箱 | harness/common.py (third_party/slime/slime/agent/harness/common.py)、Sandbox 协议 (third_party/slime/slime/agent/sandbox.py:28) | CLI 与任务怎样解耦？换 Claude/Codex、换沙箱分别改哪里？ |
| 4. 模型调用边界 | adapters/common.py (third_party/slime/slime/agent/adapters/common.py:187) | 一次请求如何进入模型、转换协议并记录结果？重点看 _run_turn、会话管理和 call_sglang_generate。 |
| 5. 轨迹与评估 | trajectory.py (third_party/slime/slime/agent/trajectory.py:345)、swe.py：run_evaluation (third_party/slime/examples/coding_agent_rl/swe.py:270) | 多轮怎样成为样本？历史变化如何分支？执行成功和任务得分为什么分开？ |
| 6. 批量与观测 | check_rollout.py (third_party/slime/examples/coding_agent_rl/check_rollout.py:24)、trace_utils.py (third_party/slime/slime/observability/trace_utils.py) | 怎样并发运行、保存结果，并追踪一次失败？ |
| 7. 训练衔接概览 | train.py (third_party/slime/train.py:13)、generate_and_rm (third_party/slime/slime/rollout/sglang_rollout.py:289) | rollout、reward、训练更新和评估如何连接？先理解数据流即可。 |

读主线时配合 CPU 端到端测试 (third_party/slime/tests/test_agent/test_agent_rollout_cpu.py)，看一个正常场景和一个失败场景。然后选 Search-R1 的循环 (third_party/slime/examples/search-r1/generate_with_search.py)作对照，理解哪些属于框架、哪些属于任务。

之后读 Dressage，重点放在分层、扩展和运行治理：

| 顺序 | 代码入口 | 重点理解 |
|---|---|---|
| 1. 环境能力抽象 | paddock/interface.py (/Users/dextermayhew/projects/Dressage/dressage/paddock/interface.py) | 共同生命周期与黑箱、白箱能力为什么分开？ |
| 2. 两种执行方式 | whitebox_agent.py (/Users/dextermayhew/projects/Dressage/dressage/rollout/generate/whitebox_agent.py)、blackbox_dispatch.py (/Users/dextermayhew/projects/Dressage/dressage/rollout/generate/blackbox_dispatch.py:116) | 自定义 Python loop 与 CLI Agent 怎样接入同一套框架？ |
| 3. CLI 差异隔离 | adapters/base.py (/Users/dextermayhew/projects/Dressage/blackbox_server/adapters/base.py:171)，再看 claude_code.py (/Users/dextermayhew/projects/Dressage/blackbox_server/adapters/claude_code.py:154) | 接口、配置编译、进程和协议差异分别放在哪里？ |
| 4. 运行与失败处理 | rollout_llm_proxy.py (/Users/dextermayhew/projects/Dressage/blackbox_server/proxy/rollout_llm_proxy.py)、failures.py (/Users/dextermayhew/projects/Dressage/dressage/paddock/blackbox/failures.py) | 请求归属、步数限制、失败分类、证据保存与收尾如何统一？ |
| 5. 上下文与轨迹 | session_manager.py (/Users/dextermayhew/projects/Dressage/dressage/proxy/session_manager.py:95)、trajectory_store.py (/Users/dextermayhew/projects/Dressage/dressage/proxy/trajectory_store.py:108) | 原始消息、规范化消息、会话分支和轨迹记录怎样关联？ |
| 6. 训练数据出口，选读 | convert_samples.py (/Users/dextermayhew/projects/Dressage/dressage/rollout/convert_samples.py:89) | 扩展框架产生的记录最终如何交回 slime？ |

阅读完成标准：你能画出“题集 → 执行器 → 模型与工具 → 轨迹 → 评分 → 结果”的链路，并解释各层为什么这样拆、失败由谁处理，以及我们复用了什么。

Megatron 算子、复杂权重同步和全部异步训练模式可以暂缓。先把上述链路讲透，对这个岗位更有价值。

---

记录说明：2026-10-22，按用户提供内容完整保存。文中的 `third_party/slime/`、`/Users/dextermayhew/projects/Dressage/` 路径与行号保留原样，本次未重新核对其对应源码版本。
