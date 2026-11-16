> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# create_app.trajectory_read（Proxy 服务端）

- 源码：[server.py:2923–2964](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2923)。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；仅看当前指定轨迹的分支。

[客户端 read_trajectory](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md) → POST /trajectory/read → **本路由**。

**当前实际路径与阅读位置**（调用和返回示意，不是可执行代码）：

```python
generate
  -> ProxyClient.read_trajectory     # 已看：发送请求。
  == HTTP POST /trajectory/read ==>
  -> Proxy 服务端 trajectory_read   # 当前卡片，已看：解析条件、选择操作。
       -> TrajectoryStore.pop_trajectory  # 尚未逐段看：真正查找和移除数据。
       <- data                       # 轨迹段列表返回服务端路由。
  # 服务端将 data 与 success、drained 等字段组成回复。
  <== HTTP 响应 ==
  # 客户端 response.json() 解析整个回复字典。
  <- generate 的 trajectory_payload 接住字典
```

这里选择的是本次 `drain=True` 的路径。下一处若要看清实际查找与移除，进入 [TrajectoryStore.pop_trajectory 源码](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/trajectory_store.py#L367)；读完先返回本卡的 `data`，再看服务端回复，不直接跳到 Sample 转换。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：客户端请求取回 finalize 已发布的轨迹，当前传入 trajectory_id、instance_id 和 drain=True。
2. **具体内容**：解析读取条件，按是否指定轨迹选择路径；在指定轨迹路径中，根据 drain 调用取出并移除或只读取的存储方法，最后将数据和状态封装为回复。
3. **建议构建的心智模型**：

   > 接收读取条件 → 从存储中取出轨迹 → 把轨迹段列表回复给客户端。

   当前 drain=True，取出时还会移除匹配记录；数据来自 finalize 已经准备好的轨迹。

   这里不构建新的轨迹，也不把它转换成 Sample。

4. **调用代码**（客户端跨 HTTP 发来）：

   ```python
   response = await self._client.post(
       f"{self._proxy_url}/trajectory/read",
       json=payload,
       headers=self._headers(),
   )
   ```

## 本场景的输入与输出

### 1. 接收读取条件

```python
body = await request.json()
trajectory_id = _trajectory_id_from_body(body)  # 优先 trajectory_id，兼容 session_id。
instance_id = body.get("instance_id")
drain = bool(body.get("drain", False))          # 本次为 True。
segment_view = body.get("segment_view")        # 本次未指定。
```

这一步就是知道：要哪条轨迹、属于哪个任务、取出后是否移除。

本次 trajectory_id 的值来自 generate 中的 session_id，它对应之前 finalize 的轨迹编号。instance_id 限定任务，segment_view 由存储层选择默认视图。鉴权及视图合法性检查见完整源码，先不逐项展开。

### 2. 读取已发布的轨迹

当前 trajectory_id 已指定且 drain=True，实际调用的是 pop_trajectory。它取回已保存的轨迹段，不再构建轨迹。

原函数在 `if trajectory_id` 分支里的完整读取表达式：

```python
data = (
    trajectory_store.pop_trajectory(
        trajectory_id,
        instance_id=instance_id,
        segment_view=segment_view,
    )
    if drain  # 当前走这里：取出并移除匹配的记录。
    else trajectory_store.read_trajectory(
        trajectory_id,
        instance_id=instance_id,
        segment_view=segment_view,
    )
)
```

pop_trajectory 的当前合同：按轨迹 ID 和可选任务 ID 匹配；选取返回视图；移除匹配记录；把返回段按 segment_index、timestamp 排序并转成字典。找不到则返回空列表。当前默认 TITO 返回 lineage 视图，但移除范围包含匹配轨迹的其他视图。

**阅读深度说明：** 当前实际展开的是客户端 read_trajectory 与本服务端路由；下游 pop_trajectory 只核对了职责，尚未逐段阅读。它负责按索引查找、筛选视图、同步移除记录、排序并序列化；如果要解释“具体如何取出并移除”，应从 trajectory_store.py:367 的这个方法继续，而不能把本路由的说明算作已经读完存储层。

这次先把存储方法作为一个动作理解，不单独建卡或深入索引维护。无 trajectory_id 时的 read_batch 属于其他入口，本轮不读。

### 3. 回复客户端，沿原调用返回

```python
return {
    "success": bool(data),               # 列表非空才为 True。
    "mode": "trajectory",               # 本次是按轨迹编号读取。
    "data": data,                        # 核心：轨迹段字典列表。
    "meta_info": trajectory_store.stats(),  # 存储统计。
    "drained": drain,                    # 反映请求的 drain 标志。
}
```

`drained=True` 不保证找到了数据；比如 data=[] 时 success=False，drained 仍可以是 True。HTTP 返回成功与轨迹非空是不同判断。

客户端接到这个回复，通过 response.json() 解析成整个字典，最终由 generate 的 trajectory_payload 接住；其中 data 才是轨迹段列表。`data` 里的 tokens、full_logprobs、full_loss_mask 等仍是轨迹字段，转换为 Sample 属于 Step 008。

当前请求包含移除操作，不能假定重复请求还能取得同一份数据。本轮不扩大为通信失败恢复专题。

## 我的直接表述（原话）

> 好的 我大概清楚了
> 那么现在是否需要看一下这个proxy这里是怎么处理的呢?

用户对客户端请求方向表示大致清楚，现进入服务端读取分支；尚无本路由内部机制的独立复述。

本轮用户要求保存：

> 好的 那么把这里的这个内容写在short term memory里面吧

已将三步解释补入本卡；保存请求不视为对所有机制的独立复述。

本轮职责复述：

> 简单来说就是把之前村的trajectory 按照需求返回对应的内容对吗?
> 那么目前这里的有什么特别需要了解的呢?

助手核对：按条件返回已有轨迹的理解正确。当前重点是按 trajectory_id 和 instance_id 定位、data 返回轨迹段列表，以及 drain=True 会移除匹配记录；找不到时 data=[]、success=False，而非重新生成。存储索引和批量分支不必现在深读。

## 尚不清楚

- 存储索引与批量读取的具体实现，本轮只按接口职责理解。
- 轨迹段如何转换成 Sample，留待 Step 008。

<details>
<summary>完整函数与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。静态核对，未发请求或删除任何真实记录。

```python
@app.post("/trajectory/read")
async def trajectory_read(request: Request):
    _check_auth(request)
    body = await request.json()
    trajectory_id = _trajectory_id_from_body(body)
    instance_id = body.get("instance_id")
    max_groups = body.get("max_groups")
    drain = bool(body.get("drain", False))
    segment_view = body.get("segment_view")
    if segment_view is not None and segment_view not in {"lineage", "timeline"}:
        raise HTTPException(
            status_code=400,
            detail="segment_view must be 'lineage' or 'timeline'",
        )

    if trajectory_id:
        data = (
            trajectory_store.pop_trajectory(
                trajectory_id,
                instance_id=instance_id,
                segment_view=segment_view,
            )
            if drain
            else trajectory_store.read_trajectory(
                trajectory_id,
                instance_id=instance_id,
                segment_view=segment_view,
            )
        )
        return {
            "success": bool(data),
            "mode": "trajectory",
            "data": data,
            "meta_info": trajectory_store.stats(),
            "drained": drain,
        }

    data = trajectory_store.read_batch(max_groups=max_groups)
    return {
        "success": bool(data),
        "mode": "batch",
        "data": data,
        "meta_info": trajectory_store.stats(),
    }
```

辅助依据：server.py:626 的轨迹 ID 解析；trajectory_store.py:353–419 的 read/pop 与视图选择。完整请求链来源见客户端函数卡。

[本轮形成过程](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md#trajectory-read-server)。

</details>
