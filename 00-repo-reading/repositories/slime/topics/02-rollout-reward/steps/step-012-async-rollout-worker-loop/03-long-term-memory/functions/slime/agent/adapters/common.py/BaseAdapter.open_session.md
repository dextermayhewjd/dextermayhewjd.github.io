# BaseAdapter.open_session

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../step-011-generate-and-rm-group/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/adapters/common.py:210–223](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L210-L223)，由助手核对。
- 首次接触：Step 4，2026-10-22 首次展开；此前在 sid 的背景说明中定位过调用。
- 最近认识更新：2026-10-22，用户尝试总结按 sid 保存状态，并提出收拢为 task flow；本轮重点澄清 store 只保存两项会话配置，题目基础信息仍由 base_sample / md 承载。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页输入输出整理，作为理解参考。

1. **使用场合**：`generate` 已取得这次 Agent 执行的 `session_id`，在准备沙箱和启动 CLI 前，先给 Adapter 登记本次执行的配置。

2. **具体内容**：检查 sid 是否已在 `store` 中；未登记时创建 `Session`，保存采样默认值与上下文长度，放入 `self.store[sid]`。重复登记抛出 `ValueError`；正常返回 `None`。

3. **建议构建的心智模型**：

   > `open_session` 用已有的 sid，在 Adapter 中登记这次执行要使用的一份配置。
   >
   > 后面的请求按 sid 取出它；会话结束时，`finish_session` 再取走这份配置。消息与生成轨迹由 manager 另行保存。

4. **调用代码**（[generate.py:195–199](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L195-L199)）：

   ```python
   state.adapter.open_session(
       session_id,
       sampling_defaults=sampling_params,
       max_context_tokens=state.max_context_len,
   )
   ```

   当前 `state.adapter` 是 `AnthropicAdapter` 对象，`open_session` 沿用 `BaseAdapter` 中的实现；进入方法后，`self` 就是这个 Adapter。调用方的 `session_id` 在本函数里叫 `sid`，编号在调用前已经取得。

## 本场景的输入与输出

接住 [_session_id 的例子](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md)：题目 `demo-1`、两个索引均为 `0`，取得编号 `cagent-demo-1-0-0`，现在把它交给当前 Adapter 登记。本例尚未发起模型请求；采样参数与长度 `4096` 是为观察登记效果补充的教学构造值，不是前页测试样本自带的字段。

**输入与调用前状态**：

```python
sid = "cagent-demo-1-0-0"  # 来自调用方的 session_id
sampling_defaults = {"temperature": 0.7, "top_p": 0.9}  # 来自 sampling_params
max_context_tokens = 4096  # 来自 state.max_context_len
self.store = {}  # 当前 Adapter 在本例调用前的状态示意
```

**输出**：函数返回 `None`，新增的数据保存在 Adapter 上：

```python
self.store = {
    "cagent-demo-1-0-0": Session(
        sampling_defaults={"temperature": 0.7, "top_p": 0.9},
        max_context_tokens=4096,
    )
}
```

- **sid 是查找键**：整个字符串标识这次 Agent 执行；本函数直接用它登记，不拆解里面的题目编号或索引。含义沿用[此前的 sid 说明](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/references/session-id.md)。
- **Session 是保存的配置对象**：这里仅含 `sampling_defaults`（本次会话的采样默认值）与 `max_context_tokens`（上下文长度配置），自身没有 sid 字段。定义与构造例子见 [Session 类卡片](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/adapters/common.py/Session.md)。题目描述、镜像标识、工作目录等仍由 `base_sample` / `md` 承载；本函数接收编号与两项配置，没有把完整题目信息写进 Session。
- **store 是当前 Adapter 的字典**：`self.store` 就是调用方看到的 `state.adapter.store`。其他编号可以各有一份配置，本例只展示这一项。
- **返回值与保存结果分开**：函数返回 `None`；新增的 `Session` 留在字典中，后续可通过同一个 sid 取得。整个登记是本进程内的对象状态更新。

源码用以下连续语句完成登记（218–223）：

```python
if sid in self.store:
    raise ValueError(f"session_id {sid!r} already exists; sids must be unique per agent run")
self.store[sid] = Session(
    sampling_defaults=dict(sampling_defaults or {}),
    max_context_tokens=int(max_context_tokens or 0),
)
```

- 同一个 sid 已在字典中时直接报错，旧配置不会被覆盖。
- 正常路径复制传入的采样字典并整理长度值，创建一份 `Session`；省略可选参数时得到空字典与 `0`。
- `Session(...)` 根据配置创建对象，`self.store[sid] = ...` 再把对象登记到该编号下；编号只决定查找键，不参与 Session 的构造。

| 后续怎样接回已有函数 | 使用这份配置的地方 |
| --- | --- |
| [_run_turn](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 第 336 行按 sid 取得 Session，再传给 `call_sglang_generate`；请求携带本例编号时，使用刚登记的配置 |
| [finish_session](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) | 第 262–264 行取出并移除这份配置，读取长度上限后交给轨迹导出 |

本函数返回后，`generate` 下一项准备是 `boot_agent_sandbox`；本轮先把会话登记这一处接清。

## 我的直接表述（原话）

用户在推荐 Step 004 的范围和首个函数后确认：

> 好的那么目前看一下这里的这一步吧

在阅读编号函数后，用户进一步指定：

> 好的那么当前看一下这里的open_session吧
> 同时最好用上这里的session_id中的例子
> 重点看一下这里的open_session
> 感觉是涉及到了adapter中的open_session
> 我感觉需要单独看一下？

这些表述确认了阅读范围与例子的接续方式。随后，用户初步复述保存配置的作用，并追问对象本体：

> 1.那么这里感觉更多的就只是吧这里的id 啊 sampling的一系列内容存放在了这里的这个store里面？
> 这个store里面是根据这个id创建了一个session？
> 2. 那么这里再看一下这里的这个session到底是什么吧
> 我的意思是是否适合单独创建一个关于session的函数卡片？

阅读 Session 类卡片后，用户回到本函数复述：

> 好的那么现在重新看一下这里的这个open_session吧
> 我当前的理解就是
> 基于metadata和base sample的一系列信息
> 组成的一个编号
> 同时把sampling 的default和max context token
> 加载这个adapter里面
> 作为adapter的一个state来处理
> 这是我对于open session的理解了

随后，用户尝试总结并提出结束本步：

> 那么当前的这个step结束了吗？
> 我可以总结为把一个题目的基础信息都存放在adapter内部的store里面通过sid给出了编号之后
> 通过open_session的方式存放下来
>
> 这就是我对于open session的理解
> 适合写成一个task flow了吗？

## 尚不清楚

- 用户已把 sid、store 与登记动作联系起来；最新表述将保存范围概括为“题目的基础信息都存放”仍需校准。store 中的 Session 仅含两项配置，完整题目信息留在 `base_sample` / `md`；这一字段边界由助手补充，尚待后续反馈。
- 默认采样参数怎样与每轮请求参数合并、长度配置怎样用于生成和导出，本轮只保留交接；具体规则可回查前序 `call_sglang_generate` 与 `finish_session`。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。Session 定义见 [common.py:33–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L33-L42)；Adapter 的 store 初始化在第 156 行。后续读取见 [_run_turn:335–344](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L335-L344)。
- 当前实现来源：[generate.py:45–52](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L45-L52) 选择 Adapter，[150–156 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L150-L156)创建对象。[AnthropicAdapter:39](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L39) 与 [OpenAIAdapter:38](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/openai.py#L38) 均继承 BaseAdapter，未覆盖 `open_session`，共用本卡记录。
- 2026-10-22 此前局部执行：用 AST 原样提取 `Session` 与 `open_session`，以仅含 store 的对象承载原方法。使用旧例 `sid-demo` 核对返回 `None`、登记字段、采样字典独立复制、重复 sid 报错且旧对象保留，以及省略参数时得到 `{}` 和 `0`。
- 2026-10-22 接续编号例子时，沿相同方式提取 `_session_id`、`Session` 与 `open_session`，先取得 `cagent-demo-1-0-0`，再完成登记；实际返回值与字典字段和本页示意一致，采样字典为独立副本。两种 Adapter 对本方法的继承关系由 AST 静态核对。
- 没有初始化完整 Adapter、发送 HTTP 请求、运行模型、沙箱或训练。构造的参数值不是实际任务配置，局部验证不表示整条生命周期已经运行。
- 形成过程：[Step 4 · 会话配置从哪里来](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#open-session-first-reading)、[接住编号例子，看 Adapter 中的登记](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#open-session-same-example)、[创建对象与按编号登记](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-object-reference)。本步范围与此前推荐见[范围确认](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#scope-confirmed)。
- 最新复述与校正：[配置作为 Adapter 中的会话状态](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#open-session-state-restatement)。本次只静态复核同一固定版本的调用、编号规则与登记实现，沿用此前局部验证，没有新增运行实验。
- 本步收拢：[题目信息与会话配置的边界](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-registration-flow-closure)。跨函数交接见本步 [task flow](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/05-task-flow.md)，本卡继续保留单函数的输入、输出与状态变化。

</details>
