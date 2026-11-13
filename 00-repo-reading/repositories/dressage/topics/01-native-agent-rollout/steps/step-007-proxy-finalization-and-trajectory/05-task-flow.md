# 05 · Step 007：后置命令、Proxy 收尾与轨迹取回

> 接住已完成的 Agent 调用，执行配置的后置命令；Proxy 将已有模型交互记录构造成轨迹，结束活跃会话；generate 再取回轨迹段，得到 trajectory_payload。

[本步 scope](01-scope.md) · [函数与类记录](02-short-term-memory/overview.md) · [形成过程](04-flow.md#close-step007) · [项目唯一进度](../../../../README.md)

## 1. 本步在任务中的位置

进入时已取得 call_payload，并有 Paddock、state、session_id、instance_id 和命令计划。模型交互在 Agent 运行期间由 Proxy 记录；本步不重新运行 Agent，也不从 CLI stdout 重建训练轨迹。

本轮沿正常路径阅读，轨迹构建以 TITO lineage 路径为重点。终点是 generate:305–309 的 trajectory_payload；Sample 转换属于 Step 008，外层资源清理属于 Step 009。

## 2. 已读部分怎样交接

下面用 Python 高亮显示中文注释。箭头表示调用或 HTTP 交接，是关系示意而非可执行代码。

```python
# generate:293–309 的三个直接阶段。
generate
  -> execute_blackbox_cmds_for_stage(..., stage="after_agent")
       -> _execute_blackbox_cmd  # 每次处理一条配置命令。
            -> BlackboxAgentPaddock.execute_cmd  # 找到已有沙箱入口。
                 -> BlackboxServerClient.execute_cmd
                      == HTTP ==> 沙箱 api.sessions.execute_cmd
                                   -> BlackboxServer.execute_cmd
                                        -> execute_shell_command
                                        # 启动 shell，收集输出，等待结束或处理超时。
                                   <- ExecuteCmdResult 封装为 ExecuteCmdResponse
                      <== HTTP == 客户端解析结果
            <- cmd_result  # 经过 Paddock 返回。
            # 整理 result_summary，追加 metadata["execute_cmds"]。
       # 一条返回后再执行下一条；无配置则直接返回。

  -> ProxyClient.finalize_session
       == HTTP ==> Dressage Proxy 的 finalize_session
                    # 取得已有 Session，其中 steps 保存多个 StepRecord。
                    -> _split_session_into_lineage_segments
                    <- lineage_segments  # 按路径归属及边界分段。
                    -> _build_tito_lineage_segment_record  # 每次处理一段。
                    <- record  # token、logprob、mask 与归属信息。
                    # TITO 还生成 timeline 视图，本轮仅作定位。
                    -> trajectory_store.write_many(records)
                    # 先发布轨迹，再移除活跃会话和模型路由上下文。
       <== HTTP == 收尾摘要  # generate 不保存此字典。
  # context_owned = False：不再承担这份会话上下文的清理责任。

  -> ProxyClient.read_trajectory(..., drain=True)
       == HTTP ==> Dressage Proxy 的 trajectory_read
                    -> trajectory_store.pop_trajectory  # 仅按接口职责理解。
                    <- data  # 轨迹段列表。
       <== HTTP == {success, mode, data, meta_info, drained}
  # trajectory_payload 接住整个字典，本步停在这里。
```

命令链入口：[阶段循环](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md)、[单条命令与记录](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md)、[shell 执行](02-short-term-memory/functions/blackbox_server/core/command.py/execute_shell_command.md)。

轨迹准备入口：[Session](02-short-term-memory/classes/dressage/proxy/session_manager.py/Session.md)、[StepRecord](02-short-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)、[分段](02-short-term-memory/functions/dressage/proxy/server.py/_split_session_into_lineage_segments.md)、[段记录构建](02-short-term-memory/functions/dressage/proxy/server.py/create_app._build_tito_lineage_segment_record.md)、[服务端收尾](02-short-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md)。

轨迹读取入口：[客户端](02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md)、[服务端路由](02-short-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。存储索引内部不属于本轮深入范围。

## 3. 本步结果的含义与去向

| 结果或变化 | 含义 |
| --- | --- |
| metadata["execute_cmds"] | 后置命令的配置与执行结果记录，不是模型训练轨迹 |
| 轨迹 records | 由已有 StepRecord 按路径和边界组织；同一 lineage 可以有多个 segment |
| context_owned=False | Proxy 正常收尾后，generate 不再承担该会话上下文的清理责任，不表示沙箱已被销毁 |
| trajectory_payload | HTTP 读取回复的整个字典；其中 data 才是轨迹段列表 |

轨迹段包含 tokens、full_logprobs、full_loss_mask、aligned_response_length 以及任务/轨迹/段标识；它还不是 Slime Sample。

当前 drain=True 会移除按轨迹与任务匹配的存储记录，避免完成的轨迹一直占用 Proxy 内存。默认 TITO 返回 lineage 视图，移除范围还包含该匹配集合中的其他视图。空结果会使 success=False，不会重新生成轨迹；本轮只核对语义，没有实际执行读取和删除。

## 4. 本步收束与后续衔接

2026-11-08 用户认为本步已足够，选择不再深入 pop_trajectory。按正常主线首轮收束，保留以下边界：

- pop_trajectory、write_many 的索引、锁与具体维护实现未逐段阅读。
- API 采集链只接清来源，未重读整个模型请求处理流程。
- TITO 的增量 token 准备、复杂分支回退、TransferQueue 和 timeline 构建未完整展开。
- required 失败分支按用户选择暂略；完整取消、重试及恢复不作已掌握结论。

下一步范围已经准备在 [Step 008 scope](../step-008-segments-to-samples/01-scope.md)：从 trajectory_payload 的 data 取段，交给 expand_segments_to_samples。当前未开始 Step 008，不提前创建新卡片或长期记忆快照。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 本步入口与终点：blackbox_dispatch.py:293–309。
- Proxy 构建、发布与读取：server.py:670、1509、2751、2923。
- 内容依据实际问答、已建函数/类卡片与静态源码核对。用户“大致理解”的反馈不扩大为全部机制掌握。
- 未执行真实 Agent、模型调用、沙箱命令或 Proxy 读写；文档检查不代替运行验证。

</details>
