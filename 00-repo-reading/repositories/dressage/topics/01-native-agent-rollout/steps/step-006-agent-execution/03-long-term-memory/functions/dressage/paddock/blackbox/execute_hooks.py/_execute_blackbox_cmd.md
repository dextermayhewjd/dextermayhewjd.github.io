# _execute_blackbox_cmd

> Step 006 继承：来自 [Step 005 的 02-short-term-memory 记录](../../../../../../../step-005-agent-registration/02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[Step 005 · 2.1](../../../../../../../step-005-agent-registration/01-scope.md#reading-navigation) → [execute_blackbox_cmds_for_stage](execute_blackbox_cmds_for_stage.md) → **本函数：执行一条命令** → 返回外层循环。

> 把一条已配置的命令交给 Paddock 执行，留下记录，再决定失败是否应中止后续流程。

## 函数定位

- 源码：[execute_hooks.py:153–219](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L153)。
- 首次单独展开：Step 005，2026-11-07。
- 最近认识更新：2026-11-07，用户进一步描述执行预配置命令、创建目录/准备文件/检查环境，并读取输出、退出码和超时状态；记录结果与按 required 决定是否继续，由助手补充。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：当前位于 Agent 开始处理题目之前。外层从 before_agent 计划中取出一条 BlackboxExecuteCmd，连同已有的 paddock/state、会话 ID 和 metadata 传进来。这里执行的是配置中指定的准备或检查动作。
2. **具体内容**：取出 command.cmd，通过 Paddock 把命令交给沙箱内的 BlackboxServer 执行；接住结果或异常，写入 metadata；必须成功的命令失败时中止后续流程。例如配置了 `mkdir -p /tmp/task-input`，就是在沙箱里创建这个目录。此命令只是用途示意，实际内容取自本次命令计划。
3. **建议构建的心智模型**：

   > 执行你事先配置好的命令，例如创建目录、准备文件、检查环境。然后读取输出、退出码和超时状态，决定是否继续。

4. **调用代码**，来自外层函数：

   ```python
   for command in schedule.get(stage, ()):
       await _execute_blackbox_cmd(
           paddock,
           state,
           metadata,
           session_id=session_id,
           command=command,
       )
   ```

## 本场景的输入与输出：沿正常路径读三步

当前是 before_agent。paddock/state 指向已经准备好的环境，command 是解析计划时得到的一条命令记录，不是整个计划。它携带 cmd、timeout、required 等信息。

正常返回值是 **None**；命令的结果保存在传入的 metadata 中。下面三段是原函数正常路径节选；完整函数与异常分支保留在后面。

### 1. 发出这一条命令，等待结果（161–173）

```python
# execute_cmd 是局部变量，指向当前 paddock.execute_cmd 这个绑定方法。
# 它将指定命令交给已有沙箱执行，不调用 Claude/Codex 来决定操作。
execute_cmd = getattr(paddock, "execute_cmd", None)
if execute_cmd is None:
    raise TypeError(f"{type(paddock).__name__} does not implement execute_cmd")

# 原函数在 try 中执行以下调用。
cmd_result = await maybe_await(
    execute_cmd(
        state,                         # 在哪个已有环境执行。
        session_id=session_id,         # 属于本次哪个会话。
        cmd=command.cmd,               # 真正要执行的命令字符串。
        timeout=command.timeout,       # 这条命令的超时参数。
    )
)
```

这次调用的去向是：

1. 当前 paddock 是 BlackboxAgentPaddock，局部变量 execute_cmd 指向它的 execute_cmd 方法。
2. Paddock 根据 state 找到已有沙箱的 endpoint，交给 BlackboxServerClient。
3. 客户端向该沙箱的 `POST /v1/sessions/{session_id}/execute_cmd` 发送命令，接收服务端回复。本函数等待这次调用返回，再处理 cmd_result。

因此，命令执行目标在沙箱里；本函数本身承担调用与结果处理。客户端请求依据见 [BlackboxServerClient.execute_cmd:236](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L236)。

`cmd_result` 是该接口返回的命令结果。即使请求正常返回，命令仍可能具有非零退出码或超时标记；第 3 步才据此决定是否中止。

### 2. 整理结果，并追加到本次 metadata（203–212）

```python
# 保留结果字段，并按配置整理/截断 stdout、stderr。
result_summary = _execute_cmd_result_summary(cmd_result, stdout_limit=command.stdout_limit)
record = {
    "stage": command.stage,
    "name": command.name,
    "cmd": command.cmd,
    "timeout": command.timeout,
    "required": command.required,
    "cmd_result": result_summary,
}
# 没有列表就建一个，再把本条记录追加进去；不覆盖之前的命令记录。
metadata.setdefault("execute_cmds", []).append(record)
```

记录把“执行了什么”和“返回了什么”放在一起。后面即使命令被判为必须中止的失败，这条记录也已经追加。

### 3. 判断失败是否应阻止后续流程（214–219）

```python
if command.required and _execute_cmd_failed(result_summary):
    raise RuntimeError(
        "required execute_cmd failed: "
        f"name={command.name} returncode={result_summary.get('returncode')} "
        f"timed_out={result_summary.get('timed_out')}"
    )
# 没有抛出异常就隐式返回 None，外层继续下一条命令。
```

这里用到的失败谓词只有一行：

```python
return result.get("returncode") != 0 or result.get("timed_out") is True
```

1. required=True 且失败：记录后抛异常，外层循环停止。
2. required=False：结果保留，但不会因为非零退出码或超时标记而在此抛异常。
3. 正常成功：返回外层循环，继续下一条；本阶段全部完成后回到 generate:250。

<details>
<summary>如果执行调用直接抛出异常，而没有得到 cmd_result</summary>

原函数的 except 分支先将异常类型、信息和可用的 HTTP 资料写入 metadata，再判断 required：必须成功的命令重新抛出原异常；可选命令记日志后返回。

这与“收到了结果，但退出码非零”是两条不同路径。两者都先记录再决定是否继续。Paddock 不提供 execute_cmd 时的 TypeError 位于 try 之外，因此不会被可选命令规则吞掉。

这里捕获的是 Exception；asyncio.CancelledError 不会因为 required=False 就被这一分支吞掉。

</details>

### 返回与按需回查

| 位置 | 本轮边界 |
| --- | --- |
| [BlackboxAgentPaddock.execute_cmd:203](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L203) | 先确认它将已有 state 对应到 endpoint，再委派客户端；不继续展开完整 HTTP/进程链 |
| [_execute_cmd_result_summary:222](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L222) | 按结果整理工具理解，不另建卡 |
| [返回外层循环](execute_blackbox_cmds_for_stage.md) | 本条返回 None 后执行下一条；全部结束才返回 generate |

<details>
<summary>完整源码（固定版本，未裁剪）</summary>

```python
async def _execute_blackbox_cmd(
    paddock: Any,
    state: Any,
    metadata: dict[str, Any],
    *,
    session_id: str,
    command: BlackboxExecuteCmd,
) -> None:
    execute_cmd = getattr(paddock, "execute_cmd", None)
    if execute_cmd is None:
        raise TypeError(f"{type(paddock).__name__} does not implement execute_cmd")

    try:
        cmd_result = await maybe_await(
            execute_cmd(
                state,
                session_id=session_id,
                cmd=command.cmd,
                timeout=command.timeout,
            )
        )
    except Exception as exc:
        record = {
            "stage": command.stage,
            "name": command.name,
            "cmd": command.cmd,
            "timeout": command.timeout,
            "required": command.required,
            "cmd_error": {
                "type": f"{type(exc).__module__}.{type(exc).__name__}",
                "message": str(exc),
                "summary": _exception_summary(exc),
            },
            "http": _http_exception_details(exc),
        }
        metadata.setdefault("execute_cmds", []).append(record)

        if command.required:
            raise

        logger.warning(
            "optional blackbox execute_cmd failed; continuing rollout: "
            "stage=%s name=%s session_id=%s error=%s",
            command.stage,
            command.name,
            session_id,
            _exception_summary(exc),
        )
        return

    result_summary = _execute_cmd_result_summary(cmd_result, stdout_limit=command.stdout_limit)
    record = {
        "stage": command.stage,
        "name": command.name,
        "cmd": command.cmd,
        "timeout": command.timeout,
        "required": command.required,
        "cmd_result": result_summary,
    }
    metadata.setdefault("execute_cmds", []).append(record)

    if command.required and _execute_cmd_failed(result_summary):
        raise RuntimeError(
            "required execute_cmd failed: "
            f"name={command.name} returncode={result_summary.get('returncode')} "
            f"timed_out={result_summary.get('timed_out')}"
        )
```

</details>

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的那么按照这个顺序读吧

这是确认按“发送 → 记录 → 失败判断”阅读，不代表已掌握本函数。

后续理解：

> 简单来说就是在这里执行 execute cmd 对吗
> 然后看这里的结果对吗
> 一般情况下 就是这里的claude或者codex cli运行一个东西我可以这么理解对吗?

助手校准：执行命令并查看结果这一关系正确。当前 before_agent 使用的是预先配置的 command.cmd，由沙箱命令接口执行，通常用于任务前置准备；不是让 Claude/Codex 根据题目自主决定操作。后面的 call_agent 才提交题目给 Agent。命令字符串本身可以包含 CLI 调用，但不能把 execute_cmd 的一般职责等同于 Agent 执行。

本轮对心智模型的表述与确认请求：

> 以及这里的心智模型应该怎么写?
> 执行实现配置好的命令
> 创建目录 准备文件 检查环境然后读取输出 退出码和超时状态?
> 这里是这个函数的心智模型?

助手将“实现配置”按上下文理解为“事先配置”。上述表述已覆盖命令用途与结果读取；进一步补充本函数会保存执行记录，并在失败时按 required 决定是否继续。该补充仍属于助手说明。

## 尚不清楚

- 用户已表达预配置命令、用途示例和输出/退出码/超时状态；局部变量与 Paddock 方法的对应、结果返回与命令成功的区别，仍未独立说明。
- 保存执行记录和 required 失败分支，本轮由助手补充，尚待用户反馈。
- 命令服务端具体怎样创建和终止进程，本轮未深入。

## 来源与验证

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 源码：execute_hooks.py:153–242；接口下游：paddock.py:203–217。
- [Step 005 本次阅读记录](../../../../../../../step-005-agent-registration/04-flow.md#read-one-execute-command)。本轮仅静态核对，没有真实执行沙箱命令。

</details>
