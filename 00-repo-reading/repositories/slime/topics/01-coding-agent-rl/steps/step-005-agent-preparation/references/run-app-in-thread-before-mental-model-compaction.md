> 2026-10-24 简化心智模型前的完整函数卡。正文保留，仅调整相对链接；线程、监听、通知和历史原话仍可在此回查。

# run_app_in_thread

- 源码定位：[slime/agent/aiohttp_threaded.py:46–98](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L46-L98)。
- 首次接触：此前在服务初始化中按启动接口定位；2026-10-24 开始展开启动与返回的交接。
- 当前阅读反馈：2026-10-24，用户尚不清楚 HTTP 应用的来源、服务在哪里运行及 AppHandle 是什么；当前先建立三者的关系，尚无机制掌握的确认。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`endpoint` 已创建 Adapter 对象，接下来要让 `adapter.app` 能接收 HTTP 请求。
2. **具体内容**：启动后台 daemon 线程；在线程中准备事件循环、AppRunner 和 TCP 监听；调用线程等待启动通知，正常返回 AppHandle。
3. **建议构建的心智模型**：

   > 将已有的 HTTP 应用交给一个持续运行的后台线程；启动成功后，调用者拿到服务句柄继续执行，后台线程继续处理请求。

4. **调用代码**：

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

## 本场景的输入与输出

<a id="http-app-service-handle"></a>

**输入的 HTTP 应用从哪里来？** Adapter 构造时就创建了 `aiohttp` 的应用对象，源码在 `BaseAdapter.__init__:224`：

```python
self.app = web.Application(client_max_size=64 * 1024 * 1024)  # 创建 HTTP 应用对象
```

随后登记请求入口。当前 AnthropicAdapter 在 `_register_routes:49` 中写下：

```python
app.router.add_post("/v1/messages", self._run_turn)  # 这个路径的 POST 请求交给 _run_turn
```

此时已经确定“收到请求后做什么”，尚未建立监听。`endpoint` 将这个 `adapter.app` 和监听配置交给本函数。

**本函数让什么运行起来？** 正常执行时，它在运行 Slime 的当前 Python 进程内启动一个后台线程，用 aiohttp 建立 HTTP 监听，持续执行应用中登记的请求处理逻辑。沙箱中的 CLI 是来访问这个服务的一方。

**返回的 AppHandle 是什么？** 它是本项目定义的普通 Python 数据对象，保存这次服务运行的信息与对象引用。调用方可以读取 `app_handle.port` 得到实际端口，之后需要关闭时使用 `app_handle.stop()`；关闭的内部机制后续再读。服务继续在后台运行，调用方拿到的是它的管理入口。

<details>
<summary>完整场景参数与句柄字段</summary>

沿用 [endpoint](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md) 的首次创建示例。输入是已有 `adapter.app`，绑定主机 `0.0.0.0`、请求端口 `18001`，线程名 `claude_code-adapter`，以及上述 runner 配置；启动等待上限使用默认 `15.0` 秒。

正常输出为 AppHandle，含 `host`、实际 `port`、`thread`、`loop`、`runner`。监听已成功建立，后台线程仍运行。值来自静态构造，未启动实际 Adapter 服务。

</details>

<a id="thread-start-first-step"></a>

### 后续局部阅读：把 _run 交给新线程执行（87–88）

HTTP 服务需要持续处理请求，外层还需要继续执行任务。先观察代码怎样把服务工作交给另一个线程；本次只关注 `target` 与 `start()`。

以下保留原语句，增加阅读注释：

```python
thread = threading.Thread(target=_run, name=thread_name, daemon=True)  # 创建线程对象，指定入口函数
thread.start()  # 启动新线程，由它调用 _run()
```

- `_run` 是前面用普通 `def` 定义的函数。定义函数时，它的函数体还没有执行。
- 第一行把函数 `_run` 作为 `target` 交给线程对象；这里没有写 `_run()`，所以此时没有调用它。
- 第二行启动新线程，由新线程执行 `_run`；原调用线程随后继续 `run_app_in_thread` 中的代码。

这段局部材料用于接清“原线程执行外层函数，新线程执行 `_run`”。原线程随后怎样等待服务准备好，再沿下一行 `started.wait(...)` 继续；下面的完整图与阶段保留供后续阅读。

```text
Caller thread                          Adapter thread
-------------                          --------------
thread.start() ----------------------> _run()
started.wait()                         new_event_loop()
                                       runner.setup()
                                       site.start()
                <--------------------- started.set()
return AppHandle                       loop.run_forever()
endpoint continues                     handles HTTP requests
```

图只表示启动成功路径；两列在通知之后各自继续。真正的服务循环在 Adapter 线程内。

### 1. 创建启动交接用的本地对象（61–63）

```python
started = threading.Event()
err_box: list[BaseException] = []
box: dict[str, Any] = {}
```

`started` 传递启动通知；`box` 交回循环、runner 与实际端口；`err_box` 交回启动错误。这些是函数内的共享变量，随后由嵌套 `_run` 与调用线程使用。

### 2. 后台线程准备监听并保持运行（65–85）

```python
def _run() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        runner = web.AppRunner(app, **(runner_kwargs or {}))
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, host, port)
        loop.run_until_complete(site.start())
        actual_port = port
        for sock in site._server.sockets:  # type: ignore[attr-defined]
            actual_port = sock.getsockname()[1]
            break
        box["loop"] = loop
        box["runner"] = runner
        box["port"] = actual_port
        started.set()
        loop.run_forever()
    except BaseException as e:  # pragma: no cover
        err_box.append(e)
        started.set()
        raise
```

- 这个嵌套函数由新线程执行。事件循环也在该线程中创建并设置。
- `runner.setup()` 准备应用，`site.start()` 建立监听；随后从 socket 取得实际端口。
- 成功时先写入结果、再发通知，最后进入持续运行的循环。发生异常时同样发通知，并把错误放入 `err_box`。

### 3. 启动线程、等待通知、交回句柄（87–98）

```python
thread = threading.Thread(target=_run, name=thread_name, daemon=True)
thread.start()
started.wait(timeout=start_timeout_sec)
if err_box:
    raise err_box[0]
return AppHandle(
    host=host,
    port=int(box["port"]),
    thread=thread,
    loop=box["loop"],
    runner=box["runner"],
)
```

- `thread.start()` 触发另一列；`started.wait(...)` 同步阻塞调用线程，等待通知或超时。
- 正常返回使用 `box` 中的实际资源，`endpoint` 随后才能组成访问地址。
- 本函数返回不等于后台线程结束。句柄中保留的是继续运行的线程、循环和 runner；`AppHandle.stop()` 的关闭过程本轮不展开。

## 我的直接表述（原话）

用户本轮问：

> 主要是这里的endpoint还有一个run app in thread的部分是否也需要考虑清楚呢?

目前提出了需要理解的边界，尚无对线程、通知或服务句柄的独立复述。

随后用户明确调整阅读节奏：

> 但是后面的这个run app_in_the_thread
> 我其实有点没动
> 那么还是一步步来吧

本次从创建线程对象与启动入口小步展开，见[对应过程记录](../04-flow.md#thread-start-first-step)。

用户后来明确提出更前面的对象与运行位置疑问：

<details>
<summary>HTTP 应用与 AppHandle 的问题（原话）</summary>

> 这里的http的部分是哪里来的
> 我知道http是传输的协议啥的
> 但是这里的apphandle什么的是啥?
> 我没有特别理解
> 还是说我其实也不需要理解?
> 但是我需要知道我的心智模型应该是什么
> 这里是在主机直接起了一个http服务?
> 还是做了什么呢?
> 我不是特别理解理解这里

</details>

## 尚不清楚

- 用户对应用对象、运行中的 HTTP 服务与 AppHandle 的关系仍有理解缺口；当前先补清来源、运行位置与返回对象，等待反馈。
- 超时后未得到通知、启动失败与完整资源回收的边界尚未做运行验证；代码未直接使用 `Event.wait` 的布尔返回值。
- AppRunner、TCPSite 的库内部、HTTP 分派与 `AppHandle.stop` 的跨循环关闭留待后续。
- 这次只读启动交接，不据此认定此前 `shutdown_session` 的跨循环问题已掌握。

<details>
<summary>来源与验证边界</summary>

- [AppHandle 的字段与停止方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L25-L43)。
- [应用对象的创建](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L224-L240)、[Anthropic 消息路由](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L48-L50)。
- [本轮形成过程](../04-flow.md#adapter-service-startup-reading)。图和字段值来自静态源码，没有真实启动 Adapter 的 HTTP 线程，也没有执行模型或沙箱。
- 小步验证：2026-10-24 以独立 Thread 实验核对“构造时不调用目标、start 后由新线程执行”；只覆盖当前两行的线程语义，未运行本函数的 HTTP 启动链。

</details>
