# _AdapterService.__init__

- 源码定位：[examples/coding_agent_rl/generate.py:168–182](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L168-L182)，由助手核对。
- 首次接触：Step 4，2026-10-22 从 `open_session` 回查 Adapter 来源；本轮确认独立建卡。
- 最近认识更新：2026-10-24，用户表示对 AdapterService 的 init 已差不多了解，要求继续选择下一处；保留“大致理解”的层次，具体 HTTP 启动机制仍待接续。

- 本轮校准：2026-10-24，创建 Adapter 与启动 HTTP 的具体过程现由 `endpoint` 承接；旧版认识日期保留。[原完整卡片](../../../../../references/adapter-service-init-at-2f231865.md)归档。

对象总览见 [_AdapterService 类卡](../../../../classes/examples/coding_agent_rl/generate.py/_AdapterService.md)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_generate` 通过 `_AdapterService(args)` 取得服务对象；这里只看当前进程首次创建时的初始化。
2. **具体内容**：保存配置，加载 tokenizer，准备长度、解析器与 SGLang 地址，建立端点缓存，再调用 `endpoint` 准备默认 Agent 的服务。
3. **建议构建的心智模型**：

   > 先准备供多个端点使用的依赖，再准备默认端点；初始化完成后，调用方用 `state` 引用这个服务对象。

4. **调用代码**：

   ```python
   state = _AdapterService(args)  # _generate:256
   ```

   类调用取得实例；`__init__` 自身返回 `None`。已有服务由 `SingletonMeta` 复用，完整单例实现暂不展开。

## 本场景的输入与输出

对 `__init__`，这里重点看**传入的配置，最后变成了对象中的哪些字段**。`__init__` 自身返回 `None`；`state = _AdapterService(args)` 得到初始化后的服务对象。

本轮只看准备共用依赖的 169–174 行。下面保留原语句，补上紧邻注释；这里的 `self` 就是初始化完成后由 `state` 引用的服务对象。

```python
self.args = args  # 保存整份输入配置，供后续使用

# 模型路径 → 加载后的 tokenizer 对象
self.tokenizer = load_tokenizer(args.hf_checkpoint, trust_remote_code=True)

# 读取上下文长度并转为整数；未配置或为空时使用 0
self.max_context_len = int(getattr(args, "rollout_max_context_len", 0) or 0)

# 保存工具解析器的名称；未配置或为空时使用 None
self.tool_parser = getattr(args, "sglang_tool_call_parser", None) or None

# 保存思考解析器的名称；未配置或为空时使用 None
self.reasoning_parser = getattr(args, "sglang_reasoning_parser", None) or None

# 模型服务的主机与端口 → URL 字符串
self.sglang_url = f"http://{args.sglang_router_ip}:{args.sglang_router_port}"
```

函数后半段还会初始化 `_endpoints`，委托 [endpoint](_AdapterService.endpoint.md) 准备默认端点，并保存 `adapter`、`adapter_url`、`app_handle`。这里先保留这个交接位置，具体过程接下来单独读。

<details>
<summary>完整构造场景与两段源码（按需展开）</summary>

静态构造：默认 Agent 为 `claude_code`，tokenizer 路径为 `/models/example-model`，上下文上限为 `4096`，模型服务为 `127.0.0.1:30000`；解析器为 `None`。假设配置齐备，默认端点在 `0.0.0.0:18001` 成功监听，对外主机为 `192.0.2.10`。这些值延续原卡片的教学用途，没有运行初始化。

**输入**：`args` 及模块中的 `CONFIG`、`AGENT_NAME`；`self` 是正在初始化的服务对象。

**输出与副作用**：返回 `None`，依赖与默认端点保存在对象字段里。类调用完成后，调用方取得 `state`。

```text
state -> _AdapterService
  tokenizer -> T
  max_context_len = 4096
  sglang_url = "http://127.0.0.1:30000"
  _endpoints["claude_code"] -> (A, "http://192.0.2.10:18001", H)
  adapter -> A
  adapter_url = "http://192.0.2.10:18001"
  app_handle -> H
```

`A` 是 AnthropicAdapter，`H` 是 AppHandle；其余字段见类卡。Adapter 的 `store` 在这里尚未登记本次执行的 sid。

### 1. 准备共用依赖（169–180）

```python
self.args = args
self.tokenizer = load_tokenizer(args.hf_checkpoint, trust_remote_code=True)
self.max_context_len = int(getattr(args, "rollout_max_context_len", 0) or 0)
self.tool_parser = getattr(args, "sglang_tool_call_parser", None) or None
self.reasoning_parser = getattr(args, "sglang_reasoning_parser", None) or None
self.sglang_url = f"http://{args.sglang_router_ip}:{args.sglang_router_port}"
if not CONFIG.adapter_public_host:
    raise RuntimeError(
        "ADAPTER_PUBLIC_HOST is not set. Export it to the host IP that "
        "sandboxes can reach for reverse-connection to the adapter; "
        "without it the sandbox cannot dial back and the rollout aborts."
    )
```

- 保存原配置和加载后的 tokenizer；解析器字段保存名称或 `None`。
- `sglang_url` 是 Adapter 将访问的模型服务地址；构造该字符串没有启动模型服务。
- 公开地址缺失会抛出异常；本轮沿配置齐备的路径。

### 2. 准备默认端点，保存其三项结果（181–182）

```python
self._endpoints = {}
self.adapter, self.adapter_url, self.app_handle = self.endpoint(AGENT_NAME)
```

[endpoint](_AdapterService.endpoint.md)创建默认 Adapter、委托 HTTP 启动并返回三元组。本方法将结果同时保留为默认字段；完成后回到 `_generate:256`。

随后 `_generate:259` 再按本次 `agent_name` 取得端点。若仍为默认的 `claude_code`，会命中刚建立的缓存；若选用另一种 Agent，则由 `endpoint` 处理对应条目。

</details>

## 我的直接表述（原话）

用户在确认第一个阅读入口后提出：

> 好的那么这里是否应该先给一个generate的adapter service先单独开一个短期记忆了呢

以上是当时独立建卡的请求。随后用户对当前职责作出首次复述：

> 好的简单来说这里的adapter cls就是把需要的tokenizer还有对应的sglang url的服务等一系列的内容都放到这个adapter里面
> 更多的是用来提前考虑清楚这里的tokenizer也好sglang也好还是tool parser也好到底应该放在哪里对吗？
> 也就是把这里的基础服务层先搭建好

2026-10-24，用户看过共用依赖段后表示：

> 好的简单来说就是吧一开始的配置的部分都放在adapter sevice了
> 那么现在看一下下面的这个endpoint吧

这次表达对应初始配置与共用依赖的集中保存，未扩大为整个初始化或端点机制已经掌握。接续见[endpoint 的缓存判断](../../../../../04-flow.md#endpoint-cache-entry)。

2026-10-24，用户进一步反馈：

> 好的 我对于这里的的adapterservice init差不多了解了
> 那么继续吧

这是对初始化整体的大致理解反馈，后续启动函数与地址获取仍是用户明确提出的疑问。

## 尚不清楚

- 用户是否已区分服务对象 `state`、其中的 Adapter，以及不同方法中的 `self`，仍需后续实际反馈。
- 依赖已初步联系到 Adapter 的准备职责；对象、地址、解析器名称以及服务启动的区别已补充说明，尚未收到进一步确认。
- tokenizer 加载、Adapter 构造内部、HTTP 服务的线程启动与回收、单例复用机制，本轮只定位职责与交接，尚未逐段展开。
- 此处选择 `None` 作为解析器名称和阈值的构造输入；具体模型与轨迹策略应如何配置不在本轮范围内。

<details>
<summary>来源、历史与验证范围</summary>

- 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本函数与调用现场见开头和当前类卡。
- [原版完整卡片](../../../../../references/adapter-service-init-at-2f231865.md)保留旧的直接创建路径、构造输入与来源；原话和未解决的问题继续保留在当前卡片中。
- [本轮形成过程](../../../../../04-flow.md#adapter-service-startup-reading)。本轮静态核对，没有加载 tokenizer、实例化完整 Adapter、启动 HTTP 服务或执行模型。

</details>
