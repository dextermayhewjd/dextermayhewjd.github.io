# Session

- 源码定位：[slime/agent/adapters/common.py:46–57](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L46-L57)，记录对象是 dataclass。
- 首次接触：Step 4，2026-10-22 从 open_session 进入；旧编号保留历史语境。
- 最近认识更新：2026-10-24，用户将 Session 联系到 Adapter 的按编号管理关系，明确内部内容暂不展开；字段表保留为源码参考。

## 1. 对象职责

一个 Session 保存一次 Agent 执行的局部状态：采样和模板配置、上下文长度、提示词前缀记录，以及追踪引用。Adapter 用 `store[sid]` 把它关联到执行编号；Session 自身没有 sid 字段。

## 2. 字段总览

当前版本共五项字段。下表只展开本次创建时怎样得到它们。

| 字段 | 含义 | 本轮展开的用法 |
| --- | --- | --- |
| `sampling_defaults` | 会话的默认采样参数；默认独立空字典 | open_session 用 `dict(...)` 复制传入字典后保存 |
| `max_context_tokens` | 会话上下文长度配置；默认 0 | open_session 整理为整数；finish_session 后续读取它 |
| `apply_chat_template_kwargs` | 生成提示词时使用的模板附加选项；默认独立空字典 | open_session 用 `dict(...)` 复制后保存 |
| `prompt_prefixes` | 本会话已记录的提示词前缀信息，元素为 PromptPrefix；默认独立空列表 | open_session 不传此字段，初始化为 `[]`；后续记录与匹配流程按需回查 |
| `trace` | 本会话的 TraceHandle 引用或 None | open_session 直接保存传入引用；追踪内部不在这里展开 |

原始字段声明：

```python
@dataclasses.dataclass
class Session:
    sampling_defaults: dict = dataclasses.field(default_factory=dict)
    max_context_tokens: int = 0
    apply_chat_template_kwargs: dict = dataclasses.field(default_factory=dict)
    prompt_prefixes: list[PromptPrefix] = dataclasses.field(default_factory=list)
    trace: TraceHandle | None = None
```

只省略源码类说明文字。默认工厂在未传该字段时创建新的字典或列表；open_session 中显式的字典复制由调用者完成，不是 dataclass 自动复制全部参数。

## 3. 与登记函数的交接

本例沿用 `sid="cagent-demo-1-0-0"`。Session 接收配置并创建实例，随后 [open_session](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) 把它保存到 `store[sid]`；该函数本身返回 `None`。完整输入与登记后的五项字段见方法卡，避免在两张卡重复同一份例子。

题目描述、镜像和工作目录保存在 `base_sample` / `md`；完整轨迹由 manager 管理。提示词前缀记录属于会话局部的接续状态，不等于整棵轨迹树。

## 4. 我的直接表述（原话）

2026-10-24，用户最新表述（节选）：

> 简单的来说就是把这个管理到底有哪些session的部分交给这里的adapter
> 我是这么理解的
> 至于这里面到底是session到底包含了什么就暂时不是特别像弄清楚和知道了

完整原话见 [open_session 卡片](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)。本轮先保留 Session 作为按 sid 管理的会话对象这一层。

此前的表述：

> 好的我也这么觉得 那么按照在这样子生成一下这个卡片吧
> 考虑一下这样子是否合适呢？
> 这里主要是一个per session的state对吧 我的意思是这里的session这个class产出的这个变量

这是原两字段版本下的整体理解，保留其来源；新增字段尚无个人复述。

## 5. 尚不清楚

- 用户明确暂缓 Session 内部字段的理解；五项字段及其使用关系作为后续参考保留。
- 采样合并、模板选项、前缀匹配、追踪传播，以及它们与其他容器的边界，继续按实际阅读问题展开。

<details>
<summary>来源、版本与验证范围</summary>

- 当前固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[创建与登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)。
- 字段用途定位：[模板与前缀读取](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L100-L128)、[会话追踪](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L405-L413)、[追加前缀](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L470-L472)。这里只定位用途，未展开内部算法。
- [旧版完整类卡](../../../../../../references/session-at-2f231865.md)保留两字段场景、原始问题与 2026-10-22 的验证；[dataclass 语法参考](../../../../../../references/session.md#session-dataclass-syntax)继续保留。
- [本轮校准](../../../../../../04-flow.md#open-session-current-entry)只补齐登记所需的对象信息，没有将源码浏览记为用户掌握。

</details>
