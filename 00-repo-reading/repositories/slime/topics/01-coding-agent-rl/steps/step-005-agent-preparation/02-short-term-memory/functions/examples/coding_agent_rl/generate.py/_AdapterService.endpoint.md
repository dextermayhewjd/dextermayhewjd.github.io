# _AdapterService.endpoint

- 源码定位：[generate.py:184–222](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L184-L222)。
- 首次接触：2026-10-24，用户要求沿 AdapterService 理清本方法与后台 HTTP 启动的关系。
- 最近认识更新：2026-10-24，用户表示整体大概清楚，概括了 Adapter、HTTP 服务及结果组合这条主线；AppHandle 的管理作用与实际处理请求的职责仍需精确区分。

对象背景见 [_AdapterService 类卡](../../../../classes/examples/coding_agent_rl/generate.py/_AdapterService.md)。这里的 `self` 是服务对象。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：初始化默认 Agent 的服务，或 `_generate` 根据本次 `agent_name` 取得对应 Adapter。
2. **具体内容**：优先返回缓存；未缓存时创建 Adapter、启动它的 HTTP 应用、组成对外地址，缓存并返回三元组。
3. **建议构建的心智模型**：

   > 按 Agent 类型取得一份可用端点：Adapter 对象 + 访问地址 + 后台服务句柄。创建只发生在缓存缺失的分支。

4. **调用代码**：

   ```python
   # __init__:182，初始化默认 Agent
   self.adapter, self.adapter_url, self.app_handle = self.endpoint(AGENT_NAME)
   # _generate:259，为本次任务取得端点
   adapter, adapter_url, _ = state.endpoint(agent_name)
   ```

## 本场景的输入与输出

静态构造例：`agent_name="claude_code"`，`self._endpoints={}`，服务共用依赖已经准备好；假设绑定 `0.0.0.0:18001` 成功，对外主机配置为 `192.0.2.10`。

**输入**：服务对象与 Agent 名称；`tokenizer`、模型服务地址和配置等从 `self` 取得。

**输出**：`(A, "http://192.0.2.10:18001", H)`。`A` 是新建的 AnthropicAdapter，`H` 是后台服务的 AppHandle。同时保存 `self._endpoints["claude_code"]`。这些值是源码推导，未启动真实服务。

<a id="endpoint-cache-entry"></a>

已有端点会直接复用。下面重点看首次创建时的三段职责；这里的 `self` 一直是 `_AdapterService` 实例，局部变量 `adapter` 指向新构造的 Adapter 对象。

<details>
<summary>前置：已有端点时直接返回（185–186）</summary>

`_endpoints` 按 Agent 名称保存三元组。第一次初始化时字典为空；同一端点已经准备好时直接返回。

```python
if agent_name in self._endpoints:  # 查找这个 Agent 类型是否已有端点
    return self._endpoints[agent_name]  # 交回缓存中的三元组，本次调用结束
```

</details>

<a id="endpoint-creation-stages"></a>

### 1. 用服务对象已有的依赖构造 Adapter（187–195）

```python
_, adapter_cls = _AGENTS[agent_name]  # 选出当前 Agent 对应的 Adapter 类
adapter = adapter_cls(  # 把服务对象中已准备的依赖交给新 Adapter
    tokenizer=self.tokenizer,
    sglang_url=self.sglang_url,
    tool_parser=self.tool_parser,
    reasoning_parser=self.reasoning_parser,
    fork_threshold_tokens=CONFIG.fork_merge_threshold,
    rollout_args=self.args,
)
```

- `_AGENTS` 将 `claude_code` 对应到 AnthropicAdapter，`codex` 对应到 ResponsesAdapter。
- `adapter` 已是 Python 对象，拥有 `app`；此时尚未经过下面的 HTTP 监听启动。

### 2. 启动这个 Adapter 的 HTTP 服务，取得句柄（200–209）

`run_app_in_thread` 在当前 Python 进程内启动后台线程，让 `adapter.app` 监听 HTTP 请求；收到请求后，由 Adapter 注册的逻辑处理消息。`app_handle` 是返回的服务句柄，保存线程、事件循环、runner 和实际监听端口。

<a id="listen-port"></a>

**端口在调用参数处看。** 下面是阅读用调用节选：

```python
app_handle = run_app_in_thread(
    adapter.app,
    host=CONFIG.adapter_bind_host,  # HTTP 服务的监听绑定地址
    port=CONFIG.adapter_port if not self._endpoints else 0,  # 请求监听的端口
    # 阅读节选：这里省略 thread_name 和 runner_kwargs
)
```

`port` 指定这个 HTTP 服务的监听入口。第一份端点使用配置的端口；后续新建端点传入 `0`，由系统分配可用端口。正常启动后，`app_handle.port` 保存实际监听端口。

<details>
<summary>完整调用与其余参数</summary>

```python
app_handle = run_app_in_thread(
    adapter.app,
    host=CONFIG.adapter_bind_host,
    port=CONFIG.adapter_port if not self._endpoints else 0,
    thread_name=f"{agent_name}-adapter",
    runner_kwargs={
        "handler_cancellation": True,
        "access_log_class": FilteredAccessLogger,
    },
)
```

`runner_kwargs` 传给 AppRunner，保留客户端断开时的取消配置和访问日志类；内部实现随后按需阅读。启动函数的完整过程见 [run_app_in_thread](../../../slime/agent/aiohttp_threaded.py/run_app_in_thread.md)。

</details>

### 3. 整理访问地址，保存并交回三项结果（210–222）

<a id="node-ip-port-thread"></a>
<a id="public-host-selection"></a>

**IP 在取得对外主机地址的语句处看。**

```python
# 自动取得当前节点 IP，或直接采用已配置的对外主机
public_host = get_current_node_ip() if CONFIG.adapter_public_host == "auto" else CONFIG.adapter_public_host
```

node 可以先理解为运行 Adapter 服务的计算节点，node IP 是它的网络地址。配置为 `"auto"` 时取得当前节点 IP；显式配置时直接使用该对外主机地址。

<a id="url-assembly"></a>

**最后只看两者怎样组合。** `public_host` 来自上面，`app_handle.port` 来自前一段启动结果：

```python
adapter_url = f"http://{public_host}:{app_handle.port}"  # 对外主机 + 实际端口 → 访问地址
# 省略日志
self._endpoints[agent_name] = (adapter, adapter_url, app_handle)  # 保存，供以后复用
return self._endpoints[agent_name]  # Adapter 对象、访问地址、服务句柄
```

例如 `public_host="192.0.2.10"`、`app_handle.port=18001` 时，得到 `http://192.0.2.10:18001`。这是示意值；URL 随后交给 Harness，供沙箱中的 CLI 访问。若调用者是 `__init__`，返回的三元组先保存为默认字段；若是 `_generate`，则解包为本次任务的局部变量。

<details>
<summary>可选回顾：请求怎样到达后台服务</summary>

```text
沙箱中的 CLI
    │ HTTP 请求：http://192.0.2.10:18001
    ▼
运行 Adapter 服务的节点
    └─ Python 进程
       └─ 后台线程运行 adapter.app，监听 18001 端口
```

第 2 段让服务开始工作，第 3 段给出访问地址；组成 URL 不会重新启动服务。

</details>

## 我的直接表述（原话）

本轮用户提出：

> 主要是这里的endpoint还有一个run app in thread的部分是否也需要考虑清楚呢?

这是最初的阅读问题。随后用户给出整体理解并提出分段要求：

<details>
<summary>2026-10-24 的整体表述与阅读取舍（原话）</summary>

> 这里难道不可以简单理解为从已经有的adapterservice这个class来获取需要到构造adapter的所有的内容
> 但这个也是属于adpter
> 然后才是这里的app hand
> 感觉就是拿了adapter对新的信息和和iayou把这里的请求配置的端口什么都处理了
> 然后在世这里的get current node ip什么的
> 感觉并不是特别需要我知道?
>
> 我赞公爵这里可以拆分出一下这里的几个内容
>
> 当前的skill有对应的办法吗?

</details>

用户已在连接配置、Adapter 与服务准备的阶段。上面关于方法归属、监听配置和 AppHandle 含义的精确区分仍是助手说明。

<details>
<summary>2026-10-24：HTTP 服务与 node IP 的疑问（原话）</summary>

> 简单的理解是adapter本身是处理消息类别的
> 而run app in thread更多的是
> 处理http应用的?
> 然后这里的访问网站是单独拿到这里的nodeip的?
> 但是node ip是什么 我可以简单的理解为跑一个沙箱所需要的cpu中的一个线程?
>
> 我暂时对于第二个和第三个具体是做什么的不是特别清楚

</details>

用户初步区分消息处理与 HTTP 应用，明确表示第 2、3 段仍不清楚。上面的节点地址、线程与服务访问关系是对此的说明，尚未得到理解反馈。

2026-10-24，在地址、缓存与返回部分之后，用户给出整体理解：

> 好的我觉得这里大概清楚了
> 其实这里就是组装adapter
> 然后组装一下这里的handle来处理http服务
> 组装一下具体的具体组合出来用于后续发服务
> 这是我的理解

本次保留“整体大概清楚”的层次。助手据源码校准：首次准备时，先创建 Adapter，再启动它的 HTTP 服务并得到 AppHandle，随后组成访问地址、缓存并返回三元组。AppHandle 保存运行信息与管理入口，接收和处理请求的是正在运行的应用及其 Adapter 处理逻辑；服务在正常返回之前已经启动。这项措辞校准尚未得到进一步反馈。

## 尚不清楚

- 整体主线已有大致理解反馈；AppHandle 管理运行资源与 HTTP 应用实际处理请求的分工，仍需精确区分。
- node IP 与线程的层级区别、第 2 段启动服务与第 3 段提供地址的区别，已补充说明，仍待反馈。
- 服务启动失败、同时请求同一未缓存端点时的行为，尚未在本轮验证。
- 两种协议 Adapter 的差异与访问日志类内部不在本轮展开。

<details>
<summary>来源与验证边界</summary>

- 固定提交同上；[选择表与 Agent 名称](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L50-L64)、[调用现场](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L279)。
- [get_current_node_ip:100–108](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L100-L108)：当前只核对取得节点 IP 的接口职责，未展开 Ray 内部的地址选择。
- [本轮形成过程](../../../../../04-flow.md#adapter-service-startup-reading)。例子为静态推导，没有初始化真实 tokenizer、Adapter、HTTP 或沙箱。

</details>
