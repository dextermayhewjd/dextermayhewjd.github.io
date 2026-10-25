# Session

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/adapters/common.py/Session.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/classes/slime/agent/adapters/common.py/Session.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/adapters/common.py:33–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L33-L42)，由助手核对；记录对象是 dataclass。
- 首次接触：Step 4，先在 open_session 中接触，随后单独展开字段与构造；原对象参考的来源一并保留。
- 最近认识更新：2026-10-22，用户提出“per session 的 state”的理解，并确认生成类卡片；实例、变量名与会话状态范围的区别由助手补充，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、源码和本页构造例子整理，作为理解参考。

1. **使用场合**：`open_session` 为本次 Agent 执行登记配置时，创建一个 Session 实例，保存到当前 Adapter 的 `store[sid]` 中，供后续模型请求使用。

2. **具体内容**：定义两项会话配置：`sampling_defaults` 保存采样默认值，`max_context_tokens` 保存上下文长度配置。同一 sid 的后续请求取用这份配置；结束时 `finish_session` 取走它，并读取长度配置用于导出。

3. **建议构建的心智模型**：

   > Session 的实例承载某次 Agent 执行的配置状态（per-session state）：采样默认值和上下文预算。
   >
   > 类定义结构，`Session(...)` 创建实例，`store[sid]` 把实例关联到这次执行。它只保存会话状态中的配置部分，轨迹和正在执行的请求由其他容器管理。

4. **调用代码**（`open_session:220–223`，构造实例并由调用方登记）：

   ```python
   self.store[sid] = Session(
       sampling_defaults=dict(sampling_defaults or {}),
       max_context_tokens=int(max_context_tokens or 0),
   )
   ```

## 本场景的输入与输出

沿用编号 `cagent-demo-1-0-0` 的场景，以及此前教学构造的采样参数和长度。这里观察 `Session(...)` 的构造结果；sid 由外层调用方持有，不是 Session 的构造参数。

**输入（构造参数）**：

```python
sampling_defaults = {"temperature": 0.7, "top_p": 0.9}
max_context_tokens = 4096
```

**输出（新建实例的形态）**：下面用教学变量名 `session` 指代这个对象。

```text
session → Session 实例
          ├─ sampling_defaults = {"temperature": 0.7, "top_p": 0.9}
          └─ max_context_tokens = 4096
```

- `Session` 是类，规定实例具有哪些字段；`Session(...)` 的结果是一个新实例。
- `session` 是引用实例的变量名。这里的名字用于解释；实际 `open_session` 将构造结果直接放入字典，没有先赋给同名局部变量。
- 类调用得到实例；外层 `open_session(...)` 的返回值仍为 `None`，登记结果留在 Adapter 中。

### 字段与默认值（33–42）

下面仅省略类的说明文字，保留完整字段定义：

```python
@dataclasses.dataclass
class Session:
    sampling_defaults: dict = dataclasses.field(default_factory=dict)
    max_context_tokens: int = 0
```

- `sampling_defaults` 未传入时，`default_factory=dict` 为新实例创建独立的空字典。
- `max_context_tokens` 的默认值为 `0`，具体怎样使用由生成与导出逻辑决定。
- `@dataclasses.dataclass` 根据字段生成初始化方法；这里没有另一个手写的 `Session.__init__` 函数体需要跳转。语法依据见[补充参考](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/references/session.md#session-dataclass-syntax)。

### 实例怎样关联到一次执行

把调用方的登记动作单独展开，等价于下面这一句；`session` 仍为上方教学变量名：

```python
self.store["cagent-demo-1-0-0"] = session
```

- **per-session 的关联由 store 建立**：sid 是字典的键，实例是对应的值；Session 自身没有 sid 字段。这里的一次 session 沿用本步约定，指某道题的一次 Agent 执行，可以包含多轮模型请求。
- **同一 sid 可以反复取用配置**：`_run_turn` 按 sid 取得实例，再把它交给生成函数；会话收尾时，`finish_session` 取出并移除它。
- **这两项配置不是会话的全部状态**：题目信息在 Sample / md 中，轨迹在 manager 中，未完成请求在 inflight 中。Session 本身不创建后台任务或 HTTP 连接。

读完返回 [BaseAdapter.open_session](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)，继续用“创建配置对象 → 按编号登记”理解原来的赋值。

## 我的直接表述（原话）

> 好的我也这么觉得 那么按照在这样子生成一下这个卡片吧
> 考虑一下这样子是否合适呢？
> 这里主要是一个per session的state对吧 我的意思是这里的session这个class产出的这个变量

## 尚不清楚

- 用户已经提出 per-session state 的概括；“类创建实例、变量引用实例”以及这里只覆盖配置状态的说明，尚待后续反馈。
- 两项配置怎样与每轮请求合并、怎样限制生成或样本长度，本卡保留用途与交接，具体规则继续回查已有函数记录。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。[Session 定义](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L33-L42)、[创建与登记](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L210-L223)、[模型请求取用](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L335-L344)、[导出时取走配置](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L261-L269)。
- 沿用原对象参考的 2026-10-22 局部验证：提取原 Session 类，在 Python 3.12.3 中核对字段、构造参数、本例属性和缺省值；两个缺省实例的字典互不共用，按 sid 登记后取得同一个对象。本轮整理类卡并静态复核源码，没有新增远端或完整 Adapter 运行。
- 原始理解过程：[Step 4 · 创建对象与按编号登记](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-object-reference)、[类型定义与记录归属](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-class-record-question)。本轮确认与复述见[Session 类卡片](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-class-card)。
- 原 reference 的主体转入本卡；[原路径](../../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/references/session.md)继续保留入口与 dataclass 的中英语法依据。记录位置变化不代表用户已经掌握全部实现。

</details>
