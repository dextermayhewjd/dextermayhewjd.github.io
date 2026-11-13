# 01 · Dressage Step 007：Agent 执行后怎样取得 Proxy 轨迹

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一阶段范围](../step-006-agent-execution/01-scope.md) · [后续规划](../../../../references/topics-and-step-scopes-after-step006.md)

> 状态：2026-11-08，本步按正常主线首轮收束，停在 generate 取得 trajectory_payload。用户选择不再深入 pop_trajectory；保留完整导航与未读边界，见[任务链路总结](05-task-flow.md)。

[本步函数记录](02-short-term-memory/overview.md) · [前序累计](03-long-term-memory/overview.md) · [形成过程](04-flow.md)

## 1. 阅读目标

**接住已经结束的 Agent 调用，弄清后置命令、Proxy 会话收尾和轨迹读取怎样依次交接。**

1. 区分 Agent 的 call_payload 与 Proxy 保存的 trajectory_payload。
2. 看清两个 Proxy HTTP 请求各自交出什么，以及 session_id 如何关联它们。
3. 知道 drain=True 影响哪份记录，不将它理解为重新运行 Agent。

## 2. 指挥官、入口与停止位置

指挥官仍是 [blackbox_dispatch.generate:293–309](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L293)。先从 after_agent 的调用位置接续；命令执行机制复用 Step 005，首个新的主要入口是 [ProxyClient.finalize_session](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L64)。

进入时应已有 Paddock、state、会话/任务标识、命令计划，以及 Step 006 交回的调用结果。这里描述入口条件，不表示已经完成本步阅读。

**停止在 generate:309：trajectory_payload 已取得，尚未进入轨迹日志与 Sample 转换。** 本轮选成功调用、正常会话收尾和按 trajectory_id 读取的路径。服务端 session 缺失、空轨迹及收尾失败只定位出口；完整恢复留到 Step 009。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在原生任务中的位置

下面是正常路径的教学骨架，省略参数、日志和大部分失败包装。它保留整个原生任务的位置；Step 编号表示阅读范围，不表示并发执行顺序。

```python
session_id = ensure_blackbox_session_id(...)
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client(...)
    handle = await claim_prewarm(...)
    ...  # 此图选择预热未命中路径，身份更新等细节折叠。
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))
    initialized = True

    await maybe_await(paddock.register_agent(...))
    await execute_blackbox_cmds_for_stage(...)  # before_agent
    ...  # 按接口能力登记 Proxy 会话，记录 context_owned。
    call_payload = await maybe_await(paddock.call_agent(...))
    agent_response = agent_response_text(call_payload)
    ...  # Step 006：执行结果的结构化失败检查。

    # Step 007（本步）：执行后置命令，给 Proxy 会话收尾并取得轨迹。
    await execute_blackbox_cmds_for_stage(...)  # after_agent
    await proxy_client.finalize_session(...)
    context_owned = False
    trajectory_payload = await proxy_client.read_trajectory(...)

    # Step 008：从轨迹中取段，形成 Sample 列表。
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result  # return 交回调用方之前仍要执行 finally。
finally:
    # Step 009：处理尚未释放的会话责任，并安排环境回收。
    try:
        if context_owned:
            await _discard_session_context(...)
    finally:
        if initialized and paddock is not None:
            schedule_terminate_paddock(...)
```

普通失败和取消的分支在 Step 009 单独定位；此图不是可直接执行的完整函数。

<a id="reading-navigation"></a>

### 3.2 本步调用骨架与阅读顺序

**采集的来源提醒：** 在 Step 006 的 `await paddock.call_agent(...)` 期间，Agent 的模型请求经沙箱内代理到 Dressage Proxy，由其请求处理路径记录进 `session.steps`。此前我们沿 Agent 控制与结果返回链阅读，尚未展开这条模型请求链；用户现明确暂不回查该链，优先看 StepRecord 格式和轨迹组合。当前 finalize 使用这些已有记录；它不是启动采集。此处只补跨服务关系，不自动开启整个 Proxy 管线的阅读。

本步正常路径节选；保留本次问题相关的阶段名、标识与 drain 参数，其余参数省略：

```python
await execute_blackbox_cmds_for_stage(..., stage="after_agent")
await proxy_client.finalize_session(...)
context_owned = False  # 记录本次会话上下文的清理责任变化。
trajectory_payload = await proxy_client.read_trajectory(
    trajectory_id=session_id,
    instance_id=instance_id,
    drain=True,
)
```

这里有两个不同的请求目标：**命令执行发往沙箱内 BlackboxServer；finalize_session 和 read_trajectory 发往 Dressage Proxy。**

下面是执行关系示意，使用 Python 高亮显示中文注释，并非可执行代码。服务端路由与 BlackboxServer.execute_cmd 已展开；shell 内部当前已展开启动、输出等待与超时配合；进程组终止内部暂不展开。

```python
# 后置命令：外层顺序执行，每次等待一条命令处理完成。
execute_blackbox_cmds_for_stage  # 选择 after_agent 计划
  -> _execute_blackbox_cmd  # 取出一条配置命令，调用 Paddock
       -> BlackboxAgentPaddock.execute_cmd  # 依据 state 找到已有沙箱入口
            -> BlackboxServerClient.execute_cmd  # 组织正文并发送请求
                 == HTTP POST ==> /v1/sessions/{session_id}/execute_cmd
                      -> api.sessions.execute_cmd  # 沙箱内服务接收
                           -> BlackboxServer.execute_cmd
                                -> execute_shell_command  # /bin/sh -lc cmd
                 <== HTTP ==  # 服务端等待命令结果，再返回响应
            <- 结果字典  # 客户端检查 HTTP 状态、解析 JSON
       <- cmd_result  # 经 Paddock 返回上层 hook
       # hook 接着记录结果，并判断 required 命令是否失败。
  <- None  # 单条处理正常返回后，循环才继续下一条
# 全部命令处理完毕，返回 generate；异常则退出正常路径。
```

命令路径中，客户端等待这次 HTTP 请求返回执行结果；不套用 Step 006 的“先收到 HTTP 202，再轮询 turn”流程。请求成功与命令成功仍需区分：命令退出码和超时标记由上层处理。

**当前展开：Proxy 怎样把记录整理成轨迹。** 下面是执行关系示意，不是可直接运行的代码；选择 TITO 的 lineage 构建路径，省略其他视图、检查与清理细节。

```python
# generate：Agent 和后置命令结束，请 Proxy 收尾。
await proxy_client.finalize_session(...)
    # 经 HTTP：POST /session/finalize
    -> Proxy 服务端 finalize_session
         # 找到执行期间已经积累的会话记录。
         session = session_manager.get_session(session_id)

         # 按历史路径和边界，把模型交互记录分段。
         lineage_segments = _split_session_into_lineage_segments(session)

         # 遍历各段，分别构建轨迹记录并加入 records。
         _build_tito_lineage_segment_record(...)

         # 保存轨迹，随后结束活跃会话并回复客户端。
         trajectory_store.write_many(records)
    <- 收尾摘要  # 经客户端返回 generate；此处尚未取回完整轨迹。

# 回到 generate：收尾请求正常完成后继续。
context_owned = False
trajectory_payload = await proxy_client.read_trajectory(...)

# Step 007 到取得 trajectory_payload 为止。
# 轨迹转换成 Sample 属于 Step 008。
```

**为什么先回查 Session 和 StepRecord？** 进入 `_split_session_into_lineage_segments(session)`，需要先看清它接收的 `session`：

```text
Session：本次执行会话的总记录
  ├─ steps：多条 StepRecord，每条保存一次模型生成
  └─ lineages：各条历史路径的信息
```

每条 `StepRecord.lineage_id` 对应一条 `Lineage.id`。**Session、StepRecord 是分段函数使用的数据，不是依次执行的两个函数。** 字段解释分别见 [Session 类卡](02-short-term-memory/classes/dressage/proxy/session_manager.py/Session.md)与 [StepRecord 类卡](02-short-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。

**本步已首轮收束：** 从服务端 trajectory_read 回复，经客户端 response.json() 返回 generate 的 trajectory_payload。当前复习入口为 [任务链路总结](05-task-flow.md)；下面保留实际读过的路径，pop_trajectory 内部仍未逐段阅读。

**停止位置与下一步边界：** generate:305–309 接住整个回复字典，其中 data 是轨迹段列表。转换成 Slime Sample 属于 Step 008，尚未展开。


<a id="reading-sequence"></a>

**上方图表达执行关系，下表数字只表示阅读顺序。** 返回同一函数的不同位置单列一行，仍使用原函数卡；源码导航或候选入口不表示已经阅读。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. after_agent 阶段命令执行 | [generate:293 的本步片段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#after-agent) → [execute_blackbox_cmds_for_stage](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md) | 看 stage 怎样选择命令；从循环中的 await 进入下一行 |
| 2. _execute_blackbox_cmd：发送一条命令 | 外层传入一个 command → [本函数第 1 段](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md#send-one-command) | getattr 取得当前 Paddock 的方法；从 execute_cmd 调用处进入下一行，记住返回值由 cmd_result 接住 |
| 3. BlackboxAgentPaddock.execute_cmd | 直接调用：[本步函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.execute_cmd.md) | 解析 state、查找 lease/endpoint，再委派客户端；下一行进入客户端 |
| 4. BlackboxServerClient.execute_cmd | Paddock 的委派 → [本步函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.execute_cmd.md) | 看请求正文和 POST 地址；本轮沿 HTTP 进入下一行的服务端路由，返回后再接 HTTP 检查与 JSON 解析 |
| 5. api.sessions.execute_cmd | 跨 HTTP：客户端 POST → [服务端路由卡](02-short-term-memory/functions/blackbox_server/api/sessions.py/execute_cmd.md) | 取得 server，在 request_scope 内委派执行；从调用处进入下一行 |
| 6. BlackboxServer.execute_cmd | 路由的 await → [本步函数卡](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.execute_cmd.md) | 会话检查后，从锁内 execute_shell_command 进入下一行；记住返回值由 result 接住 |
| 7. execute_shell_command：结果返回段 | BlackboxServer.execute_cmd 的委派 → [本函数卡](02-short-term-memory/functions/blackbox_server/core/command.py/execute_shell_command.md#return-command-result) | 已看启动、等待和结果返回；移除进程登记、解码输出并构造 ExecuteCmdResult，返回下一行调用方的 result |
| 8. 返回 BlackboxServer.execute_cmd | shell 函数返回 ExecuteCmdResult → result 接住 | 更新会话时间，展开 result 字段构造 ExecuteCmdResponse，退出会话锁，再返回下一行的路由 |
| 9. 返回服务端路由，再跨 HTTP 返回客户端 | 路由的 response 接住结果，补 request_id 并返回；客户端 post 接住 HTTP 响应 | 回到客户端 execute_cmd 的 raise_for_status 与 response.json()；接着才逐层返回 Paddock 和上层 hook |
| 10. 返回 Paddock，再返回上层 hook | 客户端返回字典 → Paddock 的 return await → [_execute_blackbox_cmd 的 cmd_result](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md#send-one-command) | 接清命令结果到达哪个变量；Paddock 不追加 metadata，也不决定 required 失败策略 |
| 11. 返回 _execute_blackbox_cmd：记录结果 | 返回已有[函数卡：整理结果并记录](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md#record-command-result) | 结果记录已回看；用户选择首轮略过 required 失败分支，按正常路径返回，不重读中间返回层 |
| 12. 返回阶段循环，再返回 generate | 单条处理正常返回 → execute_blackbox_cmds_for_stage 的 for 循环 | 下一条命令才开始；全部处理结束后回到 generate:301，必需命令失败时则中止正常路径 |
| 13. ProxyClient.finalize_session | generate:301 → [本步函数卡](02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.finalize_session.md) | 看会话标识和可选资料怎样发往 Dressage Proxy，响应为收尾摘要；generate 未保存该字典，正常返回后到 context_owned。若要解释收尾内部，再进入下一行服务端 |
| 14. Proxy 服务端 finalize_session | 跨 HTTP：[本步函数卡](02-short-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md) | 已简读收尾编排；在分段调用处暂时回查输入，按下方顺序看 StepRecord、Session，再返回分段和构建；API 采集链暂不展开，完成后回到发布和回复 |
| 15. 回查数据：StepRecord | 从 finalize 的 session.steps → [本步类卡](02-short-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md) | 已接触一条模型生成记录的格式；字段详见类卡，随后用 Session 接清这些记录的归属，不重读 API 采集链 |
| 16. 回查分段输入：Session | 从分段函数参数回查 [Session 类卡](02-short-term-memory/classes/dressage/proxy/session_manager.py/Session.md) | 先在类卡中看 get_session 如何按 ID 查回原对象，再看 Session 的 steps、lineages 和归属关系；看清输入后回到下一行分段函数 |
| 17. _split_session_into_lineage_segments | 从类卡回到 finalize 的分段调用 → [本步函数卡](02-short-term-memory/functions/dressage/proxy/server.py/_split_session_into_lineage_segments.md#group-and-split) | 按路径筛选 StepRecord，再按边界保存各段；局部 flush_segment 就地理解，返回 lineage_segments 后再看下一行构建器 |
| 18. _build_tito_lineage_segment_record：结果组装段 | 分段函数返回 finalize 的循环 → [本步函数卡](02-short-term-memory/functions/dressage/proxy/server.py/create_app._build_tito_lineage_segment_record.md#assemble-record) | 接着看 extra_info、logprob 对齐和 record 字典；返回 finalize 的 records.append，版本及专家路由细节暂略 |
| 19. 返回 Proxy 服务端 finalize_session 第 3–4 段 | 构建器返回 records.append → [第 14 项同一张服务端卡：第 3 段起](02-short-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md#publish-and-return) | 本批 records 齐备后 write_many 发布；结束活跃会话、清理上下文、回复摘要，经客户端返回下一行 generate。timeline 视图和 store 内部先按接口理解 |
| 20. 返回 generate 的 context_owned | generate:304 | 说明标记为何在 finalize 正常返回后更新；不将该赋值理解为删除沙箱 |
| 21. ProxyClient.read_trajectory | generate:305 → [本步函数卡](02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md) | 看当前 trajectory_id=session_id、instance_id、drain=True 怎样组成请求，返回整个字典给 trajectory_payload；按需进入下一行路由确认读取/移除 |
| 22. Proxy 服务端 trajectory_read | 客户端 POST /trajectory/read → [本步函数卡](02-short-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md) | 解析轨迹 ID 和 drain，当前委派 pop_trajectory 取出并移除；回复 data 等字段后，经客户端返回下一行 generate。存储方法先按合同理解 |
| <a id="current-reading"></a>**23. 返回 generate · 本步停止位置** | 客户端将正文返回给 trajectory_payload | 定位 data、success、drained 等本次返回字段；到 309 行停，下一个范围才处理 segments |

本步不展开全部 TITO/上下文压缩、模型协议或轨迹落盘格式。只有记录来路阻碍本次交接时，才回查一层必要函数。

<details>
<summary>源码与证据边界</summary>

- 固定版本：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 主要位置：generate:293–309；ProxyClient:64–82、115–147；Proxy 服务端:2751、2923 行起。
- 本步已开始源码带读；未运行 Agent、模型、HTTP 请求或清理实验，不表示相关函数已经掌握。
- 已继承前一步 03 + 02，并只为实际使用的函数保存本步记录；Proxy 服务端与客户端 read_trajectory 已展开；存储内部和其他未读路径保留源码定位，首轮总结见 05-task-flow.md。

</details>
