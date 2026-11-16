# 长函数参考：调用树、阶段问题与两层代码

- 用户认可并要求纳入：2026-11-15。
- [原始函数卡](../../../../00-repo-reading/repositories/dressage/topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/proxy/generation_controller.py/GenerationController.generate_preemptible.md)：下方保存本次认可版本，链接已按本文件位置重算；后续学习继续更新原卡，不改写本快照中的认识状态。

## 何时使用

适用于函数较长、用户容易在参数与分支中失去主线，并希望先看全程再展开细节的情况。短函数无需强制采用两层折叠；段数由真实职责决定，不固定为四段。

## 保留哪些做法

1. 在“本场景的输入与输出”开头用调用树标出调用方、当前函数、关键下游及 HTTP 等边界，并说明结果交回哪里；不把所有 helper 列成目录。
2. 保留同一阅读场景的输入、返回与副作用；正常路径和暂缓分支分开说明。
3. 按实际动作命名阶段，例如“等待允许生成，准备并登记请求”，不能用开头几行的“准备容器”概括整段。
4. 每段标题下面、代码上面写一句“本段要解决的问题”，说明为什么需要这一步。
5. 每段先给有注释的执行骨架，真实函数名、数据变化、循环退出与交接保留；省略明确标记为教学裁剪。参数字段较多的具体代码放在内层折叠，不能只缩减原本折叠的内容却声称主线已经简化。
6. 外层阶段默认折叠，让读者先浏览编号标题；展开后能看到问题和骨架，需要核对时才继续展开具体代码。返回主线和必要的语义区别应留在骨架层。
7. 个人原话、未知和来源继续保留；用户说大概理解不等于已掌握所有分支。样例只说明一种获得认可的展示方式，不证明普适认知效果。

## 已认可的完整卡片快照

---

# GenerationController.generate_preemptible

- 源码：[generation_controller.py:159–446](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/generation_controller.py#L159)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：2026-11-15，Step 006 公共 Proxy 补读。
- 最近认识更新：2026-11-15，用户表示大概理解四段顺序，并复述生成判断、发送、收集与整理；助手补充第 1 段为允许执行检查，第 4 段返回完整生成结果，元数据仅为其中一部分。

[pipeline 第 3 段](../../../../00-repo-reading/repositories/dressage/topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/proxy/server.py/create_app._chat_completions_pipeline.md#pipeline-generate) → **本函数组织生成** → 返回 router_response，继续结算租约及解析结果。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：pipeline 已准备输入 token、采样参数和推理位置，需要取得一次生成结果。
2. **具体内容**：登记正在执行的请求，调用后端，积累生成片段，撤销活跃登记，返回统一结果；被抢占时可按配置续接。
3. **建议构建的心智模型**：

   > 管理一次允许中断续接的生成；正常路径请求一次后端、接回一个片段，就整理返回。

4. **调用代码**（裁剪辅助实参）：

   ```python
   router_response = await generation_controller.generate_preemptible(
       input_ids=input_ids, sampling_params=sampling_params,
       session_id=session_id, instance_id=instance_id,
       turn_id=effective_turn_id, worker_url=routing_lease.worker_url,
       # pipeline 还传入版本、epoch、logprob 和窗口参数。
   )
   ```

## 本场景的输入与输出

<a id="generation-mainline"></a>


```text
_chat_completions_pipeline
└─ GenerationController.generate_preemptible  ← 当前阅读
   │  管理一次生成：登记请求、收集结果、必要时续接
   │
   └─ _generate_with_optional_request_id
      │  根据客户端支持的参数，委派生成
      │
      └─ SGLangRouterClient.generate
         │  组装请求，解析后端响应
         │
         └─ HTTP POST /generate
            SGLang 执行模型生成
```

**结果怎样接回来**：SGLang 响应经客户端整理后交回当前函数；当前函数汇总为 `PreemptibleGenerateResult`，由 pipeline 的 `router_response` 接住。下面四段展开当前函数自身的处理。

继续 pipeline 的 **TITO、正常成功路径**：无暂停、抢占、溢出或版本冲突；`logprob_start_len=-1`，不要求输入 token 的 logprob。这里只核对源码，未运行模型。

- **输入**：input_ids、sampling_params、session/instance/turn 身份和 worker_url。
- **返回**：PreemptibleGenerateResult，包括文本、输出 token、logprob、版本与结束原因，由 pipeline 的 router_response 接住。
- **副作用**：请求执行期间进入 self._active，收集结果后移除；本函数不写 Session 的 StepRecord。

<details>
<summary>1. 等待允许生成，准备并登记本次后端请求（186–244）</summary>

**本段要解决的问题**：现在是否允许继续生成？如果允许，这次要生成多少 token，又怎样让控制器找到这次请求？

按代码顺序看（教学骨架：省略初始化和具体参数；`...` 表示未展开的源码）：

```python
generated_ids = []
chunks = []
# 保存已经生成的 token 和后端返回片段；max_new_tokens 已从采样参数读取。

while max_new_tokens <= 0 or len(generated_ids) < max_new_tokens:
    # 检查生成额度；正常结束的判断还在第 3 段。
    await self._wait_until_resumed()
    # 控制器暂停时等待恢复，不是在检查网络是否断开。

    # 计算剩余额度，准备这次请求的采样参数。
    ...
    active = _ActiveGeneration(...)
    # 描述即将提交的后端请求。

    async with self._pause_lock:
        ...  # 再检查暂停等状态，允许执行才登记。
        self._active[active.request_id] = active
        # 登记后，控制器才能找到这个活跃请求。
    # 接第 2 段：调用后端。此时已离开 _pause_lock。
```

<details>
<summary>展开具体代码：剩余额度、请求字段与登记</summary>

以下保留现有源码摘录，仍省略辅助检查，并非完整实现。

```python
max_new_tokens = int(sampling_params.get("max_new_tokens") or 0)
generated_ids: list[int] = []
chunks: list[GenerationChunk] = []
# 同处初始化 output_ids、output_logprobs、text_parts 等结果容器。

while max_new_tokens <= 0 or len(generated_ids) < max_new_tokens:
    await self._wait_until_resumed()  # 未暂停时直接继续。
    remaining = None if max_new_tokens <= 0 else max_new_tokens - len(generated_ids)
    chunk_sampling_params = dict(sampling_params)
    if remaining is not None:
        chunk_sampling_params["max_new_tokens"] = remaining

    active = _ActiveGeneration(
        request_id=self._new_request_id(session_id=session_id, turn_id=turn_id),
        session_id=session_id, instance_id=instance_id, turn_id=turn_id,
        routing_key=routing_key, worker_url=worker_url,
        input_ids=list(input_ids), generated_ids_at_start=list(generated_ids),
        sampling_params=dict(chunk_sampling_params),
    )
    async with self._pause_lock:
        # 省略关闭/epoch 检查、暂停时 continue 和 epoch 赋值。
        self._active[active.request_id] = active
    # 第 2–3 段继续在循环内；这里的锁不会覆盖整个网络等待。
```

</details>

</details>

<details>
<summary>2. 向后端发起生成，等待一个结果（245–308）</summary>

**本段要解决的问题**：本次应让模型从哪些 token 之后继续生成，实际请求又交给谁？

按代码顺序看（教学骨架，省略处不改变实际调用关系）：

```python
response = await self._generate_with_optional_request_id(
    list(input_ids) + list(generated_ids),
    chunk_sampling_params,
    # 省略身份、推理位置和 logprob 参数。
)
# 输入 = 原始 prompt + 已生成前缀；首次请求尚无已生成前缀。
# 该方法委派 SGLang 客户端发送 /generate，并等待结果。
# 接回的 response 交给第 3 段收集。
```

本路径接回完整的 SGLangResponse，不是逐 token 接收 SSE。具体 HTTP 发送发生在下游客户端。

<details>
<summary>展开具体代码：请求参数与客户端 HTTP 发送</summary>

以下保留现有源码摘录及交接说明，仍有辅助字段省略。

```python
response = await self._generate_with_optional_request_id(
    list(input_ids) + list(generated_ids),  # 首次 generated_ids 为空。
    chunk_sampling_params,
    routing_key=routing_key,
    worker_url=worker_url,
    request_id=active.request_id,
    logprob_start_len=chunk_logprob_start_len,  # 本场景为 -1。
)
```

这里的真实交接是：

```text
_generate_with_optional_request_id
  → self._sglang_client.generate
    → HTTP POST /generate
    ← SGLangResponse
```

辅助方法只按客户端签名传递支持的参数。实际发送在 SGLangRouterClient.generate:209 附近：

```python
# 以下属于 sglang_client.py，不是本函数直接执行的语句。
target_url = (worker_url or self._router_url).rstrip("/")
response = await self._client.post(
    f"{target_url}/generate", json=payload, headers=headers
)
response.raise_for_status()
data = response.json()
```

payload 带 input_ids、sampling_params 和 logprob 选项，request_id 写入 rid；客户端再将完整 JSON 整理为 SGLangResponse。本路径不是逐 token 接收 SSE。

</details>

</details>

<details>
<summary>3. 收集结果，结束活跃登记（310–419）</summary>

**本段要解决的问题**：后端结果怎样进入本次生成的累计结果，什么时候还需要继续循环？

按代码顺序看（教学骨架，省略处不改变实际调用关系）：

```python
# 原码先检查版本、判断本次是否被抢占。
chunk = GenerationChunk(...)
chunks.append(chunk)
generated_ids.extend(chunk.output_ids)
text_parts.append(chunk.text)
# 同时累计输出 token、概率、版本等，准备最终返回。

async with self._pause_lock:
    self._active.pop(active.request_id, None)
    ...  # 更新请求状态，并通知本次请求已收集完结果。

# 原码在这里检查抢占配置与上下文上限。
if not preempted:
    break  # 正常完成，退出第 1 段的循环，进入第 4 段。
# 被抢占且允许续接时，等待恢复，再带着 generated_ids 继续循环。
```

这里 chunk 是一次后端返回的生成片段；正常路径只有一个，不是 SSE 事件。

<details>
<summary>展开具体代码：片段字段、累计结果与结束通知</summary>

以下保留现有源码摘录及交接说明，仍有辅助字段省略。

```python
# 原码先检查版本，并从 abort 状态与 response 判断 preempted。
chunk = GenerationChunk(
    output_ids=list(response.output_ids),
    output_logprobs=list(response.output_token_logprobs),
    output_token_texts=list(response.output_token_texts),
    text=str(response.text or ""),
    version=version, finish_reason=response.finish_reason, preempted=preempted,
)
chunks.append(chunk)
output_ids.extend(chunk.output_ids)
output_logprobs.extend(chunk.output_logprobs)
generated_ids.extend(chunk.output_ids)
text_parts.append(chunk.text)
# 同处收集 token 文本、版本、结束原因等。

async with self._pause_lock:
    self._active.pop(active.request_id, None)
    active.preempted_chunk_collected = preempted
    active.state = "quiesced"
    active.quiesced_event.set()

# 原码另检查抢占配置、上下文溢出；本场景均通过。
if not preempted:
    break  # 正常生成完成，不为凑满 max_new_tokens 而继续请求。
```

</details>

</details>

<details>
<summary>4. 返回统一结果，接回 pipeline（421–446）</summary>

**本段要解决的问题**：调用方需要什么，才能继续解析回复并记录这次交互？

按代码顺序看（教学骨架，省略处不改变实际调用关系）：

```python
# 离开生成循环后，对齐输入侧数组长度，整理片段元数据。
...
return PreemptibleGenerateResult(
    text="".join(text_parts),
    output_ids=output_ids,
    output_token_logprobs=output_logprobs,
    # 省略输入 token、版本、结束原因和其他记录资料。
)
# 返回 pipeline，由 router_response 接住。
```

读完回到 [pipeline 第 3 段](../../../../00-repo-reading/repositories/dressage/topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/proxy/server.py/create_app._chat_completions_pipeline.md#pipeline-generate)：router_response 接住结果，结算 routing_lease，再进入第 4 段解析。self._active 的请求登记和 pipeline 的路由租约是不同层的状态。

<details>
<summary>展开具体代码：返回对象的主要字段</summary>

以下保留现有源码摘录及交接说明，仍有辅助字段省略。

```python
# 原码先对齐输入侧数组长度，整理片段元数据。
return PreemptibleGenerateResult(
    input_token_ids=list(input_ids),
    output_ids=output_ids,
    output_token_logprobs=output_logprobs,
    all_token_ids=list(input_ids) + output_ids,
    text="".join(text_parts),
    finish_reason=finish_reason,
    # 省略输入概率、token 文本、版本、元数据及 chunks 等字段。
)
```

</details>

</details>

## 我的直接表述（原话）

最初阅读确认：

> 好的 那么继续看下去吧
> 看一下这里到底是在做什么这件事情

最新复述：

> 好的 我觉得我大概理解这里的代码了
> 1.简单来说就是先看一下是否还是在生成的部分
> 2.然后在继续生成具体的部分发送出去请求
> 3.将生成的内容统计一下
> 4.同是在考虑一下把这一个片段整理成为元数据
> 就是这里在做的事情是我的理解

助手校准：第 1 段检查生成额度、等待允许执行并登记请求；第 3 段收集并累计文本、token、概率等，同时结束活跃登记；第 4 段整理 PreemptibleGenerateResult，元数据只是其中一部分。正常路径只有一个生成片段，续接时可累计多个。以上校准尚未获得进一步复述确认。

## 尚不清楚

- 暂停、抢占、续接以及版本校验的内部机制本轮不深入。
- 客户端 _coerce_response 如何解析后端所有字段尚未展开。
- 尚无真实模型运行与输出验证。

<details>
<summary>来源与裁剪边界</summary>

- 固定提交中 generation_controller.py:159–446；辅助交接 :675–705；sglang_client.py:176–216。
- 展示的代码裁剪了验证、异常和辅助实参，分段循环体为阅读展示，不是可替换源码的实现。
- 抢占后的部分 token 来自原 /generate 请求的返回，不来自 abort_request 的响应；本轮只定位，不深入此分支。
- pipeline 的 SSE 响应组织在生成结束之后，与这里的 GenerationChunk 不同。
- [本次阅读过程](../../../../00-repo-reading/repositories/dressage/topics/01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#generation-normal-path)。

</details>
