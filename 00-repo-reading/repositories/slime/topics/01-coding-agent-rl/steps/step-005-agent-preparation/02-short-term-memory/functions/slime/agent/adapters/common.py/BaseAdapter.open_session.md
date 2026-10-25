# BaseAdapter.open_session

- 源码定位：[slime/agent/adapters/common.py:275–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)。
- 首次接触：Step 4，2026-10-22 首次展开；旧步骤编号保留当时语境。
- 最近认识更新：2026-10-24，用户已概括 Adapter 通过 store 按 session id 创建并管理 Session；明确暂不展开 Session 内部字段。
- 本轮源码校准：2026-10-24，补入模板选项与追踪引用，沿同一个编号例子观察登记；[旧版完整卡片](../../../../../../references/open-session-at-2f231865.md)保留原话、字段与验证。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_generate` 已取得 Adapter 和本次执行编号，在运行 Agent 之前登记会话状态。
2. **具体内容**：检查重复 sid，整理传入配置，创建 Session 并保存到 `self.store[sid]`；正常返回 `None`。
3. **建议构建的心智模型**：

   > 用已有编号，在当前 Adapter 中登记这次执行要使用的 Session；后续请求通过同一个 sid 取用。

4. **调用代码**（`_generate:270–279`）：

   ```python
   adapter.open_session(
       session_id,
       trace=import_trace(export_trace(bind_trace(base_sample)), base_sample.trace),
       sampling_defaults=sampling_params,
       max_context_tokens=state.max_context_len,
       apply_chat_template_kwargs={
           **(getattr(args, "apply_chat_template_kwargs", None) or {}),
           **(base_sample.apply_chat_template_kwargs or {}),
       },
   )
   ```

   `adapter` 来自前面的 `state.endpoint(agent_name)`；此处沿用 AnthropicAdapter 继承的共同实现。进入方法后，`self` 就是这个 Adapter，`sid` 对应已取得的 `session_id`。调用方如何构造 trace 和模板选项，本轮先按准备好的输入使用。

## 本场景的输入与输出

接住 [_session_id 的例子](../../../../examples/coding_agent_rl/generate.py/_session_id.md)：`instance_id="demo-1"`，两个索引为 0，得到 `sid="cagent-demo-1-0-0"`。下面采用无追踪引用、空模板附加选项的教学构造，只验证登记效果；实际调用的输入由上面的调用方提供。

**输入与调用前状态**：

```python
sid = "cagent-demo-1-0-0"
sampling_defaults = {"temperature": 0.7, "top_p": 0.9}
max_context_tokens = 4096
apply_chat_template_kwargs = {}
trace = None
self.store = {}  # 仅表示本例调用前的状态；本函数不会重置整个 store
```

**返回值**：`None`。**保存结果**：`self.store[sid]` 是新建的 Session，其字段为：

```python
Session(
    sampling_defaults={"temperature": 0.7, "top_p": 0.9},
    max_context_tokens=4096,
    apply_chat_template_kwargs={},
    prompt_prefixes=[],
    trace=None,
)
```

`prompt_prefixes` 由 Session 的默认工厂建立，本函数没有传入它。字段定义见 [Session 类卡](../../../../../classes/slime/agent/adapters/common.py/Session.md)。sid 是字典的键，不是 Session 的字段；题目描述、镜像和工作目录仍由 `base_sample` / `md` 承载。

### 用现成编号创建并登记 Session（284–292）

```python
"""Register a fresh per-sid Session; sids must be unique."""
if sid in self.store:  # 防止覆盖已登记的同名会话
    raise ValueError(f"session_id {sid!r} already exists; sids must be unique per agent run")
self.store[sid] = Session(  # 新建会话状态，用现成的 sid 关联
    sampling_defaults=dict(sampling_defaults or {}),
    max_context_tokens=int(max_context_tokens or 0),
    apply_chat_template_kwargs=dict(apply_chat_template_kwargs or {}),
    trace=trace,
)
```

- 同一个 sid 已存在时抛出 `ValueError`，原记录保留。
- 两个 `dict(...)` 各创建一份顶层字典，长度转为整数；trace 引用直接保存。
- 先由 `Session(...)` 创建对象，再赋给 `self.store[sid]`。本例完成后，用同一个 sid 能取回这份状态。
- HTTP 服务已经由前面的 endpoint 准备好；此处完成当前进程内的状态登记。

### 这份状态随后由谁使用

| 位置 | 与本步的交接 |
| --- | --- |
| [_run_turn:405–413](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L405-L413) | 按 sid 取得 Session，供本次模型请求使用；具体配置消费不在这里展开 |
| [finish_session](../../../../../../03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) | 会话结束时取出并移除 Session，将长度配置交给轨迹导出 |

本方法结束后返回 `_generate`，随后进入执行沙箱的准备。本轮在登记后的对象状态处停下。

## 我的直接表述（原话）

2026-10-24，用户对登记与管理关系的整体表述：

> 好的我目前差不多大概都清楚了这里的一系列的问题了
> 我简单的理解是 这里在adapter部分的stone里面给每一个这样子拿到了session id的 单独开一个session
> 简单的来说就是把这个管理到底有哪些session的部分交给这里的adapter
> 我是这么理解的
> 至于这里面到底是session到底包含了什么就暂时不是特别像弄清楚和知道了

本轮已表述的核心关系是 `adapter.store[sid] → Session 对象`。具体到本方法，是带着尚未登记的 sid 调用 open_session 时创建并保存对象；已有 sid 会报重复。Session 的内部字段按用户决定保留为后续参考。

以下保留旧版本阅读中的原话；新版字段和源码说明不代替个人认识。

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

- 登记与管理关系已有整体表述；Session 的具体内容及其与题目信息、轨迹的边界，按用户要求暂缓展开。
- 模板选项、追踪引用和默认前缀列表的具体用途保留为后续参考，不计为本轮已掌握。
- 配置如何参与每轮生成、前缀接续和样本导出，按后续问题回查，不以登记完成代替机制掌握。

<details>
<summary>来源、版本与验证范围</summary>

- 当前提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[调用方](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L269-L283)、[Session 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L45-L57)。
- [旧版完整卡片](../../../../../../references/open-session-at-2f231865.md)保留 `2f231865` 的两字段场景及 2026-10-22 验证；它们不作为新增字段已经验证的证据。
- [本轮接续与核对](../../../../../../04-flow.md#open-session-current-entry)。未创建完整 Adapter、HTTP 服务、模型或沙箱；参数值是教学构造。

</details>
