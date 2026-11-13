# BlackboxServer.register

[register_rollout](../../api/rollout.py/register_rollout.md) → **本函数：处理注册** → 具体 Agent 的 initialize → 回到本函数形成响应。

- 源码：[core/server.py:241–345](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241)。
- 首次单独展开：Step 005，2026-11-07；此前仅为解释注册职责回查过。
- 最近认识更新：2026-11-07，用户已概括选择适配器和完成准备的方向；助手限定为本次注册的运行准备，并区分委派初始化与题目执行准备。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：HTTP 路由收到注册正文，解析成 RegisterRequest，交给这个已有的 BlackboxServer 对象处理。
2. **具体内容**：选出 Agent 适配器，准备运行绑定并等待适配器初始化，建立会话记录、设为 READY，返回注册响应。另有重复注册、重绑定和失败分支。
3. **建议构建的心智模型**：

   > 前面的客户端负责把配置送到这里；这里把配置变成“本次会话已经准备好的 Agent 后端”。正常完成后，服务端保存适配器、运行绑定和会话记录，才允许接收后续题目消息。

4. **调用代码**（register_rollout 内）：

   ```python
   async with server.request_scope():
       response, _ = await server.register(payload)
   ```

## 本场景的输入与输出

只看首次成功注册：服务端已经启动，所选 Agent 程序已由部署提供，还没有旧绑定。以下是教学输入，不是实际网络请求：

```python
request = RegisterRequest(
    blackbox_type="claude_code",
    router="http://proxy.example:8800",
    bound_session_id="run-a",
    bound_instance_id="question-1",
    bound_sandbox_id="sandbox-a",
    backend_options={},
)
```

**返回**：(RegisterResponse, False)。False 表示本次没有直接复用已有的相同注册。response 中有 READY 状态、绑定资料、能力及生效配置；request_id 先为空，由外层路由补入 HTTP 请求编号。

| 首次注册前 | 正常完成后 |
| --- | --- |
| 没有本次 Agent 适配器 | self._adapter 保存已初始化的 ClaudeCodeAdapter |
| 没有本次运行绑定 | self._binding_context 保存运行目录、会话/任务标识及配置等资料 |
| 没有 run-a 的会话记录 | SessionStore 中建立对应的活动会话 |
| 服务端为 IDLE | 经 INITIALIZING 变成 READY，并启动监测 |

### 先看正常路径的三个动作

下面是按原执行顺序摘出的核心语句，各段不是完整函数；参数 ... 表示省略。配置解析、能力检查、锁及异常包装在末尾完整源码中保留，本轮不展开。

**1. 选定负责本次 Agent 的适配器。**

```python
adapter = create_adapter(request.blackbox_type)  # 按类型选适配器；本例得到 ClaudeCodeAdapter。
capabilities = await adapter.capabilities()      # 取得它支持的能力，供后续检查和响应使用。
```

这里选择的是 Agent 适配器，不是创建沙箱的 provider。

**2. 建立运行资料，并等待适配器初始化。**

```python
self._state = ServerState.INITIALIZING             # 标记服务端正在进行注册初始化。
self._binding_request_fingerprint = fingerprint   # 保存本次配置指纹，用于辨认重复注册。
new_binding_context: BindingContext | None = None # 先留空，后面接住本次运行资料。
# 进入原函数的 try 块，以下保留其正常路径。
await self._teardown_current_binding(reset_sessions=reset_sessions) # 清理旧绑定；本例没有旧绑定。
new_binding_context = self._build_binding_context(...) # 准备运行目录及本次身份、地址和配置。
self._adapter = adapter                          # 把选出的适配器设为当前服务使用的适配器。
await self._adapter.initialize(new_binding_context) # 将资料交给适配器，等待具体运行准备完成。
```

Claude Code 的 initialize 会准备目录、模型请求代理和配置文件，并检查程序可用；不是安装 CLI 或开始解题。

这里的结果类型叫 **BindingContext**，构造它的函数叫 _build_binding_context。它包含 binding（本次身份、运行目录、代理地址、后端选项等）和 effective_config（生效的服务端配置），交给 adapter.initialize 使用；它不是模型的聊天历史。

<a id="after-initialize"></a>

**3. 从 initialize 返回：保存结果，准备会话，再返回 READY。**

```python
self._binding_context = new_binding_context     # 保存初始化成功的本次运行绑定。
self._capabilities = capabilities               # 保存适配器能力说明。
self._effective_config = effective_config       # 保存本次实际生效的服务端配置。
await self._ensure_bound_session_initialized()  # 按绑定的会话 ID 建立或取得会话记录。
self._state = ServerState.READY                 # 标记准备就绪，可以接收后续任务消息。
self._start_monitoring()                        # 启动后端健康状态监测。
return self._build_register_response(), False   # 返回注册结果；False 表示本次不是直接复用。
```

READY 表示注册准备成功；本函数尚未提交题目的 messages。

这里 self 已回到 BlackboxServer。前三个赋值让服务端保存本次配置；会话准备按绑定的 session_id 建立或取得 SessionContext。返回的 False 表示本次不是直接复用旧注册，不表示失败。响应经 register_rollout、HTTP 客户端和 Paddock 返回 generate；generate 不保存这份返回字典，而是继续执行 before_agent。

### 下一处与返回位置

| 需要进入哪里 | 为什么在这里进入 | 返回哪里 |
| --- | --- | --- |
| [ClaudeCodeAdapter.initialize:291](../../adapters/claude_code.py/ClaudeCodeAdapter.initialize.md) | 看清目录、代理和配置具体怎样被准备出来 | 回到本函数保存 _binding_context 的语句 |
| [_build_binding_context:1280](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L1280)，仅按需回查 | 如果不清楚运行资料里有什么 | 回到 adapter.initialize 的入参 |

initialize 已经单独接触，本轮沿第 3 段返回 generate。下一处是 [execute_blackbox_cmds_for_stage](../../../dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md)，只展开 before_agent；辅助函数继续按需回查。

<details>
<summary>其他路径只保留边界，及完整源码</summary>

- 相同注册且服务端已 READY：直接返回已有响应和 True，不重新初始化。
- 有活动或失同步会话时请求换绑定：返回冲突错误。
- 初始化或协议失败：按异常类型更新服务端状态并抛出错误，不返回成功 READY。
- 核心初始化区位于 _init_lock 内；并发与完整失败恢复暂不展开。

```python
async def register(self, request: RegisterRequest) -> tuple[RegisterResponse, bool]:
    if self._state == ServerState.SHUTTING_DOWN:
        raise ApiError(503, "service_unavailable", "Server is shutting down.")

    router_base_url, router_api_path = normalize_router(request.router, request.router_api_path)
    system_prompt_file = self._validate_system_prompt_file(request.system_prompt_file)
    adapter = create_adapter(request.blackbox_type)
    capabilities = await adapter.capabilities()
    if system_prompt_file is not None and not capabilities.system_message:
        raise ApiError(
            400,
            "request_error",
            "Current backend does not support register-time system prompt injection.",
            details={"blackbox_type": request.blackbox_type},
        )

    effective_config = (
        request.server_config.apply(self._base_config)
        if request.server_config is not None
        else self._base_config.model_copy()
    )
    proxy_options = self._parse_proxy_options(request.backend_options)
    self._validate_register_binding(request, effective_config, proxy_options)
    fingerprint = binding_request_fingerprint(request, router_base_url)

    async with self._init_lock:
        if self._state == ServerState.INITIALIZING:
            raise ApiError(409, "conflict", "Server is initializing.")
        if self._state == ServerState.SHUTTING_DOWN:
            raise ApiError(503, "service_unavailable", "Server is shutting down.")

        same_fingerprint = fingerprint == self._binding_request_fingerprint
        if same_fingerprint and self._state == ServerState.READY and self._binding_context is not None:
            return self._build_register_response(), True

        if (
            not same_fingerprint
            and self._binding_context is not None
            and await self._session_store.has_open_sessions()
        ):
            raise ApiError(
                409,
                "conflict",
                "Cannot rebind while active or desynced sessions still exist.",
            )

        reset_sessions = not same_fingerprint and self._binding_context is not None
        self._state = ServerState.INITIALIZING
        self._binding_request_fingerprint = fingerprint
        new_binding_context: BindingContext | None = None
        try:
            await self._teardown_current_binding(reset_sessions=reset_sessions)
            new_binding_context = self._build_binding_context(
                request=request,
                router_base_url=router_base_url,
                router_api_path=router_api_path,
                system_prompt_file=system_prompt_file,
                effective_config=effective_config,
                proxy_options=proxy_options,
            )
            self._adapter = adapter
            await self._adapter.initialize(new_binding_context)
            self._binding_context = new_binding_context
            self._capabilities = capabilities
            self._effective_config = effective_config
            await self._ensure_bound_session_initialized()
            self._state = ServerState.READY
            self._start_monitoring()
            return self._build_register_response(), False
        except ApiError:
            self._state = ServerState.ERROR
            self._adapter = None
            self._binding_context = None
            self._capabilities = None
            if new_binding_context is not None:
                remove_runtime_dir(new_binding_context.binding.runtime_dir)
            raise
        except BackendProtocolError as exc:
            self._state = ServerState.IDLE
            self._binding_request_fingerprint = None
            self._adapter = None
            self._binding_context = None
            self._capabilities = None
            self._effective_config = self._base_config.model_copy()
            if new_binding_context is not None:
                remove_runtime_dir(new_binding_context.binding.runtime_dir)
            raise ApiError(
                400,
                "request_error",
                str(exc),
                details={"blackbox_type": request.blackbox_type},
            ) from exc
        except Exception as exc:
            self._state = ServerState.ERROR
            self._adapter = None
            self._binding_context = None
            self._capabilities = None
            if new_binding_context is not None:
                remove_runtime_dir(new_binding_context.binding.runtime_dir)
            raise ApiError(
                502,
                "backend_error",
                f"Failed to initialize backend: {exc}",
                details={"blackbox_type": request.blackbox_type},
            ) from exc
```

</details>

## 我的直接表述（原话）

> 好的 那么现在再看一下下一个函数吧

这是沿 scope 进入本函数的请求，不代表已理解其所有分支。

本轮后续表述：

> 简单来说是否可以理解为具体要用什么adapter
> 或者这里到底需要准备做什么 在这里都完成了?
> 也就是把文件什么的都准备完了?
> 是我的理解

助手校准：首次成功注册会选定适配器，await 其 initialize 完成，再保存绑定/会话并返回 READY。以 Claude Code 为例，目录、配置文件和本地模型代理由 initialize 具体准备；不能理解为任意题目的所有文件与前置工作都已完成，后面仍可能执行 before_agent 命令。

本轮关于 BindingContext 的表述：

> 好的
> 我大概理解了
> 那么我们继续吧
> 这里我可以理解为了building context就是需要哦交给adapter用来initialize的一系列东西?

助手确认其作为适配器初始化输入的理解，补充实际名称及两个字段，未将它扩展为新的独立类阅读。

## 尚不清楚

- 用户已概括选择适配器与准备工作的关系；注册准备和题目前置准备的范围区别已由助手补充，待确认。
- ClaudeCodeAdapter.initialize 的具体落地已单独接触；本轮补清返回服务端与 generate 的关系，理解状态仍按实际反馈保留。
- 重复注册指纹、重绑定及失败恢复机制，本轮先不展开。

<details>
<summary>来源与验证</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- core/server.py 的 register、_build_binding_context、_ensure_bound_session_initialized 和 _build_register_response；适配器选择见 adapters/factory.py，Claude Code 行为回查 adapters/claude_code.py:291 起。
- 教学输入与前后状态为静态推导，没有启动服务、Agent 或运行请求。
- [本步过程](../../../../../04-flow.md)。

</details>
