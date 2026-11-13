> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.execute_cmd.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServer.execute_cmd

- 源码：[core/server.py:815–887](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L815)。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；本轮用户已概括检查、执行与结果封装的主线，细节掌握不作推断。

[调用方：服务端路由](../../api/sessions.py/execute_cmd.md) → **当前方法** → execute_shell_command → 返回路由的 response。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：沙箱内 HTTP 路由已收到命令请求，传入 session_id 与 ExecuteCmdRequest。当前场景是 Agent 调用结束后的 after_agent 命令。
2. **具体内容**：检查服务端状态、命令和会话绑定，找到会话及其锁；在锁内确认允许执行，等待 shell 命令结果；更新会话时间并封装响应。
3. **建议构建的心智模型**：

   > 确认这个会话现在可以执行命令，再执行指定命令，把结果带着会话标识交回去。

   不重新选择 Claude/Codex，不创建沙箱，也不让模型规划命令。命令失败是否应中止整条 rollout，仍由上层 hook 的 required 规则判断。

4. **调用代码**（路由中）：

   ```python
   async with server.request_scope():
       response = await server.execute_cmd(session_id, payload)
   ```

## 本场景的输入与输出

这里的参数 request 就是路由传来的 payload：一个 ExecuteCmdRequest 对象，包含 cmd 和 timeout；它不是路由中的 HTTP Request 对象。输入示例为 session_id="run-a"、cmd="echo after"、timeout=30；仅示意，未实际执行。

输出是 ExecuteCmdResponse，包含命令、stdout/stderr、退出码、超时标记、耗时与起止时间，以及 session_id、instance_id、request_id。当前 request_id 暂置空，回到路由后才填入本次 HTTP 请求标识。

### 1. 找到会话，确认可以执行（815–864）

正常路径教学节选；错误响应的完整写法见文末。

```python
self._ensure_state_ready_for_messages()  # 检查服务端是否处于可处理请求的状态。
self._validate_identifier("session_id", session_id)
cmd, timeout = self._validate_execute_cmd_request(request)  # 提取命令与实际超时。

assert self._binding_context is not None
bound_session_id = self._require_bound_session_match(session_id)  # 必须匹配已绑定会话。
# 原代码在绑定缺失时抛错。
session = await self._session_store.get(bound_session_id)  # 找到会话记录。
session_lock = await self._session_store.get_lock(bound_session_id)  # 找到该会话的锁。
# 原代码在会话或锁不存在时抛错。

async with session_lock:
    ...  # 检查会话状态与活跃 turn；执行和结果封装也都在这个锁内。
```

- timeout 未提供时，使用服务端 execute_cmd_timeout 配置。这里已经得到后续执行使用的具体值。
- 锁内拒绝 ABORTED 会话、通常拒绝 DESYNCED 会话，并拒绝存在活跃 turn 的会话，避免在不允许的阶段执行命令。
- DESYNCED 有专门允许后置收集命令的例外，不能概括为一律拒绝；具体失败类型暂不展开。
- 锁从检查持续持有到命令执行和响应构造结束，不是检查完立即释放。只对使用同一锁的代码提供互斥。

### 2. 执行指定命令并等待结果（866–873）

以下代码位于上面的 session_lock 内，并由 try/except 包裹：

```python
result = await execute_shell_command(
    cmd,  # 已经写好的 shell 命令。
    timeout=timeout,
    # 启动后保存进程对象，使服务端能够找到正在运行的命令进程。
    on_process_start=lambda proc: self._set_active_cmd_process(session_id, proc),
    # 结束时移除这份活跃进程登记。
    on_process_end=lambda proc: self._clear_active_cmd_process(session_id, proc),
)
```

execute_shell_command 才负责启动 `/bin/sh -lc cmd`、收集输出和等待退出。本轮继续进入 [execute_shell_command 启动段](../command.py/execute_shell_command.md#start-process)，后续等待和收集仍未展开。两个回调管理的是进程登记，不是 Agent 的 Task/Event 或训练轨迹。

<a id="receive-command-result"></a>

### 3. 封装结果，交回路由（880–887）

```python
session.updated_at = utcnow()  # 更新会话最后活动时间。
return ExecuteCmdResponse(
    request_id="",  # 路由稍后填写。
    session_id=session_id,
    instance_id=self._response_instance_id(),
    **result.model_dump(),  # 展开命令结果字段，放入响应对象。
)
```

return 退出 async with，释放会话锁；路由的 response 接住对象，补 request_id，再返回 HTTP。这里不写 rollout 的 metadata，也不处理上层 required 配置。

| 位置 | 本轮边界与返回位置 |
| --- | --- |
| execute_shell_command | 本轮只知道启动 shell、等待并返回结果；若继续读它，读完回到 result 赋值处 |
| 服务端路由 | 本方法结束后回到 response 赋值处，继续补 request_id 并回复客户端 |

## 我的直接表述（原话）

> 好的 按么我们看一下这里第二这个balckbox server execute cmd吧

随后用户概括：

> 我感觉这里的所有的内容更耳朵的都像是一系列记录
> 记录是否能够使用
> 能否连接
> 能否运行命令
> 匹配对话
> 绘画记录等一系列检查以及
> 是否能够运行的检查
> 最后才是execute shell command是我的理解
> 最后再把这里的返回命令的结果字段放入executecmdresponse中

LLM 核对：主线理解正确；前段主要是在检查既有状态，不全是写记录，也不是网络连通性探测。

## 尚不清楚

- 会话检查和锁的完整交互机制，当前只按本次命令调用理解。
- execute_shell_command 内部的进程启动、输出收集与超时回收，尚未单独展开。
- 上层如何保存结果并按 required 判断失败，留待返回后继续。

<details>
<summary>完整源码与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。本地静态核对，未运行沙箱、命令或 HTTP 请求。

```python
async def execute_cmd(self, session_id: str, request: ExecuteCmdRequest) -> ExecuteCmdResponse:
    self._ensure_state_ready_for_messages()
    self._validate_identifier("session_id", session_id)
    cmd, timeout = self._validate_execute_cmd_request(request)

    assert self._binding_context is not None

    bound_session_id = self._require_bound_session_match(session_id)
    if bound_session_id is None:
        raise ApiError(
            500,
            "internal_error",
            "Rollout binding is missing bound_session_id.",
        )
    session = await self._session_store.get(bound_session_id)
    session_lock = await self._session_store.get_lock(bound_session_id)
    if session is None or session_lock is None:
        raise ApiError(
            404,
            "not_found",
            "Session does not exist.",
            details={"session_id": bound_session_id},
        )

    async with session_lock:
        if session.state == SessionState.ABORTED:
            raise ApiError(
                409,
                "conflict",
                "Session has been aborted and cannot execute commands.",
                details={"session_id": session_id, "state": session.state},
            )
        if (
            session.state == SessionState.DESYNCED
            and not self._session_allows_post_agent_commands(session)
        ):
            raise ApiError(
                409,
                "conflict",
                "Session is desynced and cannot execute commands.",
                details={"session_id": session_id, "state": session.state},
            )
        active_turn_id = self._active_turn_id(session)
        if active_turn_id is not None:
            raise ApiError(
                409,
                "conflict",
                "Session has an active turn in progress and cannot execute commands.",
                details={"session_id": session_id, "active_turn_id": active_turn_id},
            )

        try:
            result = await execute_shell_command(
                cmd,
                timeout=timeout,
                on_process_start=lambda proc: self._set_active_cmd_process(session_id, proc),
                on_process_end=lambda proc: self._clear_active_cmd_process(session_id, proc),
            )
        except CommandStartError as exc:
            raise ApiError(
                502,
                "backend_error",
                f"execute_cmd failed: {exc}",
                details={"session_id": session_id},
            ) from exc

        session.updated_at = utcnow()
        return ExecuteCmdResponse(
            request_id="",
            session_id=session_id,
            instance_id=self._response_instance_id(),
            **result.model_dump(),
        )
```

辅助证据：server.py:1191 的后置命令例外；1445 的参数整理；1458 起的进程登记；core/models.py:283–302 的请求和结果类型。

CommandStartError 转成 HTTP 502；会话不存在或冲突等由前置分支抛出 ApiError。命令本身的非零退出码通过结果返回，与启动失败分开。

[Step 007 形成过程](../../../../../../step-007-proxy-finalization-and-trajectory/04-flow.md#blackbox-server-execute-cmd)。

</details>
