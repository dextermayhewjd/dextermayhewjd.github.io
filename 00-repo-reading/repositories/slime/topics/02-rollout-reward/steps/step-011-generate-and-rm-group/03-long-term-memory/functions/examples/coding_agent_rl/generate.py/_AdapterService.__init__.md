# _AdapterService.__init__

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 02-short-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- Step 8 调取：2026-10-23，从[本步长期快照](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)调取完整记录。当前只接清应用、监听与 `request → body` 的来路；原话、认识时间与未解问题保留。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[examples/coding_agent_rl/generate.py:138–179](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L138-L179)，由助手核对。
- 首次接触：Step 4，2026-10-22 从 `open_session` 回查 Adapter 来源；本轮确认独立建卡。
- 最近认识更新：2026-10-22，用户首次将 tokenizer、SGLang 地址和解析器与 Adapter 的提前准备联系起来，概括为“把基础服务层先搭建好”；依赖装配与服务启动的区别由助手补充，尚待后续反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页输入输出整理，作为理解参考。

1. **使用场合**：`generate` 调用 `_AdapterService(args)` 取得服务状态。当前看该类在当前进程首次初始化的情况；随后 `generate` 通过 `state.adapter` 登记会话和导出样本，运行中的 CLI 模型请求也由这个 Adapter 处理。

2. **具体内容**：读取模型与服务配置，加载 tokenizer，准备长度、解析器名称和 SGLang 地址；创建具体 Adapter，启动它的 HTTP 应用，保存服务句柄与对外地址。方法返回 `None`，准备结果保存在服务对象的属性中。

3. **建议构建的心智模型**：

   > `_AdapterService.__init__` 为 `generate` 准备一份 Adapter 服务状态：把 tokenizer、具体 Adapter、HTTP 服务句柄和访问地址组织在同一个对象里。
   >
   > 调用方把这个服务对象称为 `state`，再通过 `state.adapter` 使用其中的 Adapter。当前重点是认清这两个对象的关系。

4. **调用代码**（`generate.py:184、195–199`，省略中间准备与登记参数）：

   ```python
   state = _AdapterService(args)
   ...  # 取得题目信息、检查并取得 session_id
   state.adapter.open_session(...)
   ```

   首次创建时执行本方法；已有服务对象时由 `SingletonMeta` 复用，不会每次进入 `generate` 都重新初始化。这里先保留这个边界，单例机制暂不展开。

## 本场景的输入与输出

教学构造：沿当前 Claude Code / `AnthropicAdapter` 路径，假设 tokenizer 加载和 HTTP 服务启动成功。下列路径、IP 与端口用于展示字段关系，不是本轮真实运行配置；输出按源码静态推导。

**输入**：`args` 是携带配置属性的对象；本方法还读取模块中已选定的 `ADAPTER_CLS` 和 `CONFIG`。`self` 是正在初始化的服务对象。相关字段如下：

```text
args 的相关属性：
    hf_checkpoint = "/models/example-model"
    rollout_max_context_len = 4096
    sglang_router_ip = "127.0.0.1"
    sglang_router_port = 30000
    sglang_tool_call_parser = None
    sglang_reasoning_parser = None

模块中已选定的值：
    ADAPTER_CLS = AnthropicAdapter
    CONFIG.adapter_public_host = "192.0.2.10"
    CONFIG.adapter_bind_host = "0.0.0.0"
    CONFIG.adapter_port = 18001
    CONFIG.fork_merge_threshold = None
```

**输出与副作用**：`__init__` 本身返回 `None`。类调用完成后，`generate` 取得服务对象并命名为 `state`；此时已经启动 Adapter 的 HTTP 服务。下面只展示与当前交接相关的属性，假定服务成功监听指定端口：

```text
state：_AdapterService 对象
├─ tokenizer → 加载得到的 tokenizer 对象 T
├─ max_context_len = 4096
├─ tool_parser = None
├─ reasoning_parser = None
├─ adapter → AnthropicAdapter 对象
│  ├─ tokenizer → 同一个对象 T
│  ├─ sglang_url = "http://127.0.0.1:30000"
│  └─ store = {}                     # 此时尚未调用 open_session
├─ app_handle → AppHandle，port = 18001；其余字段省略
└─ adapter_url = "http://192.0.2.10:18001"
```

- `state` 和 `state.adapter` 是两个对象：前者保存服务准备结果，后者负责会话和模型请求等行为。
- 两个地址有不同用途：Adapter 用 `sglang_url` 请求模型；后续 Harness 把 `adapter_url` 交给 CLI，让 CLI 请求 Adapter。
- 本方法中尚未登记任何 `sid`；后续 [open_session](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) 才向这个 Adapter 的 `store` 添加本次执行的配置。

### 整体处理位置

| 源码范围 | 本函数的处理 | 本轮深度 |
| --- | --- | --- |
| 139–149 | 加载 tokenizer、准备长度与解析器名称、拼出模型服务地址；检查对外主机地址 | 知道给下一段准备了哪些值；加载机制暂不展开 |
| 150–156 | 创建具体 Adapter，保存到服务对象的 `adapter` 属性 | **本轮展开**：创建什么、接收哪些已有值、结果保存在哪里 |
| 161–179 | 启动 Adapter 的 HTTP 应用，保存句柄和对外地址，记录日志 | 保留输出与副作用；线程和网络内部暂不展开 |

### 本轮展开：已有配置 → 服务对象持有的 Adapter（150–156）

```python
self.adapter = ADAPTER_CLS(
    tokenizer=self.tokenizer,
    sglang_url=sglang_url,
    tool_parser=self.tool_parser,
    reasoning_parser=self.reasoning_parser,
    fork_threshold_tokens=CONFIG.fork_merge_threshold,
)
```

- `ADAPTER_CLS` 在本场景是 `AnthropicAdapter`，由文件开头的 `_AGENTS` 根据 `SWE_AGENT` 选定。
- 进入这段时，tokenizer、SGLang 地址和解析器名称已经由前段准备好；这里把这些值交给 Adapter，并传入配置中的轨迹分叉合并阈值。传入的是已加载的 tokenizer 对象、模型服务的地址字符串，以及解析器名称（或 `None`）。
- `ADAPTER_CLS(...)` 创建具体 Adapter 实例；赋值将它保存在当前服务对象的 `adapter` 属性中。这里的 `self` 是服务对象，调用方随后通过 `state.adapter` 取得同一个 Adapter。
- 这些依赖为后续处理请求提供条件：用 tokenizer 编码和解码、按 SGLang 地址请求生成、根据解析器名称解释输出。本段没有启动 SGLang 模型服务；Adapter 构造时还会准备会话容器、轨迹管理器和 HTTP 应用，内部暂不展开。
- 本段结束后，本方法继续用 `self.adapter.app` 启动 HTTP 服务。等整个初始化完成，才回到 `generate` 执行后续准备；进入 `open_session` 时，该方法的 `self` 才指向 Adapter。

若没有配置 `CONFIG.adapter_public_host`，源码在创建 Adapter 前抛出 `RuntimeError`；本页输入选择了配置齐备的正常路径。

## 我的直接表述（原话）

用户在确认第一个阅读入口后提出：

> 好的那么这里是否应该先给一个generate的adapter service先单独开一个短期记忆了呢

以上是当时独立建卡的请求。随后用户对当前职责作出首次复述：

> 好的简单来说这里的adapter cls就是把需要的tokenizer还有对应的sglang url的服务等一系列的内容都放到这个adapter里面
> 更多的是用来提前考虑清楚这里的tokenizer也好sglang也好还是tool parser也好到底应该放在哪里对吗？
> 也就是把这里的基础服务层先搭建好

## 尚不清楚

- 用户是否已区分服务对象 `state`、其中的 Adapter，以及不同方法中的 `self`，仍需后续实际反馈。
- 依赖已初步联系到 Adapter 的准备职责；对象、地址、解析器名称以及服务启动的区别已补充说明，尚未收到进一步确认。
- tokenizer 加载、Adapter 构造内部、HTTP 服务的线程启动与回收、单例复用机制，本轮只定位职责与交接，尚未逐段展开。
- 此处选择 `None` 作为解析器名称和阈值的构造输入；具体模型与轨迹策略应如何配置不在本轮范围内。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。函数与调用现场见 [generate.py:138–199](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L138-L199)；类型选择见 [45–52 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L45-L52)。
- Adapter 保存参数和初始化空 store 的依据：[BaseAdapter.__init__:141–175](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L141-L175)；实际类型关系见 [AnthropicAdapter:39–41](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L39-L41)。
- 后续使用这些依赖的入口：[_run_turn:341–352](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341-L352)，解析器配置以 `tool_parser_name` 与 `reasoning_parser_name` 传给解析函数。
- HTTP 启动合同与句柄：[run_app_in_thread:46–98](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/aiohttp_threaded.py#L46-L98)。首次创建与后续复用：[SingletonMeta:62–73](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/misc.py#L62-L73)。本轮只核对相关合同。
- 构造输入、对象属性与地址均为静态示意；没有执行本初始化方法，没有加载示例路径、启动新的 HTTP 服务、请求模型或运行沙箱。本站 Hugo 预览不属于上述 Adapter 的运行证据。
- 形成过程：[Step 4 · 首个入口推荐](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#first-entry-adapter-service)、[Step 4 · 独立记录服务初始化](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#adapter-service-function-card)、[Step 4 · 依赖准备与服务启动的区别](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#adapter-dependency-restatement)。

</details>

<details>
<summary>同名旧快照与继承边界</summary>

[Step 009 的 03 完整旧快照](../../../../../../step-010-generate-and-rm/references/inherited-step009-long/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)另行保留。本页采用上一步 02 的记录；旧版的表述、未知和证据没有删除，版本差异不在本轮强行统一。

</details>
