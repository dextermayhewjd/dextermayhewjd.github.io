---
title: "S11 Background Tasks：让耗时操作在后台运行"
weight: 110
summary: "显式选择后台 Bash，先回复启动编号；worker 发布结果，下一轮请求前再收集为文本通知。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s11-chapter-outline" title="S11 本章目录" >}}

## 1. 定位：谁在等待，谁可以继续 {#background-position}

### 1.1 我想弄清楚的问题 {#background-question}

S10 记录的是哪些工作可做，但执行一个慢命令时，同步工具仍会等命令结束。假如完整测试还在运行，而检查文档不依赖它，Agent 能否先继续其他工作？

我的理解是：**Background Tasks 把显式请求的 Bash 命令放到后台线程，原调用先收到启动说明，完成结果在后续模型请求前作为通知加入消息。**

源码基准为本地 `ce8f9f1` 的 [s11_background_tasks/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s11_background_tasks/code.py)。下面的函数按真实源码摘录，类方法属于 `BackgroundManager`；完整导入与注册见原文件，伪代码另行注明。摘录按 [MIT 许可](/examples/s11-repo/NOTICE.txt)使用。

### 1.2 Background Task 和 S10 Task 有什么区别 {#background-comparison}

| 机制 | 记录什么 | ID 与存储 | 谁推动执行 |
|---|---|---|---|
| S10 Task System | 工作项、依赖、状态、负责人 | `task_…`，`.tasks/` JSON 文件 | 模型认领后用工作工具执行 |
| S11 Background Tasks | 已启动 Bash 的运行状态和结果 | `bg_0001`，进程内的 dict/list | 后台线程运行命令 |

后台命令结束不会自动把某个 S10 工作项标成 completed；两种 ID 没有自动关联。后台线程使用同一个 `WORKDIR`，文件也在同一工作区，没有单独工作目录。

### 1.3 整体过程：从 S10 到 S11 {#background-architecture}

#### 图 1：回顾 S10 的默认总览

{{< architecture from="/projects/learn-claude-code/s10" width="1200" src="images/task-agent-integration.svg" mode="baseline" modified="prepare,tools,handler,system" folded="task-tools,task-store,task-files" label="图 1：继承 S10 默认总图，标出后台分流与请求前通知的改造位置" caption="图 1：沿用 S10 的节点、位置和连线。橙色是将扩展的工具定义、分发、请求前处理和使用约定；灰色任务工具、检查与文件细节将在图 2 收入工作工具的 S10 索引，任务能力不删除。" >}}

#### 图 2：后台命令怎样接回已有系统

{{< architecture-explorer id="s11-background-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/background-agent-integration.svg" legend="evolution" label="图 2：权限放行后启动后台 Bash，先回传启动说明，完成结果在请求前注入" caption="图 2：启动后分成两条路径：主线程回传说明，后台 worker 执行并发布结果。灰色队列保存内存状态，请求前收集已完成项并注入消息；本轮退出不等待后台。S10 的任务实现已合并到工作工具索引，旧循环与其他接口保留。" >}}

**比较范围：** 总图是累积学习骨架。独立 S11 脚本实际只有 S04 的五个基础工具、Permission、Hooks 和后台机制，没有直接合入 S10 任务工具、Memory、Skills 或 Compact。图中的旧接口用于复习，不能当作已累计运行的源码。

本章没有增加第六个工具：模型仍调用 `bash`，只是 schema 多了 `run_in_background`。`execute_tool` 先做 PreToolUse，再决定同步 `call_tool` 或内部后台启动。`BackgroundManager` 方法不会作为 schema 发给模型。

#### 图 3：主循环与后台线程的最小核心

{{< architecture figureId="s11-background-core" functionExplorer="s11-background-explorer" width="1000" src="images/background-core.svg" legend="evolution" label="图 3：主循环继续，worker 在下方执行，后续请求前收集通知" caption="图 3：上方是当前调用和后续请求，下方是后台执行与共享队列。线程启动后无需等待命令结束；进入下一轮才收集完成项。如果本轮返回，就等下次进入循环。点击内部函数名可就近查看代码。" >}}

{{< mechanism-function-index id="s11-background-functions" explorer="s11-background-explorer" class="BackgroundManager" >}}

## 2. 后台生命周期：登记、运行与发布 {#background-lifecycle}

### 2.1 BackgroundManager 保存什么 {#background-state}

**所属层：** Harness 内部管理对象。它持有正在运行的任务、结果和待收集 ID；不是 S10 的文件任务仓库。

```python
def __init__(self):
        self.tasks: dict[str, dict] = {}
        self.results: dict[str, str] = {}
        self._ready: list[str] = []
        self._counter = 0
        self._lock = threading.Lock()
```

| 字段 | 内容 | 更新位置 |
|---|---|---|
| `tasks` | 原调用 ID、command、running/completed/failed | `start` 登记，`_run` 更新，`collect` 移除 |
| `results` | 命令结果字符串 | `_run` 写入，`collect` 取走 |
| `_ready` | 已完成、尚未通知的后台 ID | `_run` 追加，`collect` 清空 |
| `_counter` | 本进程内编号计数 | `start` 递增 |
| `_lock` | 保护这些共享字段的锁 | 登记、发布和收集时短暂持有 |

主线程和 worker 共享这些字段。命令执行在锁外，避免把等待慢命令变成主线程等待锁。重启进程后这些记录不会恢复。

### 2.2 显式判断是否后台运行 {#background-select}

**所属层：** Harness 内部条件判断。输入工具名和参数，输出布尔值；必须是 Bash，并且字段值严格为 Python `True`。

```python
def should_run_background(tool_name: str, tool_input: dict) -> bool:
    return (
        tool_name == "bash"
        and tool_input.get("run_in_background") is True
    )
```

模型参数里的 JSON `true` 解析成 Python `True`。省略标志、传字符串 `"true"`，或给文件工具传同名字段，都不会满足这里的条件；源码不根据命令中的 install/test/build 词语自动猜测。

### 2.3 先登记，再启动线程并返回编号 {#background-start}

`start_background_task` 是内部便利包装，返回后台 ID；它不是 `TOOLS` 里另注册的工具。

```python
def start_background_task(block) -> str:
    return BACKGROUND.start(block)
```

真正登记和启动的是 `BackgroundManager.start`。它检查 Bash 与非空 command，锁内生成 `bg_0001` 等 ID，记录原调用 ID；释放锁后启动 daemon 线程。

```python
def start(self, block) -> str:
        if block.name != "bash":
            raise ValueError("Only Bash commands can run in the background")
        command = block.input.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ValueError("Bash command cannot be empty")

        with self._lock:
            self._counter += 1
            task_id = f"bg_{self._counter:04d}"
            self.tasks[task_id] = {
                "tool_use_id": block.id,
                "command": command,
                "status": "running",
            }

        thread = threading.Thread(
            target=self._run,
            args=(task_id, command),
            daemon=True,
        )
        try:
            thread.start()
        except Exception:
            with self._lock:
                self.tasks.pop(task_id, None)
            raise
        print(f"  [background] started {task_id}: {command[:60]}")
        return task_id
```

线程启动失败会删除刚登记的任务并抛出异常。启动成功只表示命令已交给 worker，不表示完成；非常短的命令也可能在主线程准备回复时已经结束。

### 2.4 worker 执行后发布完成结果 {#background-worker}

**所属层：** `BackgroundManager._run` 是后台线程的内部函数，不是工具入口。它在锁外执行命令，之后持锁更新状态、结果和完成队列。

```python
def _run(self, task_id: str, command: str):
        try:
            output, exit_code = _run_bash_process(command)
            result = _format_bash_result(output, exit_code)
            status = "completed" if exit_code == 0 else "failed"
        except Exception as error:
            result = f"Error: {type(error).__name__}: {error}"
            status = "failed"

        with self._lock:
            task = self.tasks.get(task_id)
            if task is None:
                return
            task["status"] = status
            self.results[task_id] = result
            self._ready.append(task_id)
```

只有退出码 0 是 completed；非零退出、超时返回的 None 或异常都会进入 failed。发布到 `_ready` 不会立即调用模型，也不会执行第二次 PostToolUse。

## 3. 结果回到主循环：收集与消息注入 {#background-delivery}

### 3.1 一次性收集已完成项 {#background-collect}

包装函数调用同一个后台管理器：

```python
def collect_background_results() -> list[str]:
    return BACKGROUND.collect()
```

`BackgroundManager.collect` 在锁内移走 ready 项并清空队列，在锁外格式化通知。正在运行的任务不会被取走。

```python
def collect(self) -> list[str]:
        with self._lock:
            ready = []
            for task_id in self._ready:
                task = self.tasks.pop(task_id, None)
                result = self.results.pop(task_id, "")
                if task is not None:
                    ready.append((task_id, task, result))
            self._ready.clear()

        notifications = []
        for task_id, task, result in ready:
            notifications.append(
                f"<task_notification>\n"
                f"  <task_id>{task_id}</task_id>\n"
                f"  <status>{task['status']}</status>\n"
                f"  <command>{task['command']}</command>\n"
                f"  <summary>{result[:500]}</summary>\n"
                f"</task_notification>"
            )
            print(f"  [background] collected {task_id}: {task['status']}")
        return notifications
```

每项完成结果只送一次：收集后，任务和结果从 dict 中删除。通知的 summary 最多 500 字符，不能把它当成完整输出；当前实现没有把剩余正文另外保存为可恢复文件。

### 3.2 在模型请求前注入 user 文本 {#background-inject}

**所属层：** Harness 内部消息处理。输入 messages，收集通知后合并到最后一条 user 消息，或追加新的 user 消息；返回注入的通知数。

```python
def inject_background_results(messages: list) -> int:
    notifications = collect_background_results()
    if not notifications:
        return 0

    blocks = [{"type": "text", "text": item} for item in notifications]
    if messages and messages[-1].get("role") == "user":
        content = messages[-1].get("content", "")
        if isinstance(content, list):
            content.extend(blocks)
        else:
            messages[-1]["content"] = [
                {"type": "text", "text": str(content)},
                *blocks,
            ]
    else:
        messages.append({"role": "user", "content": blocks})
    return len(notifications)
```

最后一条 user 如果已有 tool_result 列表，就把通知 text 块接到同一列表后。若原 content 是字符串，就先转成 text 块。这样模型会在下一次请求看到消息，不会收到不配对的工具结果。

### 3.3 启动回复和完成通知是两回事 {#background-notification}

| 信息 | 形式 | 对应什么 |
|---|---|---|
| 启动回复 | `tool_result`，按原 `block.id` 配对 | 这次 Bash 调用已接受，后台编号是多少 |
| 完成通知 | user 消息中的 `text` | 某个 bg_id 后来 completed 或 failed |

原调用已经得到启动说明，因此完成结果不会再用同一个 tool_use_id 回答一次。它用独立通知表达事件：

```text
<task_notification>
  <task_id>bg_0001</task_id>
  <status>completed</status>
  <command>python -m pytest</command>
  <summary>...</summary>
</task_notification>
```

XML 风格只是文本格式，不是新的 SDK 消息角色或工具类型。它表示命令完成事件的数据，不是新增的用户任务；模型仍需判断结果是否足以继续，failed 也会作为通知送达。

### 3.4 用一次后台测试串起来 {#background-example}

1. 模型请求 `bash(command="python -m pytest", run_in_background=True)`。
2. PreToolUse 放行后启动线程，当前调用先得到带 bg_id 的启动说明。
3. 主循环可以继续处理独立的文件读取或文档检查。依赖测试结果的步骤仍应等待结果。
4. worker 结束，将状态与结果放进 ready 队列。
5. 再次进入 while 顶部时收集通知，模型请求才带上测试结果。

第 4 步可以发生在模型请求期间；结果只会在后续注入点进入 messages。如果模型已经结束本轮，通知要等新的用户回合等事件再次进入 `agent_loop`。

## 4. 接回执行入口与真实边界 {#background-integration}

### 4.1 工具入口在哪一层分流 {#background-execution}

模型看到的 Bash schema 多一个布尔参数，工具名仍是 bash：

```python
{"name": "bash", "input_schema": {
    "type": "object",
    "properties": {
        "command": {"type": "string"},
        "run_in_background": {"type": "boolean"},
    },
    "required": ["command"],
}}
```

这是省略 description 的 schema 摘录。模型不直接调用 `BackgroundManager.start`。统一入口 `execute_tool` 做权限与 Hooks，决定是否后台，再回传当前调用的结果。

```python
def execute_tool(block) -> str:
    blocked = trigger_hooks("PreToolUse", block)
    if blocked is not None:
        return str(blocked)

    if should_run_background(block.name, block.input):
        try:
            task_id = start_background_task(block)
            output = (
                f"[Background task {task_id} started] "
                "The result will be collected on a later turn."
            )
        except Exception as error:
            output = f"Error: {error}"
    else:
        output = call_tool(block)

    trigger_hooks("PostToolUse", block, output)
    return output
```

PreToolUse 返回非 None 就直接拒绝；后台启动也必须先通过它。PostToolUse 在本次启动说明或同步结果返回后执行，实际后台完成由通知机制处理。

同步分支由 `call_tool` 查本地分发表，它自身不重复执行 Hooks：

```python
def call_tool(block) -> str:
    handler = TOOL_HANDLERS.get(block.name)
    try:
        output = handler(**block.input) if handler else f"Unknown: {block.name}"
    except Exception as error:
        output = f"Error: {error}"
    return str(output)
```

`TOOL_HANDLERS["bash"]` 对应的入口是 `run_bash`。虽然它为兼容 schema 接收后台参数，函数体仍做同步执行；真正的后台判断已经在 `execute_tool` 完成。

```python
def run_bash(command: str, run_in_background: bool = False) -> str:
    return _format_bash_result(*_run_bash_process(command))
```

### 4.2 原 Agent Loop 的两个插入点 {#background-loop}

循环顶部收集结果，工具执行入口选择是否后台。剩下的消息追加与 tool_use 配对继续沿用原流程：

```python
def agent_loop(messages: list):
    while True:
        inject_background_results(messages)
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
            max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [
            block for block in response.content if block.type == "tool_use"
        ]
        if not tool_calls:
            force = trigger_hooks("Stop", messages)
            if force:
                messages.append({"role": "user", "content": force})
                continue
            return

        results = []
        for block in tool_calls:
            output = execute_tool(block)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
        messages.append({"role": "user", "content": results})
```

控制流程伪代码可以压缩为：

```text
while True:
    inject completed notifications into messages
    response = request model
    if no tool calls:
        if Stop asks to continue: continue
        return
    for each tool call:
        check PreToolUse
        if explicit background Bash:
            start worker; result = started acknowledgement
        else:
            result = execute synchronously
        run PostToolUse; pair result with original call ID
    append this batch of tool results
```

这里没有 wait/join 全部后台任务的步骤，也没有“后台完成就自动请求模型”的回调。collect 不等未完成线程；本轮没有更多工具调用且 Stop 不强制继续时，函数照常返回。

### 4.3 命令执行、超时与清理 {#background-process}

**所属层：** 内部进程执行实现。前台 Bash 与后台 worker 共用 `_run_bash_process`；不是两个不同的 Shell 执行引擎。

```python
def _run_bash_process(command: str) -> tuple[str, int | None]:
    process = None
    try:
        # start_new_session (setsid) exists only on POSIX; skip it on Windows.
        popen_kwargs = {} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=WORKDIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, errors="replace",
            **popen_kwargs,
        )
        with _shell_process_lock:
            _shell_processes.add(process)
        stdout, stderr = process.communicate(timeout=120)
        output = (stdout + stderr).strip()
        return (output[:50000] if output else "(no output)"), process.returncode
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)", None
    except OSError as error:
        return f"Error: {type(error).__name__}: {error}", None
    finally:
        if process is not None:
            _stop_process_group(process)
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
            with _shell_process_lock:
                _shell_processes.discard(process)
```

它在同一 WORKDIR 启动 Shell，communicate 最多等待 120 秒，合并 stdout/stderr 后最多保留 50,000 字符。结果格式化会把非零退出码写进错误说明：

```python
def _format_bash_result(output: str, exit_code: int | None) -> str:
    if exit_code in (0, None):
        return output
    return f"Error: command exited with status {exit_code}\n{output}"
```

清理方法如下。POSIX 使用进程组信号，Windows 回退为终止／杀死 Shell 进程；不能据此假设 Windows 会自动清理全部后代。

```python
def _stop_process_group(process: subprocess.Popen):
    """Stop a shell process and its children (cross-platform).

    POSIX uses process-group signals (SIGTERM then SIGKILL). Windows has
    neither ``os.killpg`` nor ``signal.SIGKILL``, so it falls back to
    ``Popen.terminate()`` / ``Popen.kill()``.
    """
    if os.name == "nt":
        for stop in (process.terminate, process.kill):
            if process.poll() is not None:
                return
            try:
                stop()
            except OSError:
                return
            try:
                process.wait(timeout=0.05)
            except subprocess.TimeoutExpired:
                continue
        return

    # SIGKILL is POSIX-only; fall back to SIGTERM on platforms without it.
    for sig in (signal.SIGTERM, getattr(signal, "SIGKILL", signal.SIGTERM)):
        try:
            os.killpg(process.pid, sig)
        except (ProcessLookupError, OSError):
            return
        time.sleep(0.05)
```

源码还在 atexit 和 SIGTERM 路径调用 `_stop_all_shell_processes`。这属于生命周期清理，没有提供工作区隔离；进程退出不保证所有后台命令都能自然完成。

### 4.4 当前实现的边界与我的理解 {#background-boundaries}

| 边界 | 当前源码行为 |
|---|---|
| 哪些工具可后台 | 仅显式请求的 Bash，文件工具仍同步 |
| 是否持久化 | 只有内存状态，不关联 S10 任务文件 |
| 何时收到完成结果 | 下一次模型请求前；不会主动唤醒已返回的循环 |
| 是否等待全部完成 | 不等待；本轮可先返回 |
| 是否有完整输出 | runner 先截到 50,000，通知再截到 500 字符 |
| 是否可查询或取消 | 本章没有额外 query/cancel 工具；collect 后记录移除 |
| 是否独立目录 | 仍使用同一 WORKDIR，独立性由任务安排保证 |

**我的一句话理解：让主循环先拿到启动确认继续工作，把完成结果排队，在下次请求前送回模型；后台执行和任务完成记录是两个层次。**
