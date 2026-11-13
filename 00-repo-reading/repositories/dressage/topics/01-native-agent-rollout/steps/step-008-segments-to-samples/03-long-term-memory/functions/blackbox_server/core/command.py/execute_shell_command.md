> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/blackbox_server/core/command.py/execute_shell_command.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# execute_shell_command

- 源码：[core/command.py:21](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/command.py#L21)。
- 首次单独展开：Step 007，2026-11-08；已展开启动段，本轮继续输出收集与超时段。
- 最近说明更新：2026-11-08；用户对等待与超时段反馈大致理解；本轮接续进程登记收尾与结果返回。

[调用方 BlackboxServer.execute_cmd](../server.py/BlackboxServer.execute_cmd.md) → **启动并等待 shell 命令** → 返回调用方的 result。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：服务端已经检查会话并持有 session_lock，现在需要真正执行 cmd。
2. **具体内容**：启动 shell 进程，通过管道收集输出、等待结束并处理超时，最后返回 ExecuteCmdResult。进程启动和结束时调用传入的登记回调。
3. **建议构建的心智模型**：

   > 启动一个 shell 执行指定命令，收集输出和退出状态，再把结果交回去。

4. **调用代码**：

   ```python
   result = await execute_shell_command(
       cmd,
       timeout=timeout,
       on_process_start=lambda proc: self._set_active_cmd_process(session_id, proc),
       on_process_end=lambda proc: self._clear_active_cmd_process(session_id, proc),
   )
   ```

## 本场景的输入与输出

输入为已检查的 cmd、具体 timeout 和两个进程登记回调。当前调用方未传 cwd/env，沿用默认 None；不能凭这里假定自动切到任务 workspace。命令在运行 BlackboxServer 的环境中启动。

正常返回 ExecuteCmdResult：cmd、stdout、stderr、returncode、timed_out、duration_seconds、started_at、finished_at。这里只返回命令结果，session_id 等字段由调用方补入 ExecuteCmdResponse。

<a id="start-process"></a>

### 1. 启动 shell 进程

原函数进程启动段，添加中文注释；外层计时和异常包装见完整源码。

```python
proc = await asyncio.create_subprocess_exec(
    "/bin/sh",  # 启动 shell 程序。
    "-lc",      # -c 让 shell 执行后面的命令字符串；-l 使用登录 shell 模式。
    cmd,        # 例如 "echo after"，由 shell 解析并执行。
    cwd=None if cwd is None else str(cwd),
    env=None if env is None else dict(env),
    stdout=asyncio.subprocess.PIPE,  # 把标准输出接到管道，后续由 Python 读取。
    stderr=asyncio.subprocess.PIPE,  # 标准错误单独接到管道。
    start_new_session=True,  # 新建操作系统进程会话，便于后续按进程组清理。
)
```

- 这个 await 完成时，取得的是进程对象 proc，不是命令的最终结果。命令可能还在执行，后面仍需等待和收集输出。
- /bin/sh 执行配置命令，不自动选 Claude/Codex。cmd 可以调用脚本，也可以直接是 shell 命令。
- PIPE 让 Python 可以读取输出，不是默认把输出直接打印到用户终端。
- start_new_session 是操作系统进程会话，与业务 session_id 不是同一个概念。
- 当前 cwd/env 为 None，子进程继承服务进程的工作目录和环境；shell 自身的启动行为仍可能进一步影响环境。

<a id="collect-and-timeout"></a>

### 2. 收集输出、限时等待，超时后终止进程并收完输出

启动后先调用 on_process_start(proc) 登记进程。随后出现的 Task 是 Python 中收集输出的任务，不是重新启动一个 shell 进程。

```python
timed_out = False
# 安排收集标准输出/标准错误，并等待进程退出。
communicate_task = asyncio.create_task(proc.communicate())
try:
    try:
        # 给这次等待设置时限；保护里面的收集任务不被本次超时取消。
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            asyncio.shield(communicate_task),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        timed_out = True
        # 超时不等于进程已经退出，必须显式终止命令进程组。
        await terminate_process_group(proc)
        # 收集任务还在；等待它收完剩余输出和进程退出。
        stdout_bytes, stderr_bytes = await communicate_task
finally:
    if on_process_end is not None:
        on_process_end(proc)  # 移除活跃进程登记，本身不是杀进程操作。
```

| 代码 | 在本场景解决什么 |
| --- | --- |
| proc.communicate() | 持续读取两路输出，并等待子进程结束；最终交出两个 bytes 值 |
| create_task(...) | 把收集协程安排为独立的 Python Task，后面仍能拿同一个 Task 等待结果 |
| wait_for(..., timeout) | 限制这次等待的时长；等不到就走 TimeoutError 分支 |
| shield(communicate_task) | 隔开外层等待取消对收集任务的传播，保留超时后继续收尾的能力 |

正常路径，例如时限 30 秒、命令 2 秒完成：收集任务交回两路输出，wait_for 正常返回，不进入超时分支。

超时路径，例如 30 秒仍未完成：wait_for 超时，外层收到 TimeoutError；shield 使 communicate_task 不因这次超时被取消。随后显式终止进程组，再 await 同一个收集任务，取得命令截至终止时留下的输出。

为什么不能把 shield 理解成“保护命令继续运行”：保护对象是 Python 的收集 Task。代码仍主动终止了超时命令。没有 shield 时，wait_for 超时会取消所等待的收集 Task，后面就无法靠同一个 Task 正常取得结果。取消 Python Task 本身也不等于杀掉操作系统子进程。

timeout 是这次等待的时限，终止与收尾还可能继续耗时，不是整个函数严格的墙钟上限。这里解释正常完成和本地超时；外部取消抛出的 CancelledError 不属于这个 TimeoutError 分支，不能据此宣称所有取消都完成相同回收。

<a id="return-command-result"></a>

### 3. 移除进程登记，整理返回值——当前展开

输出取得后，先退出前面的 try/finally。当前调用方传来的回调会移除服务端保存的活跃命令进程登记：

```python
finally:
    if on_process_end is not None:
        on_process_end(proc)
```

回调在异常退出时也会执行；移除登记本身不等于终止进程。下面的返回段只在流程正常走到这里时执行（包括已处理完的本地超时）。

```python
return ExecuteCmdResult(
    cmd=cmd,  # 执行的是哪条命令。
    stdout=stdout_bytes.decode("utf-8", errors="replace"),  # 输出字节变成文本。
    stderr=stderr_bytes.decode("utf-8", errors="replace"),  # 错误输出也变成文本。
    returncode=proc.returncode,  # 进程退出码。
    timed_out=timed_out,  # 是否走过本地超时处理。
    duration_seconds=perf_counter() - started,  # 包括收尾在内的耗时。
    started_at=started_at,
    finished_at=utcnow(),
)
```

这里不再执行命令，也不评判是否应该终止 rollout，只把执行事实组成结果对象。errors="replace" 让无法按 UTF-8 解码的字节显示为替代字符。

结果交给 [BlackboxServer.execute_cmd](../server.py/BlackboxServer.execute_cmd.md#receive-command-result) 的 result：

```python
result = await execute_shell_command(...)  # 接住 ExecuteCmdResult。
# 随后更新会话时间，用结果字段组成 ExecuteCmdResponse。
```

ExecuteCmdResult 保存命令执行事实；调用方的 ExecuteCmdResponse 在此基础上增加会话、任务实例及请求标识字段，交给 HTTP 路由。下一处阅读从调用方的 result 赋值处接续，不跳回创建子进程。

## 我的直接表述（原话）

用户本轮表述：

> 好的那么现在看一下这里的这个execute shell command吧好的那么现在看一下吧这个感觉就是创建了一个subprocess来执行?
> 然后呢
> 这里到底在做什么?
> 好多asyncio的wait for 和shield我其实没有特别理解在做什么

本轮已表达创建子进程执行的理解，并明确对 wait_for/shield 存在疑问；随后用户反馈：“好的 我差不多理解了 / 那么继续吧”。保留为大致理解，不推断已掌握所有取消细节。

## 尚不清楚

- 用户对本场景等待与超时解释反馈大致理解；外部取消与进程组终止细节仍未展开。
- 进程组终止内部和外部取消路径未展开。

<details>
<summary>完整源码与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。静态核对，未实际启动命令；完整源码供定位，不表示全部已读。

```python
async def execute_shell_command(
    cmd: str,
    *,
    timeout: float,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    on_process_start: ProcessHook | None = None,
    on_process_end: ProcessHook | None = None,
) -> ExecuteCmdResult:
    started_at = utcnow()
    started = perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            "/bin/sh",
            "-lc",
            cmd,
            cwd=None if cwd is None else str(cwd),
            env=None if env is None else dict(env),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        raise CommandStartError(f"Failed to start execute_cmd process: {exc}") from exc

    if on_process_start is not None:
        on_process_start(proc)

    timed_out = False
    communicate_task = asyncio.create_task(proc.communicate())
    try:
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                asyncio.shield(communicate_task),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            timed_out = True
            await terminate_process_group(proc)
            stdout_bytes, stderr_bytes = await communicate_task
    finally:
        if on_process_end is not None:
            on_process_end(proc)

    return ExecuteCmdResult(
        cmd=cmd,
        stdout=stdout_bytes.decode("utf-8", errors="replace"),
        stderr=stderr_bytes.decode("utf-8", errors="replace"),
        returncode=proc.returncode,
        timed_out=timed_out,
        duration_seconds=perf_counter() - started,
        started_at=started_at,
        finished_at=utcnow(),
    )

```

[本轮形成过程](../../../../../../step-007-proxy-finalization-and-trajectory/04-flow.md#shell-start)。

</details>
