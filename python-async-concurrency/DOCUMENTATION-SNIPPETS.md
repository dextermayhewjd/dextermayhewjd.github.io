# 文档中的 Python 异步示例

源码版本：[`2f2318653f6f`](https://github.com/THUDM/slime/tree/2f2318653f6f794dddd321eff7c9d4b7b174643f)。本清单读取 Slime 已跟踪的 Markdown，保留包含 Python 原生异步语法或标准库并发模块的 `python`、`python3`、`py` 围栏。

共 **29 段，来自 14 个文件**。计数单位是一处文档围栏，独立于 `.py` 源码 AST 的函数、语句和 API 计数；同一示例在中英文文档出现两次，就保留两个出处。Shell、YAML、补丁、未标注为 Python 的代码和只涉及 Ray/GPU 的片段不在此表中。

其中有 **13 对中英文示例**：8 对正文逐字相同，4 对只调整了注释或说明性 docstring，1 对只改变 Markdown 列表缩进；合并这些双语对应项后为 **16 个示例**。按原始正文的 SHA-256 去重为 **21 段**，这两个去重口径不同。

以下代码全部逐字摘录，没有修补或执行；语法检查只去掉 Markdown 列表带来的共同缩进，保存的正文保留原始缩进。6 段是缺少冒号/函数体的接口签名；另有 5 段需要放进异步函数才能编译。其余片段也可能省略依赖、变量、实现和运行环境，AST 可解析不等于可直接运行。

机器清单 [documentation-snippets.json](documentation-snippets.json) 保存每段正文、含首尾的代码行号、围栏行号、固定版本链接、源文件与正文 SHA-256、语法状态和双语对应关系。

## 出处索引

| 编号 | 原文件与代码行 | 原生语法 | 语法状态 | 双语对应 |
| --- | --- | --- | --- | --- |
| [DOC-001](#doc-001) | [.claude/skills/add-reward-function/SKILL.md:36–37](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/.claude/skills/add-reward-function/SKILL.md#L36-L37) | `async def` | AST 可解析 | — |
| [DOC-002](#doc-002) | [.claude/skills/add-reward-function/SKILL.md:41–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/.claude/skills/add-reward-function/SKILL.md#L41-L42) | `async def` | AST 可解析 | — |
| [DOC-003](#doc-003) | [docs/en/advanced/sglang-config.md:173–189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/advanced/sglang-config.md#L173-L189) | `async def`、`await` | AST 可解析 | PAIR-01 |
| [DOC-004](#doc-004) | [docs/en/advanced/sglang-config.md:402–431](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/advanced/sglang-config.md#L402-L431) | `async def`、`await` | AST 可解析 | PAIR-02 |
| [DOC-005](#doc-005) | [docs/en/developer_guide/trace.md:60–74](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/developer_guide/trace.md#L60-L74) | `async def` | AST 可解析 | PAIR-03 |
| [DOC-006](#doc-006) | [docs/en/developer_guide/trace.md:90–96](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/developer_guide/trace.md#L90-L96) | `async def` | AST 可解析 | PAIR-04 |
| [DOC-007](#doc-007) | [docs/en/developer_guide/trace.md:107–111](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/developer_guide/trace.md#L107-L111) | `await` | 需异步外层 | PAIR-05 |
| [DOC-008](#doc-008) | [docs/en/get_started/agent.md:41–52](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/agent.md#L41-L52) | `await` | 需异步外层 | PAIR-06 |
| [DOC-009](#doc-009) | [docs/en/get_started/customization.md:77–88](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L77-L88) | `async def`、`async for`、`await` | AST 可解析 | PAIR-07 |
| [DOC-010](#doc-010) | [docs/en/get_started/customization.md:115–115](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L115-L115) | `async def` | 不完整签名 | PAIR-08 |
| [DOC-011](#doc-011) | [docs/en/get_started/customization.md:130–150](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L130-L150) | `async def`、`await` | AST 可解析 | PAIR-09 |
| [DOC-012](#doc-012) | [docs/en/get_started/customization.md:167–167](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L167-L167) | `async def` | 不完整签名 | PAIR-10 |
| [DOC-013](#doc-013) | [docs/en/get_started/customization.md:172–172](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L172-L172) | `async def` | 不完整签名 | PAIR-11 |
| [DOC-014](#doc-014) | [docs/en/get_started/quick_start.md:500–527](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/quick_start.md#L500-L527) | `async def`、`await` | AST 可解析 | PAIR-12 |
| [DOC-015](#doc-015) | [docs/en/get_started/usage.md:356–385](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/usage.md#L356-L385) | `async def`、`await` | AST 可解析 | PAIR-13 |
| [DOC-016](#doc-016) | [docs/zh/advanced/sglang-config.md:173–189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/advanced/sglang-config.md#L173-L189) | `async def`、`await` | AST 可解析 | PAIR-01 |
| [DOC-017](#doc-017) | [docs/zh/advanced/sglang-config.md:401–430](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/advanced/sglang-config.md#L401-L430) | `async def`、`await` | AST 可解析 | PAIR-02 |
| [DOC-018](#doc-018) | [docs/zh/developer_guide/trace.md:60–74](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/developer_guide/trace.md#L60-L74) | `async def` | AST 可解析 | PAIR-03 |
| [DOC-019](#doc-019) | [docs/zh/developer_guide/trace.md:90–96](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/developer_guide/trace.md#L90-L96) | `async def` | AST 可解析 | PAIR-04 |
| [DOC-020](#doc-020) | [docs/zh/developer_guide/trace.md:107–111](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/developer_guide/trace.md#L107-L111) | `await` | 需异步外层 | PAIR-05 |
| [DOC-021](#doc-021) | [docs/zh/get_started/agent.md:41–52](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/agent.md#L41-L52) | `await` | 需异步外层 | PAIR-06 |
| [DOC-022](#doc-022) | [docs/zh/get_started/customization.md:72–83](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L72-L83) | `async def`、`async for`、`await` | AST 可解析 | PAIR-07 |
| [DOC-023](#doc-023) | [docs/zh/get_started/customization.md:100–100](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L100-L100) | `async def` | 不完整签名 | PAIR-08 |
| [DOC-024](#doc-024) | [docs/zh/get_started/customization.md:115–135](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L115-L135) | `async def`、`await` | AST 可解析 | PAIR-09 |
| [DOC-025](#doc-025) | [docs/zh/get_started/customization.md:152–152](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L152-L152) | `async def` | 不完整签名 | PAIR-10 |
| [DOC-026](#doc-026) | [docs/zh/get_started/customization.md:157–157](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L157-L157) | `async def` | 不完整签名 | PAIR-11 |
| [DOC-027](#doc-027) | [docs/zh/get_started/quick_start.md:506–533](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/quick_start.md#L506-L533) | `async def`、`await` | AST 可解析 | PAIR-12 |
| [DOC-028](#doc-028) | [docs/zh/get_started/usage.md:358–387](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/usage.md#L358-L387) | `async def`、`await` | AST 可解析 | PAIR-13 |
| [DOC-029](#doc-029) | [examples/coding_agent_rl/README.md:194–197](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/README.md#L194-L197) | `async with`、`await` | 需异步外层 | — |

## 中英文重复关系

“逐字相同”比较整个围栏正文；“注释/docstring 本地化”和“列表缩进不同”保留两侧原文，不把这些差异当成新增机制。三个无双语对应项是奖励函数 Skill 的两段签名示例和 coding-agent README 的一段 sandbox 示例。

| 对应组 | 片段 | 关系 |
| --- | --- | --- |
| PAIR-01 | [DOC-003](#doc-003)、[DOC-016](#doc-016) | 注释/docstring 本地化 |
| PAIR-02 | [DOC-004](#doc-004)、[DOC-017](#doc-017) | 注释/docstring 本地化 |
| PAIR-03 | [DOC-005](#doc-005)、[DOC-018](#doc-018) | 正文逐字相同 |
| PAIR-04 | [DOC-006](#doc-006)、[DOC-019](#doc-019) | 正文逐字相同 |
| PAIR-05 | [DOC-007](#doc-007)、[DOC-020](#doc-020) | 正文逐字相同 |
| PAIR-06 | [DOC-008](#doc-008)、[DOC-021](#doc-021) | 注释/docstring 本地化 |
| PAIR-07 | [DOC-009](#doc-009)、[DOC-022](#doc-022) | 正文逐字相同 |
| PAIR-08 | [DOC-010](#doc-010)、[DOC-023](#doc-023) | 正文逐字相同 |
| PAIR-09 | [DOC-011](#doc-011)、[DOC-024](#doc-024) | 正文逐字相同 |
| PAIR-10 | [DOC-012](#doc-012)、[DOC-025](#doc-025) | 正文逐字相同 |
| PAIR-11 | [DOC-013](#doc-013)、[DOC-026](#doc-026) | 正文逐字相同 |
| PAIR-12 | [DOC-014](#doc-014)、[DOC-027](#doc-027) | 注释/docstring 本地化 |
| PAIR-13 | [DOC-015](#doc-015)、[DOC-028](#doc-028) | 列表缩进不同 |

## 原文片段


### DOC-001

[.claude/skills/add-reward-function/SKILL.md:36–37](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/.claude/skills/add-reward-function/SKILL.md#L36-L37)

```python
async def custom_rm(args, sample):
    return float_reward_or_reward_dict
```

### DOC-002

[.claude/skills/add-reward-function/SKILL.md:41–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/.claude/skills/add-reward-function/SKILL.md#L41-L42)

```python
async def custom_rm(args, samples):
    return list_of_rewards
```

### DOC-003

[docs/en/advanced/sglang-config.md:173–189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/advanced/sglang-config.md#L173-L189)

```python
from slime.rollout.sglang_rollout import get_model_url
from slime.utils.http_utils import post

async def my_generate(args, sample, sampling_params):
    # Route to the actor model (default)
    actor_url = get_model_url(args, "actor", "/generate")
    output = await post(actor_url, {"text": sample.prompt, "sampling_params": sampling_params})
    
    # Route to the reference model
    ref_url = get_model_url(args, "ref", "/generate")
    ref_output = await post(ref_url, {"text": sample.prompt, "sampling_params": sampling_params})
    
    # Route to the reward model (e.g., OpenAI-compatible API)
    reward_url = get_model_url(args, "reward", "/v1/chat/completions")
    reward_output = await post(reward_url, {...})
    
    ...
```

### DOC-004

[docs/en/advanced/sglang-config.md:402–431](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/advanced/sglang-config.md#L402-L431)

```python
from slime.rollout.sglang_rollout import get_model_url
from slime.utils.http_utils import post

async def generate_with_models(args, sample, sampling_params):
    """Generate using actor, score with reward model, compare with reference."""
    
    # Generate from actor
    actor_url = get_model_url(args, "actor", "/generate")
    actor_output = await post(actor_url, {
        "text": sample.prompt,
        "sampling_params": sampling_params,
        "return_logprob": True,
    })
    
    # Get reference logprobs for KL penalty
    ref_url = get_model_url(args, "ref", "/generate")
    ref_output = await post(ref_url, {
        "text": sample.prompt + actor_output["text"],
        "sampling_params": {"max_new_tokens": 0, "temperature": 0},
        "return_logprob": True,
    })
    
    # Score with reward model
    reward_url = get_model_url(args, "reward", "/v1/chat/completions")
    reward_output = await post(reward_url, {
        "model": "reward",
        "messages": [{"role": "user", "content": sample.prompt + actor_output["text"]}],
    })
    
    # ... process outputs and return Sample
```

### DOC-005

[docs/en/developer_guide/trace.md:60–74](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/developer_guide/trace.md#L60-L74)

```python
from slime.observability.trace_utils import trace_function


@trace_function("generate_and_rm", target="sample")
async def generate_and_rm(args, sample, sampling_params, evaluation=False):
    ...


@trace_function(
    "generate_and_rm_group",
    target="group",
    attrs_getter=lambda args, group, sampling_params, evaluation=False: {"group_size": len(group)},
)
async def generate_and_rm_group(args, group, sampling_params, evaluation=False):
    ...
```

### DOC-006

[docs/en/developer_guide/trace.md:90–96](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/developer_guide/trace.md#L90-L96)

```python
@trace_function(
    "custom_rollout_batch",
    target="samples",
    attrs_getter=lambda samples, **_: {"batch_size": len(samples)},
)
async def custom_rollout_batch(samples, **kwargs):
    ...
```

### DOC-007

[docs/en/developer_guide/trace.md:107–111](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/developer_guide/trace.md#L107-L111)

```python
from slime.observability.trace_utils import build_sglang_meta_trace_attrs, trace_span

with trace_span(sample, "sglang_generate") as span:
    output = await post(url, payload)
    span.update(build_sglang_meta_trace_attrs(output["meta_info"]))
```

### DOC-008

[docs/en/get_started/agent.md:41–52](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/agent.md#L41-L52)

```python
from slime.agent.adapters import AnthropicAdapter

adapter = AnthropicAdapter(
    tokenizer=tokenizer,
    sglang_url=sglang_url,
    tool_parser=tool_parser,
    reasoning_parser=reasoning_parser,
)

adapter.open_session(session_id, sampling_defaults=sampling_params)
# Agent client sends requests to adapter.app.
segments = await adapter.finish_session(session_id)
```

### DOC-009

[docs/en/get_started/customization.md:77–88](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L77-L88)

```python
from slime.data.transport import publish_rollout_async
from slime.rollout.base_types import finalize_rollout_groups


async def generate_stored_batch(args, rollout_id, data_source, completed_groups):
    refs = []
    async for group in completed_groups:
        ref = await publish_rollout_async(
            group, args, rollout_id, group=True, controller=data_source.controller
        )
        refs.append(ref)
    return finalize_rollout_groups(args, rollout_id, refs, controller=data_source.controller)
```

### DOC-010

[docs/en/get_started/customization.md:115–115](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L115-L115)

```python
async def custom_generate(args, sample: Sample, sampling_params: dict) -> Sample | list[Sample]
```

### DOC-011

[docs/en/get_started/customization.md:130–150](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L130-L150)

```python
import copy

from slime.utils.types import Sample


async def custom_generate(args, sample: Sample, sampling_params: dict) -> list[Sample]:
    segments = await run_agent_and_split_segments(args, sample, sampling_params)
    rollout_id = sample.rollout_id if sample.rollout_id is not None else sample.index

    samples: list[Sample] = []
    for segment in segments:
        s = copy.copy(sample)
        s.tokens = segment.tokens
        s.response = segment.response
        s.response_length = segment.response_length
        s.loss_mask = segment.loss_mask
        s.reward = segment.reward
        s.status = Sample.Status.COMPLETED
        s.rollout_id = rollout_id
        samples.append(s)
    return samples
```

### DOC-012

[docs/en/get_started/customization.md:167–167](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L167-L167)

```python
async def custom_rm(args, sample: Sample) -> float
```

### DOC-013

[docs/en/get_started/customization.md:172–172](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/customization.md#L172-L172)

```python
async def batched_custom_rm(args, samples: list[Sample]) -> list[float]
```

### DOC-014

[docs/en/get_started/quick_start.md:500–527](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/quick_start.md#L500-L527)

```python
async def generate(args, sample: Sample, sampling_params) -> Sample:
    # ... initialization ...
    prompt, full_response, loss_masks = sample.prompt, "", []

    for _ in range(max_turns):
        # 1. Model generates action
        model_output = await call_sglang(prompt + full_response, ...)
        # ... tokenization and appending ...
        loss_masks += [1] * len(model_tokens) # loss_mask = 1
        full_response += model_output

        # 2. Parse and execute action
        action, content = parse_action(model_output)
        if action == "search":
            # 3 & 4. Get and append observation results
            tool_output = await google_search(content)
            # ... tokenization and appending ...
            loss_masks += [0] * len(tool_tokens) # loss_mask = 0
            full_response += tool_output

        elif action == "answer":
            break # end loop

    # 7. Fill and return Sample object
    sample.response = full_response
    sample.tokens = ...
    sample.loss_mask = loss_masks
    return sample
```

### DOC-015

[docs/en/get_started/usage.md:356–385](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/en/get_started/usage.md#L356-L385)

```python
    async def generate(args, sample: Sample, sampling_params) -> Sample:
        global TOKENIZER
        if TOKENIZER is None:
            TOKENIZER = AutoTokenizer.from_pretrained(args.hf_checkpoint, trust_remote_code=True)

        # send request to router
        output = await post(
            f"http://{args.sglang_router_ip}:{args.sglang_router_port}/generate",
            {
                "text": sample.prompt,
                "sampling_params": sampling_params,
            }
        )

        prompt_tokens_ids = TOKENIZER(sample.prompt, add_special_tokens=False)["input_ids"]
        response_token_ids = TOKENIZER(output["text"], add_special_tokens=False)["input_ids"]

        # set sample
        sample.tokens = prompt_tokens_ids + response_token_ids
        sample.response_length = len(response_token_ids)
        finish_reason = output["meta_info"]["finish_reason"]["type"]
        if finish_reason == "length":
            sample.status = Sample.Status.TRUNCATED
        elif finish_reason == "abort":
            sample.status = Sample.Status.ABORTED
        else:
            sample.status = Sample.Status.COMPLETED
        sample.response = output["text"]

        return sample
```

### DOC-016

[docs/zh/advanced/sglang-config.md:173–189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/advanced/sglang-config.md#L173-L189)

```python
from slime.rollout.sglang_rollout import get_model_url
from slime.utils.http_utils import post

async def my_generate(args, sample, sampling_params):
    # 路由到 actor 模型（默认）
    actor_url = get_model_url(args, "actor", "/generate")
    output = await post(actor_url, {"text": sample.prompt, "sampling_params": sampling_params})
    
    # 路由到 reference 模型
    ref_url = get_model_url(args, "ref", "/generate")
    ref_output = await post(ref_url, {"text": sample.prompt, "sampling_params": sampling_params})
    
    # 路由到 reward 模型（如 OpenAI 兼容 API）
    reward_url = get_model_url(args, "reward", "/v1/chat/completions")
    reward_output = await post(reward_url, {...})
    
    ...
```

### DOC-017

[docs/zh/advanced/sglang-config.md:401–430](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/advanced/sglang-config.md#L401-L430)

```python
from slime.rollout.sglang_rollout import get_model_url
from slime.utils.http_utils import post

async def generate_with_models(args, sample, sampling_params):
    """使用 actor 生成，用 reward 模型打分，与 reference 比较。"""
    
    # 从 actor 生成
    actor_url = get_model_url(args, "actor", "/generate")
    actor_output = await post(actor_url, {
        "text": sample.prompt,
        "sampling_params": sampling_params,
        "return_logprob": True,
    })
    
    # 获取 reference logprobs 用于 KL penalty
    ref_url = get_model_url(args, "ref", "/generate")
    ref_output = await post(ref_url, {
        "text": sample.prompt + actor_output["text"],
        "sampling_params": {"max_new_tokens": 0, "temperature": 0},
        "return_logprob": True,
    })
    
    # 用 reward 模型打分
    reward_url = get_model_url(args, "reward", "/v1/chat/completions")
    reward_output = await post(reward_url, {
        "model": "reward",
        "messages": [{"role": "user", "content": sample.prompt + actor_output["text"]}],
    })
    
    # ... 处理输出并返回 Sample
```

### DOC-018

[docs/zh/developer_guide/trace.md:60–74](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/developer_guide/trace.md#L60-L74)

```python
from slime.observability.trace_utils import trace_function


@trace_function("generate_and_rm", target="sample")
async def generate_and_rm(args, sample, sampling_params, evaluation=False):
    ...


@trace_function(
    "generate_and_rm_group",
    target="group",
    attrs_getter=lambda args, group, sampling_params, evaluation=False: {"group_size": len(group)},
)
async def generate_and_rm_group(args, group, sampling_params, evaluation=False):
    ...
```

### DOC-019

[docs/zh/developer_guide/trace.md:90–96](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/developer_guide/trace.md#L90-L96)

```python
@trace_function(
    "custom_rollout_batch",
    target="samples",
    attrs_getter=lambda samples, **_: {"batch_size": len(samples)},
)
async def custom_rollout_batch(samples, **kwargs):
    ...
```

### DOC-020

[docs/zh/developer_guide/trace.md:107–111](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/developer_guide/trace.md#L107-L111)

```python
from slime.observability.trace_utils import build_sglang_meta_trace_attrs, trace_span

with trace_span(sample, "sglang_generate") as span:
    output = await post(url, payload)
    span.update(build_sglang_meta_trace_attrs(output["meta_info"]))
```

### DOC-021

[docs/zh/get_started/agent.md:41–52](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/agent.md#L41-L52)

```python
from slime.agent.adapters import AnthropicAdapter

adapter = AnthropicAdapter(
    tokenizer=tokenizer,
    sglang_url=sglang_url,
    tool_parser=tool_parser,
    reasoning_parser=reasoning_parser,
)

adapter.open_session(session_id, sampling_defaults=sampling_params)
# Agent client 向 adapter.app 发送请求。
segments = await adapter.finish_session(session_id)
```

### DOC-022

[docs/zh/get_started/customization.md:72–83](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L72-L83)

```python
from slime.data.transport import publish_rollout_async
from slime.rollout.base_types import finalize_rollout_groups


async def generate_stored_batch(args, rollout_id, data_source, completed_groups):
    refs = []
    async for group in completed_groups:
        ref = await publish_rollout_async(
            group, args, rollout_id, group=True, controller=data_source.controller
        )
        refs.append(ref)
    return finalize_rollout_groups(args, rollout_id, refs, controller=data_source.controller)
```

### DOC-023

[docs/zh/get_started/customization.md:100–100](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L100-L100)

```python
async def custom_generate(args, sample: Sample, sampling_params: dict) -> Sample | list[Sample]
```

### DOC-024

[docs/zh/get_started/customization.md:115–135](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L115-L135)

```python
import copy

from slime.utils.types import Sample


async def custom_generate(args, sample: Sample, sampling_params: dict) -> list[Sample]:
    segments = await run_agent_and_split_segments(args, sample, sampling_params)
    rollout_id = sample.rollout_id if sample.rollout_id is not None else sample.index

    samples: list[Sample] = []
    for segment in segments:
        s = copy.copy(sample)
        s.tokens = segment.tokens
        s.response = segment.response
        s.response_length = segment.response_length
        s.loss_mask = segment.loss_mask
        s.reward = segment.reward
        s.status = Sample.Status.COMPLETED
        s.rollout_id = rollout_id
        samples.append(s)
    return samples
```

### DOC-025

[docs/zh/get_started/customization.md:152–152](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L152-L152)

```python
async def custom_rm(args, sample: Sample) -> float
```

### DOC-026

[docs/zh/get_started/customization.md:157–157](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md#L157-L157)

```python
async def batched_custom_rm(args, samples: list[Sample]) -> list[float]
```

### DOC-027

[docs/zh/get_started/quick_start.md:506–533](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/quick_start.md#L506-L533)

```python
async def generate(args, sample: Sample, sampling_params) -> Sample:
    # ... 初始化 ...
    prompt, full_response, loss_masks = sample.prompt, "", []

    for _ in range(max_turns):
        # 1. 模型生成动作
        model_output = await call_sglang(prompt + full_response, ...)
        # ... tokenization and appending ...
        loss_masks += [1] * len(model_tokens) # loss_mask = 1
        full_response += model_output

        # 2. 解析并执行动作
        action, content = parse_action(model_output)
        if action == "search":
            # 3 & 4. 获取并追加观察结果
            tool_output = await google_search(content)
            # ... tokenization and appending ...
            loss_masks += [0] * len(tool_tokens) # loss_mask = 0
            full_response += tool_output

        elif action == "answer":
            break # 结束循环

    # 7. 填充并返回 Sample 对象
    sample.response = full_response
    sample.tokens = ...
    sample.loss_mask = loss_masks
    return sample
```

### DOC-028

[docs/zh/get_started/usage.md:358–387](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/usage.md#L358-L387)

```python
  async def generate(args, sample: Sample, sampling_params) -> Sample:
      global TOKENIZER
      if TOKENIZER is None:
          TOKENIZER = AutoTokenizer.from_pretrained(args.hf_checkpoint, trust_remote_code=True)
  
      # send request to router
      output = await post(
          f"http://{args.sglang_router_ip}:{args.sglang_router_port}/generate",
          {
              "text": sample.prompt,
              "sampling_params": sampling_params,
          }
      )
  
      prompt_tokens_ids = TOKENIZER(sample.prompt, add_special_tokens=False)["input_ids"]
      response_token_ids = TOKENIZER(output["text"], add_special_tokens=False)["input_ids"]
  
      # set sample
      sample.tokens = prompt_tokens_ids + response_token_ids
      sample.response_length = len(response_token_ids)
      finish_reason = output["meta_info"]["finish_reason"]["type"]
      if finish_reason == "length":
          sample.status = Sample.Status.TRUNCATED
      elif finish_reason == "abort":
          sample.status = Sample.Status.ABORTED
      else:
          sample.status = Sample.Status.COMPLETED
      sample.response = output["text"]
  
      return sample
```

### DOC-029

[examples/coding_agent_rl/README.md:194–197](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/README.md#L194-L197)

```python
await sb.exec(cmd, user=..., check=..., timeout=...)
await sb.write_file(sandbox_path, content_or_host_path, user=...)
await sb.read_file(sandbox_path, user=...)
async with E2BSandbox(...) as sb: ...
```
