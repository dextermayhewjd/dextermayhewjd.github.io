# 01 · 一份黑盒 Agent 任务，怎样交回训练样本？

[本步入口](README.md) · [项目目标与接续](../../README.md) · [范围与核心骨架 skill](../../../../../.agents/skills/repo-reading-scope/SKILL.md)

## 1. 阅读目标

总目标是为混元 Agent 强化学习框架岗位建立工程能力。本步先理解单条黑盒 rollout 如何连接任务执行、生成记录和训练样本交接，为后续阅读模型调用、上下文管理、并发治理和评测接入建立定位骨架。

本步只回答：**给定一份任务，Dressage 怎样准备环境、交给 Agent 执行，再取回轨迹并转换成样本？**

当前范围从 `generate()` 收到输入开始，到正常路径返回 `list[Sample]`、安排环境回收结束。奖励计算、训练批次组织和模型参数更新属于后续交接，本步只知道它们位于下游。

## 2. 找到指挥官函数

源码入口：[blackbox_dispatch.py → generate()](/Users/dextermayhew/projects/Dressage/dressage/rollout/generate/blackbox_dispatch.py:116)。

源码基准：`3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；2026-10-23 静态核对。官方概览可对照 [docs/rollout.md 的 Blackbox Dispatch](/Users/dextermayhew/projects/Dressage/docs/rollout.md:82)，具体顺序与行为以该版本源码为准。

选择这个函数，是因为它接收一份任务，串联执行环境、黑盒 Agent 和 Proxy，最后交回训练样本。它组织一次任务的编排；Agent 内部的模型与工具循环由外部后端执行。

| 输入或对象 | 本步需要知道什么 |
| --- | --- |
| `sample` | 携带任务提示、标签及元数据的输入样本 |
| `args`、`sampling_params` | 这次执行使用的配置与采样参数 |
| `paddock` | 提供环境生命周期和 Agent 交互操作；本步按默认黑盒实现理解 |
| `proxy_client` | 用于访问记录模型生成过程的 Proxy 服务 |
| 返回的 `result` | 正常路径下，由轨迹分段转换出的 `list[Sample]` |

```text
blackbox_dispatch.py :: generate(args, sample, ...)                     L116
├─ paddock = get_paddock_from_env(...)                                  L221
│  └─ 取得沙箱调度器（负责 Docker/Bwrap 等隔离执行容器）
├─ state = await paddock.init(session_id, ...)                          L223
│  └─ 初始化并启动沙箱容器环境
├─ await paddock.register_agent(state, router_url=proxy_url(), ...)     L233
│  └─ 核心注入！将沙箱内 Agent 的 LLM API 地址强行指向本地 Proxy
├─ await proxy_client.register_session_context(session_id)              L255
│  └─ 开启监听：通知 Proxy 开始拦截录制该 session_id 的多轮模型流量
├─ await paddock.call_agent(state, messages=..., ...)                   L260
│  └─ 运行黑盒 Agent 进程（Agent 在沙箱中自主执行工具并多轮请求模型）
├─ trajectory = await proxy_client.read_trajectory(...)                 L305
│  └─ Agent 执行完毕退出，从 Proxy 提取完整的多轮交互轨迹数据
└─ result = multi_segment.expand_segments_to_samples(...)               L324
   └─ 将多轮轨迹切片转换为标准 RL 训练样本序列 (list[Sample])          L349
```

这里是核心函数调用树与源码定位图。具体模型请求会在沙箱内由 Agent 发出，跨 HTTP 边界经由 Proxy 转发与录制。当前先把输入任务、Proxy 服务和沙箱环境视为已就绪的上下文条件；遇到内部交接问题再下钻回查。

## 3. 给出真正干活的核心骨架

以下为教学裁剪：选择 `evaluation=False`、未取得预热环境、Agent 正常完成的路径。省略配置解析、检查、日志、请求上下文登记及异常恢复；保留主要交接与清理位置。命令执行阶段按配置运行，可以没有命令；`maybe_await` 是兼容可等待返回值的辅助层，本步保留调用形状而不展开内部。

```python
initialized = False
paddock = None

try:
    proxy_client = get_proxy_client()                   # 取得 Proxy 客户端
    paddock = get_paddock_from_env(...)                 # 取得黑盒交互对象

    state = await maybe_await(paddock.init(...))        # 准备环境，取得会话状态
    initialized = True

    await maybe_await(paddock.register_agent(...))      # 配置后端 Agent 与模型请求路由
    await execute_blackbox_cmds_for_stage(...)          # before_agent：前置命令

    call_payload = await maybe_await(
        paddock.call_agent(...)
    )                                                   # 发送任务，等待 Agent 执行结果
    agent_response = agent_response_text(...)           # 从执行结果提取回答文本

    await execute_blackbox_cmds_for_stage(...)          # after_agent：后置命令

    await proxy_client.finalize_session(...)            # 整理本次会话的生成记录
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []     # 取得轨迹分段

    result = multi_segment.expand_segments_to_samples(...)  # 分段转换为样本
    return result

finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)                 # 安排环境回收，不等待回收完成
```

骨架保留真实调用顺序；命令执行的两个位置分别对应源码中的 `before_agent` 与 `after_agent`。原实现还包含预热复用、提前停止、失败返回和取消处理，这里只展开选定的正常路径。`finally` 在函数退出时执行，但安排回收不等于远端环境已在返回前完成释放。

第一遍重点辨认两条结果通道：

```text
paddock.call_agent(...)
    → call_payload
    → agent_response：Agent 的回答文本

proxy_client.read_trajectory(...)
    → trajectory_payload
    → segments：Proxy 保存的生成轨迹

二者与输入 sample 一起参与样本构建
    → result：list[Sample]
```

它们来自同一次任务，但承担不同职责。这里先定位来源与去向，token、logprob、mask 如何记录和转换留待局部阅读。

**停止条件：**能借助骨架指出任务从哪里进入、在哪里执行、回答与轨迹分别从哪里取得、样本在哪里形成，以及退出时怎样安排回收。子函数内部机制可以明确留白；不以能背出代码为继续阅读的条件。

后续若研究“Agent 执行期间，Proxy 怎样获得生成记录”，就从 `paddock.call_agent()` 保留来路，定位一次模型请求的处理；读完回到 `finalize_session()`，连接轨迹整理。这是下一步候选，不预设已经开始阅读或掌握。

本步 scope 保存任务骨架，[04-flow.md](04-flow.md)保存实际讨论；`02`、`03` 暂不创建子函数卡片。后续选定局部问题时才建立函数记录，按 skill 限制一轮展开量并保留返回位置。
