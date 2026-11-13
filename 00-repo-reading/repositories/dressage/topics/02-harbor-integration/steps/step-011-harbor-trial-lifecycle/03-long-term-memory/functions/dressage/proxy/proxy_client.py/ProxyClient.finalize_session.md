> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.finalize_session.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.finalize_session.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.finalize_session.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.finalize_session.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# ProxyClient.finalize_session

> 2026-11-08 按用户明确要求开始本函数阅读；从此前备用材料调入并按当前源码核对。此前准备材料不算提前完成阅读。

[Step 007 阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/01-scope.md#reading-navigation) → [generate 的会话收尾调用](../../rollout/generate/blackbox_dispatch.py/generate.md#finalize-call) → **本函数：向 Proxy 发送会话收尾请求**。

## 函数定位

- 源码：[proxy_client.py:64–82](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L64)。
- 首次单独展开：Step 007，2026-11-08。
- 最近认识更新：本轮建立源码说明，尚无用户对本函数的独立复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 调用与配置的 after_agent 命令已正常结束，generate 要求 Dressage Proxy 收尾本次会话。
2. **具体内容**：组装会话标识和可选任务资料，发送 POST /session/finalize，检查 HTTP 状态并返回响应字典。
3. **建议构建的心智模型**：

   > 告诉 Proxy 该给这次会话收尾了，等它处理后回复。

4. **调用代码**，来自 generate：

   ```python
   await proxy_client.finalize_session(
       session_id,
       instance_id=instance_id,
       label=getattr(sample, "label", None),
   )
   context_owned = False  # 只有前面的 await 正常返回才继续执行。
   ```

## 本场景的输入与输出：沿完整函数看三处

**当前位置：generate:301 → 本函数；读完接回 generate:304。**

输入沿用当前 session_id、任务实例 instance_id 和 sample 的可选 label。请求发送到外部 Dressage Proxy；模型交互已经在 Agent 运行期间记录，本次正文不重新上传 CLI 输出或整份对话。

```python
async def finalize_session(
    self,
    session_id: str,
    *,
    instance_id: str | None = None,
    label: Any | None = None,
) -> dict:
    # [1] 告诉 Proxy 要处理哪个会话；可选资料有值才传。
    payload: dict[str, Any] = {"session_id": session_id}
    if instance_id is not None:
        payload["instance_id"] = instance_id
    if label is not None:
        payload["label"] = label

    # [2] 发给 Dressage Proxy 的收尾接口，等待 HTTP 回复。
    response = await self._client.post(
        f"{self._proxy_url}/session/finalize",
        json=payload,
        headers=self._headers(),
    )
    # [3] HTTP 错误会抛出；正常时解析并返回响应正文。
    response.raise_for_status()
    return response.json()
```

1. **session_id 选择会话。** instance_id 用于任务关联；label 是可选标注资料，传入它不表示本函数在计算奖励。
2. **客户端只负责请求。** 真正整理并发布轨迹的是 Proxy 服务端对应的处理函数。
3. **返回的是收尾响应。** 服务端正常响应含 success、trajectory_id、num_steps、num_segments 等摘要；完整轨迹正文由后面的 read_trajectory 取得。generate 在此没有保存这个响应字典。

### 读完返回哪里

下一处要问“收尾内部到底做了什么”时，按 HTTP 路径进入 [Proxy 服务端 finalize_session 函数卡](../server.py/create_app.finalize_session.md)。本轮已按用户要求简读服务端收尾顺序，具体轨迹构建算法仍不展开。

该请求正常完成后返回 generate，继续 context_owned = False，再到 read_trajectory。本次 finalize 不负责删除 Pod 或终止 Paddock；资源回收仍由外层生命周期处理。

## 我的直接表述（原话）

> 好的那么看一下这里的这个 proxyclient finalize session吧

这是本函数的阅读确认，尚无该函数机制的独立复述。

## 尚不清楚

- Proxy 服务端如何取得已有会话、构造轨迹记录并发布。
- context_owned 的责任变化与异常清理的关系，返回 generate 时再接清。
- 后续 read_trajectory 如何选择并取走轨迹，本轮尚未展开。

<details>
<summary>来源与验证</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，源码工作区干净。
- 当前方法：proxy_client.py:64–82；调用处：blackbox_dispatch.py:301–304；服务端响应及发布位置：proxy/server.py:2751 行起。
- [Step 007 本次记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md#start-step007)。仅静态核对，没有发起 HTTP 请求、运行后置命令或模型。

</details>
