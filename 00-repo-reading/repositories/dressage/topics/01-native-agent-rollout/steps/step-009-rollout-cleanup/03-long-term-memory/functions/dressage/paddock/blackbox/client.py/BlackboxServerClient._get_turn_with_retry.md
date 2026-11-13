> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServerClient._get_turn_with_retry

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../step-006-agent-execution/02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 阅读导航](../../../../../../../step-006-agent-execution/01-scope.md#reading-sequence) → [_poll_turn](BlackboxServerClient._poll_turn.md) → **本函数：发送一次带重试的状态查询** → 返回 _poll_turn 解析回复。

## 函数定位

- 源码：[client.py:355–378](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L355)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：本轮按用户指定建立说明，尚无对本函数的独立复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_poll_turn 已经用沙箱地址、session_id 和 turn_id 拼好 URL，现在要发送一次状态查询。
2. **具体内容**：读取重试设置，将 URL、查询参数和请求头交给公共 GET 函数，等待并原样返回 HTTP 响应。
3. **建议构建的心智模型**：

   > 发出这次状态查询，遇到允许重试的请求失败就按规则重试，拿到 HTTP 回复后交回上层。

4. **调用处**，位于 _poll_turn 的循环中：

   ```python
   response = await self._get_turn_with_retry(
       url,
       params={"wait": poll_wait},
       operation="poll_turn",
       trajectory_id=trajectory_id,
       headers=endpoint.headers,
   )
   data = response.json()  # 回到 _poll_turn 后才解析正文。
   status = str(data.get("status") or "")
   ```

## 本场景的输入与输出：沿完整函数看交接

输入 URL 指向沙箱内 BlackboxServer 的 `/v1/sessions/{session_id}/turns/{turn_id}`。params 携带本次服务端等待参数；headers 沿用沙箱入口的请求头。输出是同一个 httpx.Response 对象，调用方再从中读取状态和结果。

以下保留完整函数，只添加中文注释：

```python
async def _get_turn_with_retry(
    self,
    url: str,                      # _poll_turn 已拼好的完整查询地址。
    *,
    params: dict[str, Any],         # 当前是 {"wait": poll_wait}。
    operation: str,                # 当前是 "poll_turn"，用于请求日志。
    trajectory_id: str,            # 日志中的关联标识。
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    # [1] 取得尝试次数、初始等待、基础退避上限和随机抖动设置。
    max_attempts, initial_delay, max_delay, jitter_fraction = self._retry_config()
    # [2] 真正的 GET 和重试循环在公共函数中。
    return await get_json_with_retry(
        self._client,
        url,
        params=params,
        operation=operation,
        trajectory_id=trajectory_id,
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        jitter_fraction=jitter_fraction,
        log_prefix="blackbox server",
        logger=logger,
        headers=headers,
    )  # [3] 正常取得 HTTP 回复后交回 _poll_turn；失败可能抛出异常。
```

下层 get_json_with_retry 中，真正发请求的是：

```python
response = await client.get(url, params=params, headers=headers)
```

### 两种“再试一次”要分开

| 发生什么 | 谁负责下一步 |
| --- | --- |
| 请求遇到允许重试的连接/超时异常，或默认可重试的 HTTP 503 | get_json_with_retry 按次数和等待设置重试 GET |
| 请求成功，正文中的调用状态仍是 queued / inflight | 本函数返回 Response，外层 _poll_turn 解析后继续下一次查询 |
| 请求成功，正文中的调用状态是 committed | 本函数同样返回 Response，外层 _poll_turn 整理并返回调用结果 |

所以，HTTP 请求成功不等于 Agent 已经做完题目。本函数不检查正文中的任务状态，也不重新提交题目。

与之前 [_post_agent_with_retry](BlackboxServerClient._post_agent_with_retry.md) 的区别很小：之前发送 POST 正文，这次使用已拼好的 URL 发送 GET 查询参数；两者都补上重试配置，再返回 HTTP 响应。

## 返回哪里，本轮在哪里停

看清“补重试设置 → 委派 GET → 返回 Response”即可。接着返回 [_poll_turn 的 response.json()](BlackboxServerClient._poll_turn.md#parse-query-response)，看它怎样读取 status，决定继续查询还是结束。

<details>
<summary>按需回查：重试范围与源码</summary>

- 当前未覆盖环境变量时，最多尝试 6 次（含首次），初始等待 1 秒，基础退避上限 10 秒，随机抖动比例 0.2。详见 [_retry_config:291](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L291)。
- 公共 GET 函数默认仅将 HTTP 503 列为可重试状态码；404 等其他 HTTP 错误直接抛出，不是所有失败都会重试。
- 它捕获的请求异常是 ConnectError、ConnectTimeout、PoolTimeout、ReadTimeout；达到尝试上限仍失败时抛出。
- 重试循环和退避细节在 [get_json_with_retry:109](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/http_retry.py#L109)。本轮只核对本方法所依赖的行为，没有为下层辅助函数另建卡片。

</details>

## 我的直接表述（原话）

> 那么看一下这里的这个get turn with retry吧

这是指定阅读入口的请求，尚无机制复述。

## 尚不清楚

- 本轮 HTTP 重试与外层状态轮询的区别，尚待用户反馈。
- 完整退避算法和服务端 GET 路由内部的实现，继续按需回查。

<details>
<summary>来源与验证</summary>

- 固定源码：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 调用者：client.py:182–190；当前方法：355 行起；公共 GET：common/http_retry.py:109 行起。
- [Step 006 本次过程](../../../../../../../step-006-agent-execution/04-flow.md#get-turn-with-retry-reading)。仅静态核对，未向沙箱发送 HTTP 请求或执行重试实验。

</details>
