# SGLangRouterClient.generate

- 源码：[sglang_client.py:176](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/sglang_client.py#L176)。本地 `/home/hongshi/projects/Dressage`，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独整理：2026-11-16，Step 006 公共 Proxy 补读。
- 认识状态：2026-11-16 用户概括发送职责并要求返回主线；客户端与服务端的区别由助手校准。静态核对，未请求真实模型。

[本步 scope](../../../../../01-scope.md) · [返回调用方](../generation_controller.py/GenerationController._generate_with_optional_request_id.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：生成控制器已准备本次请求，辅助方法完成参数兼容后调用当前客户端。
2. **具体内容**：把参数组装成 HTTP 正文和请求头，选择目标地址，发送 /generate，检查响应并转换为 SGLangResponse。
3. **建议构建的心智模型**：

   > 将 Python 生成调用转换为 HTTP 请求，再将后端 JSON 转换为 Python 结果对象。

4. **调用代码**（来自辅助方法末尾，generate 已指向 self._sglang_client.generate）：

   ```python
   return await generate(input_ids, sampling_params, **kwargs)
   ```

## 本场景的输入与输出

承接当前正常首次生成：输入为 prompt token、采样参数、routing_key、request_id、worker_url 及 logprob_start_len=-1；未显式传入的 return_logprob 使用默认 True。客户端还可能依据实例配置要求返回专家路由资料。

```text
生成控制器 → 参数兼容辅助方法 → 当前客户端
                                 → HTTP POST /generate
                                 ← 后端 JSON
                             ← SGLangResponse
控制器接住 response，继续累计并整理结果
```

### 1. 把生成内容与返回选项放入正文

```python
payload = {
    "input_ids": input_ids,
    "sampling_params": sampling_params,
    "return_logprob": return_logprob,
    "logprob_start_len": logprob_start_len,
    "return_text_in_logprobs": True,
}
```

输入和采样参数来自上游，当前函数负责装入请求。原码还根据 return_routed_experts 或实例配置添加同名选项。

### 2. 放入请求编号与路由请求头

```python
if request_id:
    payload["rid"] = request_id
headers = {}
if routing_key:
    headers["X-SMG-Routing-Key"] = routing_key
```

rid 标识本次生成；路由 key 进入请求头，供相应路由策略使用。二者用途不同，概念图保留在调用方函数卡。

### 3. 选择目标并等待 HTTP 响应

```python
target_url = (worker_url or self._router_url).rstrip("/")
response = await self._client.post(
    f"{target_url}/generate", json=payload, headers=headers
)
```

有 worker_url 就优先使用它，否则用初始化时的 router_url。这里的 response 是 HTTP 响应对象，还不是 SGLangResponse。

### 4. 检查并转换结果，返回调用方

```python
response.raise_for_status()
data = response.json()
return self._coerce_response(
    data,
    input_ids=input_ids,
    expect_input_logprobs=bool(return_logprob and logprob_start_len == 0),
)
```

先检查 HTTP 状态，再解析 JSON，由 _coerce_response 整理成 SGLangResponse。本场景 expect_input_logprobs 为 False。返回对象经辅助方法交回控制器，包括文本、token 和概率等生成资料；不是最终的 PreemptibleGenerateResult，也不是 StepRecord。

读到返回即可；_coerce_response 的内部字段解析先不展开。HTTP 失败或 JSON 解析失败不会在此自动变成成功结果。

## 我的直接表述（原话）

本轮入口确认，节选：

> 这里应该继续看一下这个sglang client generate了吗？

本轮复述与返回请求：

> 简单来说就是吧需要的内容和部分发送给sglang的客户端
> 我觉得可以回去了？
> 这里的内容差不多了？

助手校准：本函数本身属于客户端，组织 HTTP 请求并发给目标推理服务，随后整理返回结果。用户要求结束本层阅读并返回主线；不据此标记响应解析内部已掌握。

## 尚不清楚

- _coerce_response 如何解析后端各字段，暂留为按需回查。
- 尚未进行真实模型请求或取得真实返回样例。

<details>
<summary>完整源码与验证边界</summary>

以下为固定提交本地源码 176–216 行；仅静态阅读，未修改或执行服务。

```python
async def generate(
    self,
    input_ids: list[int],
    sampling_params: dict[str, Any],
    *,
    return_logprob: bool = True,
    logprob_start_len: int = 0,
    return_routed_experts: bool = False,
    routing_key: str | None = None,
    request_id: str | None = None,
    worker_url: str | None = None,
) -> SGLangResponse:
    payload = {
        "input_ids": input_ids,
        "sampling_params": sampling_params,
        "return_logprob": return_logprob,
        "logprob_start_len": logprob_start_len,
        "return_text_in_logprobs": True,
    }
    if return_routed_experts or self._return_routed_experts:
        payload["return_routed_experts"] = True
    if request_id:
        # SGLang request-level abort is keyed by rid.  Keep the public
        # Python parameter name request_id because the rest of Dressage and
        # blackbox server use that terminology.
        payload["rid"] = request_id
    headers = {}
    if routing_key:
        headers["X-SMG-Routing-Key"] = routing_key

    target_url = (worker_url or self._router_url).rstrip("/")
    response = await self._client.post(
        f"{target_url}/generate", json=payload, headers=headers
    )
    response.raise_for_status()
    data = response.json()
    return self._coerce_response(
        data,
        input_ids=input_ids,
        expect_input_logprobs=bool(return_logprob and logprob_start_len == 0),
    )
```

[本次整理过程](../../../../../04-flow.md)。

</details>
