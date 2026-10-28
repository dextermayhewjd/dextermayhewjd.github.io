# run_app_in_thread

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 02-short-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/02-short-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- **Step 009 调取（2026-10-25）**：完整复用 [Step 005 的现行卡片](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md)。原卡保留 Claude Code 场景；本步以 Codex 举例的共同启动机制见 [HTTP 请求分派说明](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/references/http-request-dispatch.md)。正文、图示、原话、未知和认识时间保留，仅补本条来源并重算相对链接。

- 源码定位：[slime/agent/aiohttp_threaded.py:46–98](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L46-L98)。
- 首次接触：此前在服务初始化中按接口定位；2026-10-24 开始展开启动交接。
- 最近认识更新：2026-10-24，用户在完整卡片重构后表示已差不多理解，并要求继续；记录为对本函数整体的大致理解，具体异常、停止与跨循环细节不据此标为掌握。
- 本次整理：按既有完整函数卡恢复场景、输入输出与分段源码；版式调整不计为新增理解。

- 本步补充（2026-10-25）：用户仍不清楚监听服务如何连到 Adapter，已在第 3 段补出两层回调关系；下面的说明不作为用户已掌握的结论。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`endpoint` 已创建 Adapter，准备运行其 HTTP 应用，让沙箱中的 CLI 能向它发送请求。
2. **具体内容**：在后台线程中准备事件循环和 HTTP 监听；调用线程等待启动结果，成功后取得 AppHandle，后台继续运行。
3. **建议构建的心智模型**：

   > 把已配置好路由的应用交给后台线程运行，等待启动结果，再将服务的运行资源交回调用方管理。

4. **调用代码**（`endpoint:200–209`）：

   ```python
   app_handle = run_app_in_thread(  # 将已有应用交给后台启动，接住返回句柄
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

## 本场景的输入与输出

<a id="http-app-service-handle"></a>

沿用 [endpoint 的首次创建场景](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md)：当前为 `claude_code`，输入应用是已经登记了路由的 `adapter.app`。假设监听地址为 `0.0.0.0`、请求端口为 `18001`，并在默认等待上限 `15.0` 秒内成功启动；这些值用于静态说明，没有运行实际 Adapter 服务。

**输入**：`app`、`host`、`port`、`thread_name`、`start_timeout_sec` 和 `runner_kwargs`。其中线程名是 `claude_code-adapter`，运行选项沿用上面调用中的取消配置和日志类。

**正常输出**：一个 AppHandle，保存本次服务的运行资源：

| 字段 | 本例返回的内容 |
| --- | --- |
| `host` | `"0.0.0.0"`，监听绑定地址；对外访问主机随后由 endpoint 确定 |
| `port` | `18001`，本例成功监听的实际端口 |
| `thread` | 执行 `_run` 的后台线程对象 |
| `loop` | 在该线程中创建并继续运行的事件循环 |
| `runner` | 管理这个 aiohttp 应用运行与清理的 AppRunner |

**持续状态**：函数返回后，后台线程继续处理 HTTP 请求。调用方拿到句柄后回到 `endpoint:210`，随后读取 `app_handle.port` 组成访问地址；`AppHandle.stop()` 的关闭过程另行阅读。

### 先看两个线程怎样交接

框内是本函数及其嵌套函数 `_run` 的代码职责。下面按执行关系讲解：源码先定义 `_run`，到 `thread.start()` 才由新线程执行它的函数体。第 2 段的等待与第 3 段的启动工作分属两个线程；图示采用启动成功的路径。

```text
╔═══════════════════════════════════════════════════════════════════════╗
║ run_app_in_thread: direct startup code                                ║
║ Caller thread                       HTTP thread                       ║
║ [1] create Event / boxes                                              ║
║ [2] thread.start() ----------------> [3] _run()                       ║
║     started.wait()                       loop / runner / site.start() ║
║                    <------------------- started.set()                 ║
║ [4] return AppHandle                    loop.run_forever()            ║
╚═══════════════════════════════════════════════════════════════════════╝
```

路由已经由 Adapter 配好，例如 `POST /v1/messages` 对应 `_run_turn`。本函数运行该应用；具体消息处理属于之后到达的请求。

### 1. 调用线程准备通知与结果容器（61–63）

```python
started = threading.Event()  # 启动结果的通知，初始未触发
err_box: list[BaseException] = []  # 后台出错时，在这里留下异常
box: dict[str, Any] = {}  # 后台成功时，在这里留下运行资源
```

- 两个线程共享这些对象：`started` 传递通知，`box` 传回成功结果，`err_box` 传回异常。
- 此时只是建立交接所需的对象，HTTP 监听尚未启动。

<a id="thread-start-first-step"></a>

### 2. 启动线程，调用方等待启动结果（87–89）

```python
thread = threading.Thread(target=_run, name=thread_name, daemon=True)  # 指定新线程要执行的函数
thread.start()  # 启动后，由新线程执行 _run
started.wait(timeout=start_timeout_sec)  # 调用线程等待通知，最多等给定秒数
```

- `_run` 是上面已经定义好的普通函数。`target=_run` 将它交给线程对象，`start()` 触发新线程执行。
- `started.wait(...)` 等待的是启动结果通知。与此同时，HTTP 线程执行下面第 3 段；通知若先到，等待可直接返回。

### 3. HTTP 线程建立监听，交出资源并继续运行（65–85）

```python
def _run() -> None:
    loop = asyncio.new_event_loop()  # 在 HTTP 线程中创建事件循环
    asyncio.set_event_loop(loop)  # 设为本线程的当前循环
    try:
        runner = web.AppRunner(app, **(runner_kwargs or {}))  # 用已有应用及配置准备运行管理对象
        loop.run_until_complete(runner.setup())  # 完成应用的启动准备
        site = web.TCPSite(runner, host, port)  # 指定 HTTP 监听地址与端口
        loop.run_until_complete(site.start())  # 建立监听
        actual_port = port  # 随后从实际 socket 读取端口
        for sock in site._server.sockets:  # type: ignore[attr-defined]
            actual_port = sock.getsockname()[1]
            break
        box["loop"] = loop  # 把运行资源放入共享结果字典
        box["runner"] = runner
        box["port"] = actual_port
        started.set()  # 通知调用线程：结果已准备好
        loop.run_forever()  # 后台继续运行，处理后续请求
    except BaseException as e:  # pragma: no cover
        err_box.append(e)  # 失败时保存异常
        started.set()  # 失败也通知调用线程，结束其等待
        raise
```

- **准备与监听**：`AppRunner` 接住已有 `app`；`TCPSite` 接住监听地址和端口。完成 `site.start()` 后，本例的 HTTP 监听已经建立。
- **交出结果**：从 socket 取得实际端口，将 `loop`、`runner`、`port` 写入 `box`，再调用 `started.set()`。请求端口为 `0` 时，同样从这里取得系统分配的实际端口。
- **持续工作或报告失败**：成功时进入 `loop.run_forever()`，服务继续接收请求；异常时保存错误，也发出通知，让调用方能结束等待并读取异常。因此收到通知后还需要下面的错误检查。

<a id="listener-handler-binding"></a>

**这里最关键的连接：创建服务时，已经指定了“收到请求后调用谁”。**

`AppRunner(app)` 接住的是带有路由的应用。`runner.setup()` 继续在 aiohttp 内部创建 Server，把这个应用的 `app._handle` 保存为请求回调；`site.start()` 再把这个 Server 交给事件循环监听。下面是 aiohttp **v3.12.15 的调用关系节选**，用于解释上述两行的作用，属于库内部实现：

```python
# Application._make_handler：这里 self 是 app
return Server(self._handle, request_factory=self._make_request, loop=self._loop, **kwargs)

# TCPSite.start：server 来自 runner，参数中的处理逻辑与地址一起交给事件循环
server = self._runner.server
self._server = await loop.create_server(
    server, self._host, self._port,
    # 省略 ssl、backlog 等参数
)
```

因此要区分两层已保存的函数：

| 保存在哪里 | 保存的是谁 | 请求到达后做什么 |
| --- | --- | --- |
| aiohttp 的 Server / RequestHandler | `app._handle` | 网络层把解析后的 request 交给这个应用 |
| 这个 app 的路由器 | 当前 Adapter 的 `self._run_turn`，连同 `POST /v1/messages` | 应用匹配方法与路径后，才调用该 Adapter 方法 |

路由中的 `self._run_turn` 是**绑定到当前 Adapter 实例的方法**，所以调用它时已经知道该使用哪个 Adapter。事件循环负责调度网络事件；以上保存的回调决定事件到来后执行什么。其他路径使用其他 handler，未登记的路径返回 404，不能理解为任何请求都会进入 `_run_turn`。

库内部真正执行回调的是 `RequestHandler._handle_request` 的 `await request_handler(request)`；此处保存的 `request_handler` 就是 `app._handle`。随后应用查路由，再执行 `await handler(request)`。完整的保存与调用位置见[两层回调的源码证据](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/references/http-request-dispatch.md#listener-to-adapter)。这些行为发生在服务启动后的请求处理期，不是本函数逐个直接调用业务方法。

### 4. 调用线程检查结果，返回 AppHandle（90–98）

```python
if err_box:
    raise err_box[0]  # 后台报告失败时，向调用方抛出
return AppHandle(  # 成功路径：把运行资源组装为句柄
    host=host,
    port=int(box["port"]),
    thread=thread,
    loop=box["loop"],
    runner=box["runner"],
)
```

- 正常路径从 `box` 取出刚才后台建立的资源，加上线程对象和绑定地址，形成 AppHandle。
- 返回句柄后，外层继续 [endpoint 的地址组装](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md#public-host-selection)。HTTP 线程仍在运行，双方在通知之后各自继续。

<details>
<summary>当前保留的边界：超时、启动错误与参数作用</summary>

- `start_timeout_sec` 限制的是 `Event.wait` 的等待时间。源码未检查它的布尔返回值；若超时时 `box` 尚未填好，后面取字段可能失败，不能把它描述为完整的超时清理流程。
- `err_box` 非空时，调用线程抛出记录的异常。启动失败后的完整资源回收不在本轮正常路径中验证。
- `thread_name` 用于标识线程；`daemon=True` 使它成为守护线程，具体进程退出与主动关闭问题后续再读。
- `runner_kwargs` 原样传给 AppRunner。当前调用保留 `handler_cancellation=True` 与 `FilteredAccessLogger`，具体请求取消和日志过滤另有职责。
- `app` 的创建与路由注册发生在 Adapter 中：例如 `AnthropicAdapter._register_routes` 登记 `POST /v1/messages → _run_turn`。其他路径按各自的路由处理，本函数不改写这个对应关系。

</details>

## 我的直接表述（原话）

本轮用户概括：

> 这个函数框架还是太多了
> 有没有比较简单一点的呢?
> 我的意思是这里的内容符合skill中对于一个函数的心智模型建立的准则吗?
> 我可以简单的理解为在当前的adapter中开启一个网络服务
> 所有的网络服务发出来之后都会通过这里的对应的adapter的部分转发出去?
> 这是我对于这里的理解
> 简单的来说就是开启了一个接受网络请求的接口
> 同时给出了发送什么请求会运行什么内容这件事情
> 这里倒是终于写清楚了原来是在这里决定了发的请求会送到run turn那里

“开启接收请求的入口”已抓到职责方向。上面的路由归属与请求范围说明是助手校准，尚未得到进一步反馈；[此前完整问题](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/references/run-app-in-thread-before-mental-model-compaction.md#我的直接表述原话)继续保留。

2026-10-24，阅读完整卡片后，用户反馈：

> 好的 我差不多了理解了
> 那么现在继续吧
> 我应该看什么了呢?

本次按对函数整体的大致理解接续；随后回到 endpoint 的地址与结果交接。

2026-10-25，用户再次明确仍未看清的连接（节选）：

> 但是这里没有说明白的事情是为什么这里监听了之后就能够做到
> 就是是怎么挂在在adapter上面
> 并且能够做到任何发往adapter的请求都会走register的路线的?
>
> 当前的第二部分只是说明了有一个aiohttp服务起来了
> 我没有看到在run app in thread里面这里是如何解释这个第二步的

[完整原话与本次校准](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#listener-callbacks-and-bound-methods)保留用户已说清的部分和仍然不清楚的部分。

随后用户反馈“好的我大概明白了”，并转而询问在 `generate` 中哪里触发路由登记；见[构造链回查](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#adapter-constructor-registration)。该反馈只记录为对本轮两层回调解释的大致理解。

## 尚不清楚

- 用户已对两层回调解释反馈大概明白；当前继续回查 Adapter 的构造调用如何触发提前注册，不据此认定全部网络或回调机制已掌握。
- 用户已对整体给出大致理解反馈；线程、Event、事件循环与 AppHandle 各字段的细分机制未逐项确认。
- 启动超时、失败回收及 AppHandle.stop 的机制尚未读清；此前 shutdown_session 的跨循环问题继续保留。

<details>
<summary>来源、历史与验证范围</summary>

- 固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[调用处](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L200-L222)、[AppHandle 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L25-L43)。
- [应用创建](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L224-L240)、[路由登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L48-L50)。
- [较早完整记录](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/references/run-app-in-thread-before-mental-model-compaction.md)保存原线程讲解与早期原话；[此前简版](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/references/run-app-in-thread-compact-version.md)保留本次恢复前的内容。
- [本次按标准格式重构](../../../../../../../../01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#run-app-standard-card)。源码块按执行关系排列并添加注释；本例未真实启动 Adapter、HTTP 服务、模型或沙箱。
- 历史 Thread 小实验只验证构造与启动的线程语义，不能作为本页完整 HTTP 启动的运行证据。
- 第 3 段的库内部说明采用 aiohttp v3.12.15 参考源码；未确认实际运行环境的安装版本，未进行真实网络请求。具体源码位置集中在[流程说明](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/references/http-request-dispatch.md#listener-to-adapter)。

</details>
