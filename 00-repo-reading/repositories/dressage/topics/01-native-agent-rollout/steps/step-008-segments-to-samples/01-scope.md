# 01 · Dressage Step 008：轨迹段怎样成为 Sample 列表

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一阶段范围](../step-007-proxy-finalization-and-trajectory/01-scope.md) · [后续规划](../../../../references/topics-and-step-scopes-after-step006.md)

> 状态：2026-11-08 正常主线首轮收束，result 已接住 Sample 列表；扩展路径仍保留未知，见[任务链路总结](05-task-flow.md)。

## 1. 阅读目标

**把上一阶段取得的轨迹段接成 Sample 列表，保留执行归属与训练字段的对应关系。**

1. 区分一条原始任务轨迹、轨迹中的多个段和返回的多个 Sample。
2. 对上一份人工小样本，看 token、mask、logprob 和 response_length 怎样进入 Sample。
3. 定位各段归属和奖励锚点，不把分段直接当作多次独立答题。

## 2. 指挥官、入口与停止位置

外层入口是 [generate:322–331](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L322)，本步主要编排函数为 [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118)。进入时应已有 trajectory_payload、原始 sample 模板、args、agent_response 和会话/任务标识。

选一条含两个有效段的轨迹作为后续带读样例；这里仅约定样例形状，不预填真实运行值。样本构造从空轨迹/重复段索引的检查处保留必要边界。

**停止在 generate:331：result 接住 Sample 列表。** 后面的样本日志仅作定位；349 行的 return 真正交出结果前还要走 finally，其责任由 Step 009 处理。本步不训练模型、不计算完整 RL loss。

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

    # Step 007：执行后置命令，给 Proxy 会话收尾并取得轨迹。
    await execute_blackbox_cmds_for_stage(...)  # after_agent
    await proxy_client.finalize_session(...)
    context_owned = False
    trajectory_payload = await proxy_client.read_trajectory(...)

    # Step 008（本步）：从轨迹中取段，形成 Sample 列表。
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

**本步首轮已收束：** 复习入口为 [05-task-flow](05-task-flow.md)。下表保留实际阅读顺序和返回点；最终 result 是 Sample 列表，接下来的 return/finally 在 Step 009 展开。

以下为正常路径教学裁剪；排序、校验和多余元数据字段先折叠，保留真实写入与返回关系：

```python
# generate 中接住轨迹，取得其 data。
segments = trajectory_payload.get("data") or []
result = multi_segment.expand_segments_to_samples(...)

# expand_segments_to_samples 内部：每段生成一份样本。
out = []
for i, segment in enumerate(sorted_segments):
    sample = copy.deepcopy(template_sample)
    sample.rollout_id = rollout_id
    write_sample_from_segment(...)  # 修改这份 sample，填入该段训练字段。
    sample.metadata["parent_traj_id"] = sid
    sample.metadata["segment_index"] = int(segment.get("segment_index", 0))
    if i != last_idx:
        sample.reward = 0.0
    out.append(sample)
return out  # 回到 generate 的 result；这里还未退出外层 finally。
```

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 取 segments 并传入模板 | [generate:322–331 本步卡](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#extract-segments) | 先看从 data 取段、原 sample 作为模板；本轮停在转换调用入口，后续再进入下一行 |
| 2. expand_segments_to_samples | generate 的委派 → [本步函数卡](02-short-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md#prepare-and-copy) | 对齐段排序、身份信息、每段 deepcopy 与写入调用；当前停在 write_sample_from_segment 的委派，下一处再展开字段转换 |
| 3. write_sample_from_segment：主干拆解 | 外层复制 sample 后委派 → [本步函数卡](02-short-term-memory/functions/dressage/rollout/artifacts/samples.py/write_sample_from_segment.md#mainline) | 本函数内依次接清数组合同、response_start 与切片、文本/来源、状态与原地返回；长度/版本/传输/专家分支先知道触发和影响，逐段读完再返回外层 |
| 4. 返回 expand_segments_to_samples 尾段 | write_sample_from_segment 返回 → [外层函数卡第 3 段](02-short-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md#return-to-segment-loop) | 看 parent_traj_id、segment_index、非末段 reward=0 与 out.append；完整奖励算法不下钻，return out 后进入下一行 generate |
| <a id="current-reading"></a>**5. 返回 generate · 本步停止位置** | out → result | 列出本次返回列表的形状与字段关系；到 331 行停，return/finally 留给 Step 009 |

本轮只选当前配置的一条数组构建路径。TransferQueue、不同 token 版本、复杂截断和完整奖励归一化先保留位置；若当前样例涉及截断，则必须同时核对各数组长度，不能只看 tokens。

<details>
<summary>源码与证据边界</summary>

- 固定版本：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 主要位置：generate:322–331；multi_segment.py:118–192；artifacts/samples.py:291 行起。奖励后处理的独立入口只作定位，本步不提前展开。
- 本步已开始静态阅读，未运行 Agent、模型、HTTP 请求或转换实验，不表示相关函数已经读懂。
- 已建立前序继承、当前 generate 片段与形成过程；未读函数不提前建卡，已生成本步任务链路总结，未将可选路径标为掌握。

</details>
