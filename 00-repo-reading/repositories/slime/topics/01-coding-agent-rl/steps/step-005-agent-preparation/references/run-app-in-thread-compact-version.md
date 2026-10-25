> 2026-10-24 恢复完整函数卡格式前的简版快照。正文保留，仅调整相对链接。

# run_app_in_thread

- 源码定位：[slime/agent/aiohttp_threaded.py:46–98](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L46-L98)。
- 首次接触：此前在服务初始化中按接口定位；2026-10-24 开始展开启动交接。
- 最近认识更新：2026-10-24，用户概括为开启接收网络请求的入口，并联系到请求与处理函数的对应；路由何时注册、哪些请求会被处理，仍需校准。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Adapter 已准备好 HTTP 应用和处理规则，需要让 CLI 能访问它。
2. **具体内容**：在后台线程中运行这个应用；正常开始监听后，交回管理此次服务的 AppHandle。
3. **建议构建的心智模型**：

   > 把已经配好路由的 HTTP 应用运行起来，开始接收请求，并返回一个服务管理对象。

4. **调用代码**（入口示意，省略其他参数）：

   ```python
   app_handle = run_app_in_thread(adapter.app, ...)  # 运行已有应用，取得服务管理对象
   ```

## 本场景的输入与输出

<a id="http-app-service-handle"></a>

- **输入**：`adapter.app`，以及监听地址、端口等配置；应用中已经登记了请求处理规则。
- **正常结果**：HTTP 服务在当前进程的后台线程中运行；调用方获得 AppHandle，可查看实际端口，之后需要时关闭服务。

**处理规则在启动前登记。** 例如 AnthropicAdapter 的 `_register_routes` 中：

```python
app.router.add_post("/v1/messages", self._run_turn)  # 指定这个方法和路径交给谁处理
```

服务启动后，发到这个服务、匹配 `POST /v1/messages` 的请求才会交给 `_run_turn`。其他路径按各自的注册规则处理。`run_app_in_thread` 使用已有规则，不在这里决定各个路径的处理函数。

<a id="thread-start-first-step"></a>

<details>
<summary>按需回查完整参数、线程启动、监听和通知过程</summary>

[原完整记录](run-app-in-thread-before-mental-model-compaction.md)保留原调用参数、AppHandle 的五个字段、线程图、逐段源码与此前原话。线程启动的局部讲解见[原来的对应位置](run-app-in-thread-before-mental-model-compaction.md#thread-start-first-step)。本轮先停在“已有应用 → 开始接收请求 → 管理对象”的交接。

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

“开启接收请求的入口”已抓到职责方向。上面的路由归属与请求范围说明是助手校准，尚未得到进一步反馈；[此前完整问题](run-app-in-thread-before-mental-model-compaction.md#我的直接表述原话)继续保留。

## 尚不清楚

- 路由提前注册与服务启动的分工，以及只有匹配请求才进入对应处理函数，仍待确认理解。
- AppHandle 的具体资源字段、线程通知、事件循环、启动超时和停止回收尚未读清。
- 此前 `shutdown_session` 的跨循环问题继续保留，本次概括不代表已掌握那些机制。

<details>
<summary>来源与验证范围</summary>

- 固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[应用创建](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L224-L240)、[请求路由注册](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L48-L50)。
- [AppHandle 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L25-L43)；[返回 endpoint](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md)。
- [本轮原话与收拢](../04-flow.md#run-app-compact-model)。本轮静态核对，没有真实运行 HTTP、Adapter、模型或沙箱。
- 原 Thread 小实验只验证构造与启动的线程语义，其范围和结果保存在[原完整卡片](run-app-in-thread-before-mental-model-compaction.md)。

</details>
