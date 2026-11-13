> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# create_app.finalize_session（Proxy 服务端）

- 源码：[dressage/proxy/server.py:2751](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2751)，定义在 create_app 内的路由处理函数。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；本轮按正常路径简读，不代表掌握全部构建算法。

[客户端 finalize_session](../proxy_client.py/ProxyClient.finalize_session.md) → POST /session/finalize → **本路由** → 回复客户端 → 返回 generate。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 与后置命令结束，generate 经客户端请求 Proxy 收尾指定会话。
2. **具体内容**：取得此前记录的 session，在会话锁内构建轨迹记录并发布；移除活跃会话、缓存收尾响应，清理模型路由上下文与可选 hook 状态，返回摘要。
3. **建议构建的心智模型**：

   > 把执行期间积累的会话记录整理为可读取的轨迹，保存好以后结束活跃会话，再回复“已完成收尾”。

4. **调用代码**（客户端跨 HTTP 发送，不是直接调用 Python 函数）：

   ```python
   response = await self._client.post(
       f"{self._proxy_url}/session/finalize",
       json=payload,
       headers=self._headers(),
   )
   ```

## 本场景的输入与输出

输入正文包括 session_id，以及可选 instance_id、label。实际模型交互数据来自 Proxy 已有 session.steps；没有从本次 HTTP 正文重新上传完整对话或 CLI 输出。

正常返回 finalization_result：含 success、session_id、trajectory_id、instance_id、finalization_id、步数/轮数/分段数和构建模式信息。完整轨迹写到 trajectory_store，随后由 read_trajectory 获取；本次回复是摘要。

### 为什么 generate 没有直接调用“采集”？

采集确实发生在 generate 运行期间，主要在它等待 paddock.call_agent 返回时。generate 编排任务；Agent 在沙箱中运行；Dressage Proxy 作为独立 HTTP 服务处理模型请求，采集代码位于 Proxy 的请求处理路径中，并非 generate 的直接子调用。

此前 generate:233 注册 Agent 时传入 router_url=proxy_url()，下游据此配置模型请求去向。注册本身不是采集；它准备了请求能经过 Proxy 的路径。执行期间 Agent 的模型调用经沙箱内代理进入 Dressage Proxy，再转向模型后端，响应处理中记录 step。

```python
# 运行关系示意，箭头不是同一进程中的直接 Python 调用。
generate
  -> paddock.call_agent(...)  # generate 等待 Agent 完成
       # Agent 执行期间，每次模型调用走另一条 HTTP 路径：
       Agent -> 沙箱内代理 -> Dressage Proxy -> 模型后端
       # Proxy 在模型响应处理路径中调用 _record_step_atomically，记录 step。
  <- call_payload
  -> proxy_client.finalize_session(...)  # 整理此前记录的数据
  -> proxy_client.read_trajectory(...)   # 取回已发布轨迹
```

此前阅读主要沿“控制 Agent 并取回结果”的链路，模型请求与采集链只说明了职责，没有展开。这是阅读覆盖尚未补齐，不是 generate 期间没有发生采集。记录入口为 server.py:1939 的 _chat_completions_pipeline，其中 2479 行调用 _record_step_atomically；当前仅定位，不视为读完整个请求处理管线。

### 回查 call_agent：已有代理衔接，但采集实现在外部 Proxy

2026-11-08 用户要求检查“当时的call agent里面没有吗?”。实际有相关衔接，不能概括为整条 call_agent 链没有 Proxy：

- Paddock.call_agent（paddock.py:184）转交客户端；客户端 call_agent（client.py:97）提交消息并轮询结果，没有直接调用记录 step 的函数。
- 下游 ClaudeCodeAdapter.send_message（claude_code.py:355）调用本地 RolloutLLMProxy.open_turn，标记当前 turn；CLI 运行后在 384 行 drain_turn，等待在途代理请求收尾。
- Claude 环境中的 ANTHROPIC_BASE_URL 指向本地代理（claude_code.py:221），本地代理构造时接收上游 Proxy 地址和绑定标识（:624）；转发头带 X-Session-Id（rollout_llm_proxy.py:358 等）。
- 外部 Dressage Proxy 在 _chat_completions_pipeline 中调用 _record_step_atomically（server.py:2479），才是本次记录 step 的位置。

Step 006 的 ClaudeCodeAdapter.send_message 卡片已保存 open_turn/drain_turn/clear_turn，并明确当时未进入代理内部。因此缺少的是从本地代理到外部记录的这一段深入阅读，不是此前完全未接触 Proxy；旧步骤保持当时快照。

### 先接清：API 已经记录了，为什么还要 build？

**采集发生在模型 API 调用期间；finalize 使用已采集的数据，分段并构造成统一的轨迹记录。** 不是结束时才去拦截 API，也不是从 CLI stdout 还原轨迹。

```python
# 执行期间：每次模型交互取得结果后，记录一个 step。
# server.py:2479，经 _record_step_atomically / _record_step 交给 SessionManager。
await _record_step_atomically(session, ...)  # 消息、token IDs、logprobs、分支信息等。
# session_manager.py:561，保存到这次会话中。
session.steps.append(step)

# 收尾期间：finalize_session 读取已有 session.steps。
# 下面只示意 tito 分支的 lineage 部分，省略 timeline 记录与其他处理。
lineage_segments = _split_session_into_lineage_segments(session)
for segment_index, segment in enumerate(lineage_segments):
    records.append(_build_tito_lineage_segment_record(...))
trajectory_store.write_many(records)
```

例如一次任务有多次模型 API 调用，会留下多个 step。训练消费侧需要明确：哪些 token 属于同一段、各 token 的 logprob 是什么、哪些位置参与 loss，以及这段属于哪个任务/轨迹。请求期间已有部分 token/拼接信息，finalize 按构建模式组织为统一记录；不是这里凭空产生 logprob 或第一次完成所有加工。

**真正 build 的位置**都在 dressage/proxy/server.py：

- `_build_tito_lineage_segment_record:1509`：将同一分段中各 step 已记录的 concat_token_ids、concat_response_mask 等组合，构造 tokens、full_logprobs、full_loss_mask 与标识信息；检查数组长度关系。
- `_build_step_snapshot_record:1401`：从该段末尾 step 的 token 快照及响应 logprob 构造记录，区分 prompt 和 response 的 mask。
- `finalize_session:2797` 附近：根据 token_build_mode 选择分段和构建路径；TITO 模式同时建立 lineage 和 timeline 视图；随后 write_many 发布。

当前先看清数据流：**模型 API → step → session.steps → 分段/构建 records → trajectory_store → 后续 read_trajectory。** 分段不保证整次任务只有一条记录，发生上下文改写或分支时尤其需要保留关系。

上述构建函数本轮只用来定位数据变化，不另建卡或自动深入算法；不是所有辅助函数都必须逐个读完。

### 本轮范围收敛：先看 StepRecord，再看怎样组成轨迹

用户明确同意暂不展开 API 采集链，当前缺口是 step 格式与最终组合方式。这里的 step 指一次模型生成记录 StepRecord，不是阅读目录的 Step 007，也不是一整次 Agent 任务。

| 要认识的数据 | StepRecord 中的字段示例 | 先回答什么 |
| --- | --- | --- |
| 本次交互 | prompt_token_ids、response_token_ids、response_logprobs、messages_snapshot | 模型看到了什么、生成了什么、留下了哪些数据 |
| 拼接材料 | concat_token_ids、concat_response_mask、concat_response_logprobs | TITO 构建器实际拿哪些已准备的数据来拼接 |
| 归属与边界 | step_id、turn_id、lineage_id、lineage_segment_boundary_before | 哪些 step 可以放在同一个分段，哪里需要断开 |

本步类卡：[StepRecord](../../../../classes/dressage/proxy/session_manager.py/StepRecord.md)，源码入口为 session_manager.py:95。不是现在背完其全部字段；版本、路由专家和性能字段先保留定位。

组合路线需按模式区分：TITO 路径先由 _split_session_into_lineage_segments（server.py:670）按 lineage 与边界组成若干 segment，然后 _build_tito_lineage_segment_record（:1509）在每个 segment 内拼接 concat_token_ids 和 concat_response_mask，并处理对应 logprob。不能把各次完整 prompt + response 不加区分地连接；后续请求通常携带旧历史，拼接材料在记录阶段已经准备。

Timeline 路径由 _split_session_into_timeline_segments（:709）每个 step 组成一段，再由 _build_step_snapshot_record（:1401）构建快照。TITO 模式还同时发布 timeline 视图，不能概括为无论配置怎样都把所有 step 合成一条。

当前已接触 StepRecord 和 Session 类卡，现进入 [_split_session_into_lineage_segments 函数卡](_split_session_into_lineage_segments.md)；读完分段再看 TITO 构建器。当前不重新钻入 HTTP 转发或原子记录的取消机制；这些入口未因此标记为已读。

### 1. 找到之前记录的会话

按 session_id 查缓存的收尾结果；已收尾且缓存仍有效时直接回复，避免重复发布。首次正常请求取得 session，然后在 session.request_lock 内再检查并进行后续处理。鉴权、缺失或空会话等失败分支首轮折叠。

### 2. 将会话整理成轨迹记录

```python
# 正常路径教学裁剪：省略调用参数、循环与检查，保留模式分支。
records = []
if token_build_mode == "tito":
    lineage_segments = _split_session_into_lineage_segments(session)
    timeline_segments = _split_session_into_timeline_segments(session)
    ...  # 遍历分段，分别用 _build_tito_lineage_segment_record 和
         # _build_step_snapshot_record 构建记录，追加到 records。
else:
    timeline_segments = _split_session_into_timeline_segments(session)
    ...  # 遍历分段，用 _build_step_snapshot_record 追加记录。
```

当前只需知道：会话里积累的模型交互会被整理成一批 records，而不是简单把原 session 原样返回。模式在 Proxy 启动时配置，本次请求不选择模式。TITO 与 snapshot 的分段/构建内部留待相关问题，不在此下钻。

<a id="publish-and-return"></a>

### 3. 从构建器返回，发布轨迹，再结束活跃会话

**当前返回位置：** `_build_tito_lineage_segment_record` 返回的一个 record 已由 `records.append(...)` 收下。finalize 会处理剩余的 lineage 段；TITO 模式还会构建 timeline 视图，此处沿用职责定位，不重复进入该构建器。随后给记录加 finalization 标记、组织回复摘要。

等本批 records 都准备好，才走到下面几行。保留真实执行顺序，省略记录标记、摘要字典与一致性检查：

```python
trajectory_store.write_many(records)  # 先发布完整的一批轨迹记录。
finalized = session_manager.finalize_session(
    session_id,
    result=finalization_result,       # 移除活跃会话，并缓存收尾摘要。
)
await engine_rebalancer.finalize_session(session_id)  # 移除该会话的模型路由上下文。
```

write_many 先把字典转换为 TrajectorySegment，校验这一批记录，再发布到 store。当前默认 TrajectoryStore 使用内存索引 `_by_trajectory` 和 `_by_instance`，不能把此处 write 理解成已经持久化到磁盘；传输引用模式的底层数据位置不在本轮展开。此处只看存储接口职责，不逐个进入它的辅助函数。

这个先后顺序重要：轨迹发布完成后，才从活跃会话表移除 session；轨迹仍保留在另一份存储中供后续读取。这里不是销毁 sandbox，也没有在本函数计算奖励或生成 Slime Sample。

### 4. 回复摘要，返回客户端

锁外如有 tool_call_hook_chain，则清掉该会话对应的 hook 状态，最后 return finalization_result。客户端解析该回复，返回 generate；generate 没有保存摘要字典，而是继续 context_owned = False，再调用 read_trajectory。

本轮接清发布和回复。读完返回 ProxyClient.finalize_session 的 response.json()，然后回到 generate:304 的 context_owned 赋值处；之后才进入 read_trajectory，不把收尾摘要当作完整轨迹。

## 我的直接表述（原话）

> 好的那么简单看一下吧
> 这里收尾的过程中到底做了什么

本轮为简读请求，尚无对服务端收尾机制的个人复述。

后续明确疑问（节选）：

> 这里是怎么把绘画记录整理为可读取的轨迹呢?
> 不是应该在api进行拦截吗?
> 这里是到底是在哪里buil 这个trajectory的呢?

本轮补齐 API 采集与 finalize 构建的时机、数据和源码位置；仍未将解释写作个人已理解。

## 尚不清楚

- TITO/snapshot 怎样构建具体 token、mask 等字段，当前未深入。
- 已发布轨迹如何被 read_trajectory 选择与取走，尚未展开。
- 异常和外部取消下的完整一致性边界，本轮未验证。

<details>
<summary>完整源码与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。只做静态核对，未运行网络请求、模型或轨迹构建实验。

辅助依据：session_manager.py:595 移除活跃会话并缓存结果；rebalancing/scheduler.py:2013 移除会话路由状态。这两处仅用于核对职责，不另建函数卡。

```python
@app.post("/session/finalize")
async def finalize_session(request: Request):
    _check_auth(request)
    body = await request.json()
    session_id = body["session_id"]
    instance_id = body.get("instance_id")
    label = body.get("label")
    if (
        "token_build_mode" in body
        or "token_build_modes" in body
        or "trajectory_build_mode" in body
        or "trajectory_build_modes" in body
    ):
        raise HTTPException(
            status_code=400,
            detail="token_build_mode is configured at proxy startup",
        )

    cached_result = session_manager.get_finalization_result(session_id)
    if cached_result is not None:
        return cached_result

    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    async with session.request_lock:
        # A concurrent duplicate may have waited on this same lock.  The
        # cached response makes finalize idempotent without writing the
        # trajectory a second time.
        cached_result = session_manager.get_finalization_result(session_id)
        if cached_result is not None:
            return cached_result
        if session_manager.get_session(session_id) is not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found",
            )
        if not session.steps:
            raise HTTPException(status_code=400, detail="Session has no turns")

        effective_instance_id = instance_id or session.instance_id
        trajectory_id = session.session_id
        finalization_id = uuid.uuid4().hex
        trajectory_ref = (
            transfer_queue_runtime.trajectory_ref(session)
            if transfer_queue_runtime is not None
            else None
        )
        records: list[dict[str, Any]] = []
        if token_build_mode == "tito":
            lineage_segments = _split_session_into_lineage_segments(session)
            timeline_segments = _split_session_into_timeline_segments(session)
            for segment_index, segment in enumerate(lineage_segments):
                records.append(
                    _build_tito_lineage_segment_record(
                        session=session,
                        trajectory_id=trajectory_id,
                        segment=segment,
                        segment_index=segment_index,
                        segment_count=len(lineage_segments),
                        instance_id=effective_instance_id,
                        label=label,
                    )
                )
            for segment_index, segment in enumerate(timeline_segments):
                records.append(
                    _build_step_snapshot_record(
                        session=session,
                        trajectory_id=trajectory_id,
                        segment=segment,
                        segment_index=segment_index,
                        segment_count=len(timeline_segments),
                        instance_id=effective_instance_id,
                        label=label,
                        token_build_mode_for_record="tito",
                    )
                )
            segment_count = len(lineage_segments)
            timeline_segment_count = len(timeline_segments)
        else:
            timeline_segments = _split_session_into_timeline_segments(session)
            for segment_index, segment in enumerate(timeline_segments):
                records.append(
                    _build_step_snapshot_record(
                        session=session,
                        trajectory_id=trajectory_id,
                        segment=segment,
                        segment_index=segment_index,
                        segment_count=len(timeline_segments),
                        instance_id=effective_instance_id,
                        label=label,
                        token_build_mode_for_record="snapshot",
                    )
                )
            segment_count = len(timeline_segments)
            timeline_segment_count = len(timeline_segments)

        for record in records:
            extra_info = dict(record.get("extra_info") or {})
            extra_info.update(
                {
                    "finalization_complete": True,
                    "finalization_id": finalization_id,
                }
            )
            record["extra_info"] = extra_info
        finalization_result = {
            "success": True,
            "session_id": session_id,
            "trajectory_id": trajectory_id,
            "instance_id": effective_instance_id,
            "finalization_id": finalization_id,
            "num_steps": len(session.steps),
            "num_turns": len(session.turn_ids),
            "num_segments": segment_count,
            "num_timeline_segments": timeline_segment_count,
            "history_rewritten": session.history_rewritten,
            "token_build_mode": token_build_mode,
            "token_build_model": token_build_model,
            "record_token_versions": record_token_versions,
            "mask_nonlast_version_tokens": mask_nonlast_version_tokens,
        }
        if trajectory_ref is not None:
            finalization_result["tq_trajectory_ref"] = trajectory_ref.to_dict()

        # Record conversion validates every item before write_many enters
        # its one-lock commit.  The active Session is removed only after
        # the complete trajectory batch has been published.
        trajectory_store.write_many(records)
        finalized = session_manager.finalize_session(
            session_id,
            result=finalization_result,
        )
        if finalized is not session:  # defensive; request_lock owns finalize
            raise RuntimeError("session changed during atomic finalization")

        await engine_rebalancer.finalize_session(session_id)

    if tool_call_hook_chain is not None:
        purged = tool_call_hook_chain.purge_session(session_id)
        if purged:
            finalization_result["tool_call_hook_keys_purged"] = purged

    return finalization_result
```

[本轮形成过程](../../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md#proxy-finalize-server)。

</details>
