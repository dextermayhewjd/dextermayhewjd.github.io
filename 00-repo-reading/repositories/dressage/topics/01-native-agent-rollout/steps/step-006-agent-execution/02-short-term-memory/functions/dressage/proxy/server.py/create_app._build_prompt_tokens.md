# create_app 内的 _build_prompt_tokens

- 源码：`dressage/proxy/server.py:1665`，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次独立建卡：2026-11-17，Step 006；从 pipeline 第 2 段的回查说明拆出。
- 当前状态：用户希望定位文字转 token 的位置；以下为助手静态核对，未验证个人已掌握，也未实际运行 tokenizer。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：pipeline 已得到规范化消息、工具定义及历史 route，需要构建这次推理的 token 输入。
2. **具体内容**：根据模式和历史条件选择完整分词或 TITO 历史 token 合并，并返回输入 token 与记录所需的附加字段。
3. **心智模型**：本函数决定“怎样构建 token”；真正调用 tokenizer 的语句位于下游。本卡先追首条请求的完整分词分支。
4. **调用现场**：来自 [pipeline 第 2 段](create_app._chat_completions_pipeline.md#pipeline-prepare-input)，返回后读取 input_ids，再交给第 3 段生成调用。

## 本场景的输入与输出

**场景**：沿用父卡的 TITO 模式、会话首条有效请求，没有可复用的 base_step。输入为 `session`、`route`、`lineage_segment_boundary_before`、`normalized_request_messages` 和 `tools`。

### ① 选中完整分词分支

```python
# 源码裁剪：保留首请求的选择条件和返回；后续 TITO 分支未展开。
base_step = (
    None
    if route.base_step_id is None
    else session.steps_by_id.get(route.base_step_id)
)
if (
    token_build_mode != "tito"
    or base_step is None                 # 当前首请求命中这里
    or lineage_segment_boundary_before
):
    input_ids = _full_prompt_token_ids(
        normalized_request_messages=normalized_request_messages,
        tools=tools,
    )
    return {
        "input_ids": input_ids,          # 真正交给生成调用的整数 token IDs
        "context_delta_ids": list(input_ids),  # 本分支把整份输入作为上下文增量
        "used_tito_for_prompt": False,
        "tito_incremental_tokenization_failed": False,
    }
```

### ② 定位实际 tokenizer 调用

```text
_full_prompt_token_ids                           # server.py:1653
  → mask_builder.tokenize_messages               # prompt_assistant_mask.py:166
      → _apply_chat_template(..., tokenize=True)
          → self._tokenizer.apply_chat_template  # :145
  ← list[int]
```

`tokenize=True` 要求按对话模板处理消息并完成分词；工具定义也作为输入传入。这里先认清委派关系，不逐层深入模板与 tokenizer 算法。

### ③ 带着结果返回父函数

```python
# 回到 _chat_completions_pipeline：这句取结果，不做分词。
input_ids = prompt_payload["input_ids"]
# 随后生成阶段把 input_ids 交给 generate_preemptible。
```

**接入边界**：MiniMax 消息接口的候选分支在父函数仍保留 messages/tools、尚未进入 token 构建路径时；不是把本函数输出的整数直接当成消息发送。初始化与结果记录兼容性仍待处理，这里没有实现 API 适配。

**其余分支只定位**：有可复用历史且满足条件时走 TITO `merge_tokens`；合并失败会回退完整分词。本卡不将首请求路径冒称全部调用行为。

## 我的直接表述（原话）

> 主要是哪里从文字被tokenizer 变成token的是需要了解的对吗？

> 我的意思是把这个分之在这里单独拆开成为一个函数卡片同时的放在scope的3.2里面？

## 尚不清楚

- 具体模板如何排列消息、工具定义及生成提示，尚未展开。
- TITO 历史 token 合并机制尚未展开。
- 本轮没有真实 tokenizer 输出；不填写虚构的 token 编号。

<details>
<summary>来源与验证边界</summary>

- [分支及完整分词委派](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1653)。
- [tokenize_messages 及 tokenize=True](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/last_step/prompt_assistant_mask.py#L166)。
- [实际调用 tokenizer 的包装](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/last_step/prompt_assistant_mask.py#L119)。
- 本地静态源码核对；未修改 Dressage、未运行模型或 API。

</details>
