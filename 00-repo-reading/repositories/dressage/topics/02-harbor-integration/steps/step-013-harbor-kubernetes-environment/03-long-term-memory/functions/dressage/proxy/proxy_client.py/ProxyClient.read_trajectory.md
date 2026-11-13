> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# ProxyClient.read_trajectory

- 源码：[proxy_client.py:115–147](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L115)。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；本轮建立客户端函数卡，不代表个人已掌握服务端内部。

[从 generate 返回后的调用进入](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#read-trajectory) → **本客户端方法** → POST /trajectory/read → 返回 generate 的 trajectory_payload。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：finalize_session 已将轨迹准备好，generate 更新 context_owned 后，请 Proxy 交回本次轨迹。
2. **具体内容**：将查询标识、可选视图/批量参数和 drain 组成正文，向 Dressage Proxy 发送 POST，检查 HTTP 状态并返回 JSON 字典。当前走指定 trajectory_id 的单条轨迹路径。
3. **建议构建的心智模型**：

   > 按轨迹编号向 Proxy 取回已整理好的轨迹；本次还要求从 Proxy 的轨迹存储中移除对应记录。

   finalize 负责准备和保存，read_trajectory 负责领取；不是再运行 Agent 或再采集一次模型请求。

4. **调用代码**（generate:301–309）：

   ```python
   await proxy_client.finalize_session(
       session_id, instance_id=instance_id, label=getattr(sample, "label", None)
   )
   context_owned = False
   trajectory_payload = await proxy_client.read_trajectory(
       trajectory_id=session_id,
       instance_id=instance_id,
       drain=True,
   )
   ```

## 本场景的输入与输出

### 1. 当前参数是什么

| 参数 | 当前传入 | 用途 |
| --- | --- | --- |
| trajectory_id | session_id | 指定本次轨迹；前面的 finalize 就使用 session.session_id 作为 trajectory_id |
| instance_id | 当前任务实例 ID | 限定记录所属的任务，不是 sandbox ID |
| drain | True | 服务端取出后移除匹配记录，避免已完成轨迹一直占用 Proxy 内存 |
| session_id / max_groups / segment_view | 本次未传 | 分别是兼容查询标识、批量参数和视图选择；当前不展开其他查询路径 |

方法默认 drain=False，但 generate 明确传了 True，因此当前不能按“读完仍保留原记录”理解。

### 为什么读取轨迹要发 HTTP POST？

不是把请求发给 client，而是通过 client 把请求发给 Proxy 服务端。`ProxyClient` 在 rollout 一侧负责通信；`self._client` 是 HTTPX 客户端；`self._proxy_url` 指向运行 Dressage Proxy 的服务。轨迹在服务端的 trajectory_store，客户端不直接持有那份内存对象，即使部署在同一台机器上也按该接口通信。

```text
rollout / generate
    -> ProxyClient.read_trajectory
    -> HTTPX POST /trajectory/read
    -> Dressage Proxy: trajectory_read
    -> trajectory_store
    <- JSON response with data
    <- trajectory_payload
```

请求正文是“读取条件”，不是重新上传轨迹：本次包含 trajectory_id、instance_id 和 drain=True。服务端按条件查找已存数据，将轨迹段放进响应的 data 返回。

POST 不代表每个接口都只能新建数据；本仓库将这个带 JSON 条件的操作定义为 POST /trajectory/read。它还支持取出后移除记录，本次 drain=True 就有这个副作用，所以也不是纯粹的只读查询。具体方法名由接口约定决定，代码并没有表示所有轨迹读取都必须用 POST。

### 2. 完整函数：构造正文、发送请求、返回字典

原函数仅添加中文注释：

```python
async def read_trajectory(
    self,
    *,
    trajectory_id: str | None = None,
    session_id: str | None = None,
    instance_id: str | None = None,
    max_groups: int | None = None,
    segment_view: str | None = None,
    drain: bool = False,
) -> dict:
    payload: dict[str, Any] = {
        "drain": drain,  # 当前为 True，要求领取后移除匹配记录。
    }
    # 可选项仅在有值时写入正文；当前写入 trajectory_id 和 instance_id。
    if trajectory_id is not None:
        payload["trajectory_id"] = trajectory_id
    if session_id is not None:
        payload["session_id"] = session_id
    if instance_id is not None:
        payload["instance_id"] = instance_id
    if max_groups is not None:
        payload["max_groups"] = max_groups
    if segment_view is not None:
        payload["segment_view"] = segment_view

    # 发送到 Dressage Proxy，不是沙箱内的 BlackboxServer。
    response = await self._client.post(
        f"{self._proxy_url}/trajectory/read",
        json=payload,
        headers=self._headers(),
    )
    response.raise_for_status()  # HTTP 错误在这里抛出。
    return response.json()      # 整个回复字典交给 trajectory_payload。
```

### 3. 返回什么，以及 drain 的边界

指定轨迹的服务端响应有五个字段：success、mode、data、meta_info、drained。其中 mode 为 "trajectory"，data 是轨迹段字典的列表，success 为 bool(data)，meta_info 是存储统计，drained 反映请求的 drain 值。客户端没有只取 data，也没有在 success=False 时主动抛错；HTTP 成功不保证 data 非空。

每个 data 元素带有 tokens、full_logprobs、full_loss_mask、aligned_response_length 和轨迹/段标识等，来自前面构建并存储的轨迹。当前返回值尚不是 Sample。

TITO 模式本次未指定 segment_view，默认选择 lineage 视图。drain=True 的服务端 pop 按 trajectory_id 与可选 instance_id 匹配并移除记录；返回结果再选择视图，因此移除范围可能包含未返回的 timeline 视图。它不是只删除返回的 lineage 列表，也不销毁沙箱或取消任务。这里仅核对接口语义，存储实现不逐段展开。

## 读完返回哪里

客户端接到响应后返回 generate:305 的 trajectory_payload；后续 `trajectory_payload.get("data")` 才取出段列表，转换成 Sample 属于 Step 008。

若需要确认服务端怎样查找和移除，下一处为 [POST /trajectory/read 的服务端函数卡](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)。本轮已按用户要求建立服务端路由卡；存储方法仍按接口理解，不提前建卡。

## 我的直接表述（原话）

> 好的 是这里的proxy client read trajectory对吗?

随后要求：

> 那么生成一下这里的这个trajectory的函数吧

以上确认本轮函数范围，尚无对读取和 drain 机制的独立复述。

本轮疑问：

> 这里为什么是通过向client来post这个trajectory read来阅读这里的轨迹的呢?
> 我有点小小的不理解

随后用户表示“好的 我大概清楚了”，并请求查看 Proxy 服务端处理；不据此推断已理解全部服务端机制。

## 尚不清楚

- 服务端路由与存储查询的逐段实现，当前只核对接口语义。
- 段列表怎样变成 Slime Sample，留到 Step 008。

<details>
<summary>来源与验证</summary>

- 固定源码：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- proxy_client.py:115–147：当前完整函数；blackbox_dispatch.py:301–309：当前实参及接收位置。
- proxy/server.py:2923–2964：指定轨迹与批量分支；trajectory_store.py:353、367：读取与移除；默认视图由 _default_segment_view 选择，TITO 为 lineage。
- trajectory_store.py:70 的 to_dict 提供段字典格式。
- 静态源码核对，未发出请求或移除任何真实记录。
- [本轮形成过程](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md#read-trajectory-client)。

</details>
