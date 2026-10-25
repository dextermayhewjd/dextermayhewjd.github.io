# _AdapterService

## 1. 对象职责

`state` 引用这个服务对象。它保存共用依赖，并按 Agent 类型管理 Adapter、访问地址和 HTTP 服务句柄；每次执行的 Session 由具体 Adapter 保存。

**本轮关注：** 先认清 `state`，再沿 `__init__ → endpoint → run_app_in_thread` 看清服务怎样就绪。首次创建后，由 `SingletonMeta` 复用已有实例；单例内部暂不展开。

## 2. 字段总览

本类初始化建立 10 个实例字段；以下用法由助手按本轮源码整理。

| 字段 | 含义 | 本轮展开的用法 |
| --- | --- | --- |
| `args` | 原始配置对象 | `endpoint` 将它作为 `rollout_args` 传给 Adapter |
| `tokenizer` | 加载后的 tokenizer 对象 | 各 Adapter 复用它进行编解码 |
| `max_context_len` | 上下文长度配置；缺省为 0 | `_generate` 将它交给 `open_session` |
| `tool_parser` | 工具调用解析器名称或 `None` | 构造 Adapter 时传入 |
| `reasoning_parser` | 思考内容解析器名称或 `None` | 构造 Adapter 时传入 |
| `sglang_url` | 模型服务地址 | Adapter 用它请求模型生成 |
| `_endpoints` | `agent_name → (adapter, adapter_url, app_handle)` | `endpoint` 查找、创建并缓存；初始为 `{}` |
| `adapter` | 默认 Agent 对应的 Adapter | `__init__` 接住默认端点；本次执行另按 `agent_name` 选择 |
| `adapter_url` | 默认 Adapter 的对外访问地址 | 与默认 Adapter 一起保存；CLI 使用对应端点的地址 |
| `app_handle` | 默认 Adapter 的 HTTP 服务句柄 | 与默认 Adapter 一起保存，包含线程、循环、runner 和监听地址 |

`agent_name`、`adapter_cls` 和 `public_host` 是方法内的参数或局部变量，不是额外字段。`adapter_url` 与 `sglang_url` 指向不同服务。

## 3. 进入与返回

```python
state = _AdapterService(args)
agent_name = agent_name_for(base_sample)
adapter, adapter_url, _ = state.endpoint(agent_name)
adapter.open_session(...)
```

类调用取得服务对象；`__init__` 自身返回 `None`。`endpoint` 返回三元组，调用方分别取得本次 Adapter 与地址；`open_session` 的 `self` 是这个 Adapter。

方法入口：[初始化](../../../../functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) → [取得端点](../../../../functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md) → [后台启动 HTTP](../../../../functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md)。Adapter 自身的字段见[已有 BaseAdapter 类卡](../../../../../03-long-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)。

## 4. 我的直接表述（原话）

2026-10-24，用户提出需要先理清：

> 这里给出的是一个adapter service
> 也就是如何生成一个state
> 然后再从这里的state 拿到对应的adapter和adapter url
> 然后在在这里使用的adapter对应的open_session?

这表达了希望连接的对象关系，尚不据此认定已理解全部字段或服务启动机制。

2026-10-24，用户随后概括共用依赖的保存：

> 我简单的理解就是这里adapter service
> 就是吧tokenir啊 tool parser啊
> 还有reaseing parser啊
> 什么的全都放在一个地方了
> 这里是我的理解

这次已明确表达“将共用依赖集中保存”的认识。`tokenizer` 保存加载后的对象，两个 parser 字段保存名称配置；具体字段类型由源码核对，未作为用户原话。用户同时表示后台启动部分仍未理解。

## 5. 尚不清楚

- `endpoint` 与 `run_app_in_thread` 的具体交接正在本轮展开，尚无新的机制复述。
- `SingletonMeta` 的实现、HTTP 请求分派和服务停止回收仍未在本轮深入。

## 6. 来源

<details>
<summary>源码、形成过程与验证边界</summary>

- 固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[类与两个方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L167-L222)。
- 首次通过初始化认识服务对象：2026-10-22；本类卡于 2026-10-24 建立，字段说明来自静态源码。
- 最近认识更新：2026-10-24，用户概括共用依赖集中保存；[本次表述与小步阅读](../../../../../04-flow.md#thread-start-first-step)保留理解范围与未知。
- [本轮阅读与用户问题](../../../../../04-flow.md#adapter-service-startup-reading)；没有加载模型、创建真实 Adapter 或启动其 HTTP 服务。

</details>
