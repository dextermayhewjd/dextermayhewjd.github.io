---
title: "S13 Agent Teams：让多个 Agent 协作"
weight: 130
summary: "Lead 创建持久队友，独立循环通过文件邮箱交换事件；空闲认领共享任务，审批与 worktree 约束执行。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s13-chapter-outline" title="S13 本章目录" >}}

## 1. 定位：从一个循环到多个协作循环 {#team-position}

### 1.1 我想弄清楚的问题 {#team-question}

S06 把工作交给一个子 Agent，然后等待这次调用返回。现在我希望几个队友分头做事，保留各自上下文，还能收到补充要求、等待审批、接手下一项工作。

我的理解是：**Agent Teams = 独立的 Agent Loop + 共享任务板 + 消息投递 + 协作约束。** 每个队友仍使用 S01 的“模型 → 工具 → 结果 → 模型”，外面多了一层 WORK / IDLE 生命周期。

源码基准为本地 `ce8f9f1` 的 [s13_agent_teams/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s13_agent_teams/code.py)。代码按真实函数摘录，类方法保留 `self`；本页片段用于分步阅读，不是可独立运行的完整程序。按 [MIT 许可](/examples/s13-repo/NOTICE.txt)使用。

### 1.2 与前面机制的区别 {#team-comparison}

| 机制 | 执行单元 | 何时结束／返回 |
|---|---|---|
| S06 Subagent | 一次受委派的子循环 | 父工具调用等待子循环返回 |
| S11 Background Tasks | 一个后台 Bash 进程 | 完成后收集命令结果 |
| S12 Cron Scheduler | 时间规则和待执行 prompt | 到期启动一轮 Agent |
| S13 Agent Teams | 多个独立模型循环 | 一轮结束可进入 IDLE，消息或任务使其继续 |

“这一轮不再调用工具”只说明这一轮结束；不表示队友线程已经退出。线程之间可以同时请求模型，但每个队友内部仍顺序执行自己的工具调用。

### 1.3 整体过程：从 S12 到 S13 {#team-architecture}

#### 图 1：回顾 S12 的默认总览

{{< architecture from="/projects/learn-claude-code/s12" width="1200" src="images/cron-agent-integration.svg" mode="baseline" modified="history,handler,tools,system,pre-event,added-file-tools" folded="cron-create,cron-poll,cron-queue,cron-idle,cron-ack,cron-deliver" label="图 1：保留 S12 结构，标记团队入口的改造与 Cron 细节的合并" caption="图 1：沿用 S12 的节点、位置和连线。橙色位置本章增加团队工具、独立执行约束和新的消息来源；六个灰色 Cron 细节在图 2 合并为定时事件接口，具体实现仍见 S12。" >}}

#### 图 2：队友循环怎样连接已有系统

{{< architecture-explorer id="s13-team-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/team-agent-integration.svg" legend="evolution" label="图 2：Lead 启动队友，队友独立工作、投递结果，邮箱唤醒 Lead，空闲时等待或认领任务" caption="图 2：上方主循环作为 Lead；紫色完整展开本章的启动、独立循环、邮箱、空闲与唤醒路径。工具立即返回启动确认，队友事件稍后从 CLI 外层作为 user 消息进入 Lead。Cron 内部折叠到蓝色 S12 索引。" >}}

**比较范围：** 总图沿用累积学习骨架；独立 S13 脚本实际合入基础工具、Hooks、Task System、Teams、计划协议和可选 worktree，未合入 S11 后台任务、S12 Cron、Skills、Memory 或 Compact。蓝色旧接口是复习索引，不是这个脚本已经注册的功能。

#### 图 3：多个循环之间的最小协作机制

{{< architecture figureId="s13-team-core" functionExplorer="s13-team-explorer" width="1000" src="images/team-core.svg" legend="evolution" label="图 3：启动队友、独立工作、邮箱交付与 Lead 唤醒，下方为空闲认领与退出路径" caption="图 3：上方串起一次协作，下方区分等待新工作、自动认领和真正退出。点击函数名查看内部实现；run_spawn_teammate 等模型工具包装只在正文讨论。" >}}

{{< mechanism-function-index id="s13-team-functions" explorer="s13-team-explorer" class="TeammateRuntime" >}}

## 2. 启动与工作：每个队友有自己的循环 {#team-runtime}

### 2.1 工具定义、包装入口与内部实现 {#team-layers}

| 层次 | 本章对应代码 | 职责 |
|---|---|---|
| 模型可见定义 | `TOOLS` / `TEAMMATE_TOOLS` | 名称、description、input_schema |
| Harness 分发表 | Lead 的 `TOOL_HANDLERS` / 队友的 `self.handlers` | 把名称映射到本地函数 |
| 具体工具入口 | `run_spawn_teammate`、队友的 `claim` / `complete` | 接收模型参数，绑定调用者身份 |
| 内部运行机制 | `spawn_teammate_thread`、`TeammateRuntime`、`MessageBus` | 线程、循环、消息和状态 |
| 共享存储 | `.tasks` / `.mailboxes` / 可选 `.worktrees` | 任务、邮箱和不同工作目录 |

Lead 有 **18 个 schema**：5 个基础工具、6 个任务工具、7 个团队工具。队友有 **10 个**：5 个基础工具，加发送消息、提交计划、列举／认领／完成任务。队友不能创建任务或改变依赖图，也没有“检查邮箱”工具；收信由运行时处理。

源码中的 `spawn_teammate` 定义如下，`task_id` 和 `require_plan` 都可选：

```python
{"name": "spawn_teammate",
 "description": "Spawn a persistent teammate.",
 "input_schema": {"type": "object",
                  "properties": {
                      "name": {"type": "string",
                               "pattern": "^[A-Za-z0-9_-]{1,64}$"},
                      "role": {"type": "string"},
                      "prompt": {"type": "string"},
                      "task_id": {"type": "string",
                                  "pattern": "^task_[0-9a-f]{8}$"},
                      "require_plan": {"type": "boolean"}},
                  "required": ["name", "role", "prompt"]}},
```

模型只看到定义；本地注册与包装负责实际调用。下列注册片段来自源码，字典省略了其他条目：

```python
TOOL_HANDLERS = {
    "spawn_teammate": run_spawn_teammate,
    # 其余已注册工具省略
}
```

```python
def run_spawn_teammate(name: str, role: str, prompt: str,
                       task_id: str | None = None,
                       require_plan: bool = False) -> str:
    return spawn_teammate_thread(name, role, prompt, task_id, require_plan)
```

包装把参数交给内部启动函数；不是把 Python 函数本身一并发给模型。

### 2.2 先认领，再启动持久队友 {#team-spawn}

**所属层：** Harness 内部启动逻辑。输入名字、角色、提示、可选任务 ID 和审批要求；输出启动确认。先校验名字、注册队友与计划闸门，有初始任务则先认领；认领失败撤销注册，不启动线程。

```python
def spawn_teammate_thread(name: str, role: str, prompt: str,
                          task_id: str | None = None,
                          require_plan: bool = False) -> str:
    """Claim an initial Task, then start one persistent teammate."""
    if not is_valid_agent_name(name):
        return ("Invalid teammate name: use 1-64 letters, digits, "
                "underscores, or dashes")
    if name.lower() in RESERVED_TEAMMATE_NAMES:
        return f"Invalid teammate name: '{name}' is reserved by the runtime"
    with team_lock:
        if any(existing.casefold() == name.casefold()
               for existing in active_teammates):
            return f"Teammate '{name}' already exists"
        active_teammates[name] = "working"
        plan_gates[name] = "required" if require_plan else "not_required"
        assignment_versions[name] = 0

    if task_id:
        try:
            claimed = claim_task(task_id, owner=name)
        except (FileNotFoundError, ValueError) as exc:
            claimed = f"Error: {exc}"
        if not claimed.startswith("Claimed "):
            with team_lock:
                active_teammates.pop(name, None)
                plan_gates.pop(name, None)
                assignment_versions.pop(name, None)
            return f"Cannot spawn teammate '{name}': {claimed}"

    runtime = TeammateRuntime(name, role, prompt, task_id, require_plan)
    thread = threading.Thread(target=runtime.run, daemon=True)
    with team_lock:
        teammate_threads[name] = thread
    thread.start()
    print(f"  [teammate] {name} spawned as {role}")
    assigned = f" for {task_id}" if task_id else " without an initial Task"
    return (
        f"Teammate '{name}' spawned as {role}{assigned}. "
        "End this turn; the runtime will deliver its events."
    )
```

`lead` / `agent` 是保留身份；已有名字不允许再次启动。`daemon=True` 表示主进程退出时不会等待这些线程。

SYSTEM 要求 Lead 先提出团队、等用户确认后再启动，并在启动后结束当前回合。这是**提示词约定**：`agent_loop` 没有遇到 spawn 就强制 return，也没有硬编码的“团队确认”状态机。

### 2.3 独立上下文与工具身份 {#team-state}

**所属层：** `TeammateRuntime` 初始化。每个实例保存自己的 system、messages 和 handlers；传入初始 task_id 时，提示里附上已经认领的任务与目录。

```python
def __init__(self, name: str, role: str, prompt: str,
             task_id: str | None, require_plan: bool):
    self.name = name
    self.system = (
        f"You are '{name}', a {role}. Use tools to complete the assigned "
        "Task, then call complete_task and report a concise result. "
        "If the first user message contains [Assigned task], that Task is "
        "already claimed; do not call claim_task for it again. "
        "When asked for a plan, call submit_plan and wait for approval "
        "before bash or file changes. File and shell tools use the Task's "
        "working directory; that directory is not a sandbox. The runtime "
        "delivers your final text to Lead. Use send_message only for "
        "intermediate coordination, and address the coordinator as 'lead'."
    )
    self.messages = [{"role": "user", "content": prompt}]
    if task_id:
        task = load_task(task_id)
        cwd = assignment_cwd(name)
        self.messages[0]["content"] += (
            f"\n\n[Assigned task {task.id}] {task.subject}\n"
            f"{task.description}\nWork directory: {cwd}"
        )
    if require_plan:
        self.messages[0]["content"] += (
            "\n\n[Plan required] Submit a plan and wait for Lead approval "
            "before changing files or using bash."
        )
    self.handlers = {
        "bash": self.bash,
        "read_file": self.read,
        "write_file": self.write,
        "edit_file": self.edit,
        "glob": self.glob,
        "send_message": lambda to, content: _teammate_send_message(
            name, to, content),
        "submit_plan": lambda plan: _teammate_submit_plan(name, plan),
        "list_tasks": run_list_tasks,
        "claim_task": self.claim,
        "complete_task": self.complete,
    }
```

共享的是任务和邮箱，不是 messages 数组。队友的 `claim` / `complete` 把 `owner=self.name` 传入内部任务逻辑，Lead 的包装使用 `owner="agent"`；协调者的邮箱名则是 `lead`。

普通补充消息会追加到该队友自己的历史；它本身不等于新任务，不自动改变 assignment 或计划版本。

### 2.4 WORK：仍然是熟悉的工具循环 {#team-work}

**所属层：** `TeammateRuntime.work` 执行一次模型请求。先收信，再使用自己的 system、messages、TEAMMATE_TOOLS 请求模型；有工具就顺序执行并追加配对结果，返回 `continue`。

```python
def work(self) -> str:
    """Run one model turn. Return continue, idle, or stop."""
    if self.handle_inbox(BUS.read_inbox(self.name)):
        return "stop"
    with team_lock:
        active_teammates[self.name] = "working"
    try:
        response = client.messages.create(
            model=MODEL,
            system=self.system,
            messages=self.messages,
            tools=TEAMMATE_TOOLS,
            max_tokens=8000,
        )
    except Exception as exc:
        BUS.send(self.name, "lead",
                 f"{type(exc).__name__}: {exc}", "error")
        return "stop"

    self.messages.append({"role": "assistant",
                          "content": response.content})
    tool_calls = [
        block for block in response.content if block.type == "tool_use"
    ]
    if tool_calls:
        results = []
        for block in tool_calls:
            output = _run_teammate_tool(
                self.name, block, self.handlers
            )
            results.append({"type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output})
        self.messages.append({"role": "user", "content": results})
        return "continue"

    summary = _last_assistant_text(response.content)
    gate = plan_gates.get(self.name, "not_required")
    if gate != "pending" and summary:
        BUS.send(self.name, "lead", summary, "result")
    if gate == "pending":
        with team_lock:
            active_teammates[self.name] = "waiting_approval"
    else:
        release_completed_assignment(self.name)
        with team_lock:
            active_teammates[self.name] = "idle"
        BUS.send(self.name, "lead", "Waiting for more work.",
                 "idle_notification")
    return "idle"
```

无工具时，非 pending 计划且有文本才发 `result`。等待审批则标记 `waiting_approval`；否则释放已完成任务的目录租约，标记 idle 并发 `idle_notification`。**result 是自然语言汇报，任务 completed 必须由 complete_task 单独写入。**

下面是线程生命周期。`work()` 返回 `idle` 后进入等待，返回 `continue` 就继续请求；只有 `stop`、有效关机或异常使线程结束：

```python
def run(self):
    try:
        state = "continue"
        while state != "stop":
            if state == "idle" and not self.wait_for_work():
                break
            state = self.work()
    except Exception as exc:
        try:
            BUS.send(self.name, "lead",
                     f"{type(exc).__name__}: {exc}", "error")
        except Exception:
            pass
    finally:
        try:
            release_teammate_assignment(self.name)
        except Exception as exc:
            try:
                BUS.send(
                    self.name, "lead",
                    f"Assignment cleanup failed: {type(exc).__name__}: {exc}",
                    "error",
                )
            except Exception:
                pass
        with team_lock:
            active_teammates.pop(self.name, None)
            plan_gates.pop(self.name, None)
            plan_request_ids.pop(self.name, None)
            teammate_threads.pop(self.name, None)
        print(f"  [teammate] {self.name} finished")
```

### 2.5 执行闸门不是只有一句提示 {#team-gate}

**所属层：** 队友 Harness 的工具执行入口。输入模型的工具调用及本队友的 handlers；输出配对 tool_result 的内容。计划未通过时拦住 Bash／写／编辑，再检查非交互权限；工具异常转换成文本结果。

```python
def _run_teammate_tool(name: str, block, handlers: dict) -> str:
    gate = plan_gates.get(name, "not_required")
    if block.name in {"bash", "write_file", "edit_file"}:
        if gate != "approved":
            if gate != "not_required":
                return (f"Blocked: plan status is {gate}. Submit or revise the "
                        "plan and wait for approval before changing the workspace.")
        blocked = check_permission(block, prompt_user=False)
        if blocked:
            return blocked
    handler = handlers.get(block.name)
    if not handler:
        return f"Unknown tool: {block.name}"
    trigger_hooks("PreToolUse", block, skip_permission=True)
    try:
        output = str(handler(**block.input))
    except Exception as exc:
        output = f"Error: {type(exc).__name__}: {exc}"
    trigger_hooks("PostToolUse", block, output)
    return output
```

读取和 glob 不受计划闸门禁止，但工作区工具仍要求有效任务 assignment。`_run_teammate_tool` 虽以 `_run` 开头，职责是 Harness 内部执行入口；`run_spawn_teammate` 则是某个模型工具的包装，不能仅凭名字判断层次。

审批不覆盖权限。后台队友使用 `prompt_user=False`，遇到源码判定需要确认的命令会返回“请 Lead 执行”，不会在线程里向用户弹交互输入。详见 [S13.2 计划协议](02-team-protocols/#protocol-gate)。

## 3. 消息与空闲：谁让下一轮开始 {#team-events}

### 3.1 Mailbox：工具确认和后续结果分开 {#team-mailbox}

**所属层：** MessageBus 内部通信。`send` 把 from、to、content、type、ts、metadata 追加到目标 JSONL 文件，然后唤醒同进程里等待收信的队友。

```python
def send(self, from_agent: str, to_agent: str, content: str,
         msg_type: str = "message", metadata: dict | None = None):
    msg = {"from": from_agent, "to": to_agent,
           "content": content, "type": msg_type,
           "ts": time.time(), "metadata": metadata or {}}
    with self._changed:
        MAILBOX_DIR.mkdir(parents=True, exist_ok=True)
        with self._path(to_agent).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(msg, ensure_ascii=True) + "\n")
        self._changed.notify_all()
    print(f"  [bus] {from_agent} -> {to_agent}: "
          f"({msg_type}) {content[:50]}")
```

运行时创建 `RLock` 和与它绑定的 `Condition`。这些对象是内部状态，不会发送给模型。下面的读操作持锁，取出所有行后删除收件箱文件：

```python
def read_inbox(self, agent: str) -> list[dict]:
    with self._lock:
        return self._read_unlocked(agent)
```

```python
def _read_unlocked(self, agent: str) -> list[dict]:
    inbox = self._path(agent)
    if not inbox.exists():
        return []
    msgs = [json.loads(line) for line in inbox.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    inbox.unlink()
    return msgs
```

```python
def peek(self, agent: str) -> bool:
    with self._lock:
        inbox = self._path(agent)
        return inbox.exists() and inbox.stat().st_size > 0
```

```python
def wait_for_messages(self, agent: str,
                      timeout: float | None = None) -> list[dict]:
    """Block until the agent has messages or timeout expires."""
    deadline = None if timeout is None else time.monotonic() + timeout
    with self._changed:
        while not self.peek(agent):
            remaining = (None if deadline is None
                         else deadline - time.monotonic())
            if remaining is not None and remaining <= 0:
                return []
            self._changed.wait(remaining)
        return self._read_unlocked(agent)
```

因此收信具有“取走”语义；文件保存消息不等于完整可靠队列，读完但尚未注入模型时没有持久 ACK／重投协议。邮箱锁和 Condition 仅协调当前进程；不要与任务认领使用的跨进程文件锁混淆。

启动返回的 `tool_result` 是“队友启动了”。稍后的 `result` 和 `idle_notification` 是不同类型的团队事件，详见 [S13.1 消息协作](01-team-messaging/)。

### 3.2 队友何时收信 {#team-inbox}

**所属层：** `TeammateRuntime.handle_inbox` 将普通消息变成自己的 user 消息，审批／关机走协议校验。只有匹配的 shutdown_request 才会确认并要求退出。

```python
def handle_inbox(self, inbox: list[dict]) -> bool:
    """Append work messages and return True for a valid shutdown."""
    work_messages = []
    for msg in inbox:
        msg_type = msg.get("type", "message")
        if msg_type == "shutdown_request":
            accepted, notice = apply_shutdown_request(self.name, msg)
            if not accepted:
                work_messages.append(notice)
                continue
            BUS.send(self.name, "lead", "Shutdown acknowledged.",
                     "shutdown_response",
                     {"request_id": notice, "approve": True})
            return True
        if msg_type == "plan_approval_response":
            _, notice = apply_plan_response(self.name, msg)
            work_messages.append(notice)
            continue
        if msg_type == "plan_request":
            work_messages.append(f"[Plan required] {msg['content']}")
            continue
        work_messages.append(
            f"[Message from {msg['from']}] {msg['content']}"
        )
    if work_messages:
        self.messages.append({"role": "user",
                              "content": "\n".join(work_messages)})
    return False
```

WORK 在每次模型请求前收信；IDLE 在等待函数中收信。正在运行的模型请求或 Bash 不会被新消息立即打断，同一批工具执行中也不会重新读邮箱。关机属于协作式退出，不是强行终止进程。

### 3.3 Lead 的唤醒在 CLI 外层 {#team-wake}

**所属层：** CLI 事件入口。Lead 空闲时，`wait_for_cli_event` 检查收件箱，也用 select 等待用户输入。收到团队事件就返回 wake；不是让模型调用 check_inbox 反复查询。

```python
def wait_for_cli_event() -> tuple[str, str | None]:
    prompt_visible = False
    while True:
        if BUS.peek("lead"):
            if prompt_visible:
                print()
            return "wake", None
        if not prompt_visible:
            print("s13 >> ", end="", flush=True)
            prompt_visible = True
        readable, _, _ = select.select([sys.stdin], [], [], 0.25)
        if readable:
            line = sys.stdin.readline()
            if line == "":
                return "quit", None
            return "user", line.rstrip("\n")
```

**所属层：** 事件消费与格式转换。先匹配响应更新协议状态，再将事件写成 `[Team events]` 文本，追加到 Lead 的 user 消息。

```python
def consume_lead_inbox() -> list[dict]:
    """Consume Lead events and update protocol state before model delivery."""
    msgs = BUS.read_inbox("lead")
    for msg in msgs:
        metadata = msg.get("metadata", {})
        request_id = metadata.get("request_id", "")
        if request_id and msg.get("type", "").endswith("_response"):
            match_response(msg["type"], request_id,
                           metadata.get("approve", False),
                           msg.get("from", ""), msg.get("to", ""))
    return msgs
```

```python
def format_team_events(msgs: list[dict]) -> str:
    lines = []
    for msg in msgs:
        metadata = msg.get("metadata", {})
        request_id = metadata.get("request_id")
        suffix = f" request_id={request_id}" if request_id else ""
        lines.append(
            f"[{msg['type']}{suffix}] {msg['from']}: {msg['content']}"
        )
    return "[Team events]\n" + "\n".join(lines)
```

唤醒只在 CLI 回到这个等待入口后发生；Lead 当前回合中途不会被邮箱事件抢占。各队友的工具结果留在其私有历史中，Lead 接收的是汇报和事件，不是合并整份队友上下文。

### 3.4 IDLE：先等消息，超时再发现任务 {#team-idle}

**所属层：** `TeammateRuntime.wait_for_work`。输入本队友的身份和共享任务板；收到消息则继续，超时后尝试认领 ready task，成功把任务及目录追加为新 user 消息。

```python
def wait_for_work(self) -> bool:
    """Wait for a message or atomically claim the next ready Task."""
    while True:
        inbox = BUS.wait_for_messages(self.name, IDLE_SCAN_INTERVAL)
        if inbox:
            before = len(self.messages)
            if self.handle_inbox(inbox):
                return False
            if len(self.messages) > before:
                return True
            continue

        task = claim_next_task(self.name)
        if not task:
            continue
        cwd = assignment_cwd(self.name)
        self.messages.append({
            "role": "user",
            "content": (
                f"[Auto-claimed task {task.id}] {task.subject}\n"
                f"{task.description}\nWork directory: {cwd}"
            ),
        })
        print(f"  [idle] {self.name} claimed {task.id}: {task.subject}")
        return True
```

`IDLE_SCAN_INTERVAL = 2.0`。等待消息靠 Condition，没有每两秒向模型提问；只有收到工作消息或认领成功才进入下一次 WORK。已有 assignment 的队友不会自动接手第二项任务。

下面两步把候选发现与最终认领分开。扫描结果可能过时，`claim_task` 必须在锁内重新检查：

```python
def scan_unclaimed_tasks() -> list[Task]:
    """Return ready tasks whose optional worktree binding is usable."""
    with task_lock:
        ready = []
        for task in list_tasks():
            if (task.status != "pending" or task.owner is not None
                    or not can_start(task.id)):
                continue
            _, error = task_worktree_cwd(task)
            if not error:
                ready.append(task)
        return ready
```

```python
def claim_next_task(name: str) -> Task | None:
    """Claim the first still-available task, never a second assignment."""
    with task_lock:
        if teammate_assignments.get(name) or _owner_in_progress(name):
            return None
    for task in scan_unclaimed_tasks():
        result = claim_task(task.id, owner=name)
        if result.startswith("Claimed "):
            return load_task(task.id)
    return None
```

```python
def claim_task(task_id: str, owner: str = "agent") -> str:
    """Atomically claim one task and bind the owner's filesystem cwd."""
    with task_store_lock():
        task = load_task(task_id)
        if task.status != "pending":
            return f"Task {task_id} is {task.status}, cannot claim"
        if task.owner:
            return f"Task {task_id} is already owned by {task.owner}"
        assignment = teammate_assignments.get(owner)
        if assignment:
            return (f"Owner {owner} must finish the current work turn for "
                    f"{assignment['task_id']} before claiming another task")
        current = _owner_in_progress(owner)
        if current:
            return (f"Owner {owner} must complete {current.id} before "
                    "claiming another task")
        if not can_start(task_id):
            return f"Blocked by: {_incomplete_dependencies(task)}"
        cwd, error = task_worktree_cwd(task)
        if error:
            return f"Cannot claim {task_id}: {error}"
        task.owner = owner
        task.status = "in_progress"
        save_task(task)
        teammate_assignments[owner] = {"task_id": task.id, "cwd": cwd}
        advance_assignment_version(owner)
    print(f"  [claim] {task.subject} -> in_progress (owner: {owner})")
    return f"Claimed {task.id} ({task.subject})"
```

任务依赖、锁与 owner 的完整说明见 [S13.3 任务认领](03-task-claiming/)。任务需要单独目录时，先在 pending、未认领状态创建并绑定 worktree，再交给队友；详见 [S13.4 工作目录](04-worktree-isolation/)。

### 3.5 真正退出：清理角色与任务归属 {#team-exit}

**所属层：** 任务归属清理。线程退出时，尚在进行中的任务改回 pending 并清 owner；移除 assignment，推进版本使旧审批失效。

```python
def release_teammate_assignment(owner: str):
    """Return abandoned teammate work to the task board on thread exit."""
    with task_lock:
        try:
            task = _owner_in_progress(owner)
            if task:
                task.status = "pending"
                task.owner = None
                save_task(task)
        finally:
            teammate_assignments.pop(owner, None)
            advance_assignment_version(owner)
            if owner in globals().get("plan_gates", {}):
                globals()["plan_gates"][owner] = "not_required"
```

`TeammateRuntime.run` 的 finally 还会移除运行中的队友、计划闸门和线程注册。退出时不删除任务、分支或 worktree；工作目录的保留与移除另有生命周期。

## 4. 串回主循环，并按问题进入子章节 {#team-recap}

### 4.1 Lead 的基础循环仍然保留 {#team-lead}

**所属层：** Lead Harness 的模型／工具循环。传入 history，发送 SYSTEM 和 TOOLS；追加模型回答，有工具就执行并追加 tool_result，无工具则结束本轮。

```python
def agent_loop(messages: list):
    while True:
        try:
            response = client.messages.create(
                model=MODEL,
                system=SYSTEM,
                messages=messages,
                tools=TOOLS,
                max_tokens=8000,
            )
        except Exception as exc:
            messages.append({
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": f"[Error] {type(exc).__name__}: {exc}",
                }],
            })
            release_completed_assignment("agent")
            trigger_hooks("Stop", messages)
            return

        messages.append({"role": "assistant", "content": response.content})
        tool_calls = [
            block for block in response.content if block.type == "tool_use"
        ]
        if not tool_calls:
            release_completed_assignment("agent")
            trigger_hooks("Stop", messages)
            return

        results = []
        for block in tool_calls:
            print(f"> {block.name}")
            output = execute_tool(block)
            print(output[:300])
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
        messages.append({"role": "user", "content": results})
```

这里没有消费 Lead 邮箱的代码。团队事件的接入点位于**外层 CLI**，随后再调用同一个 agent_loop。

### 4.2 把所有流程串起来的伪代码 {#team-pseudocode}

下面是结构伪代码，省略异常、锁、Hooks 与协议细节；函数名对应前面源码，但不是另一份可运行实现：

```python
# Lead CLI: two event sources, one ordinary Agent Loop
while cli_running:
    event = wait_for_cli_event()
    if event.kind == "quit":
        break
    if event.kind == "user":
        lead_history.append(user_message(event.text))
    else:
        messages = consume_lead_inbox()
        if not messages:
            continue
        lead_history.append(user_message(format_team_events(messages)))
    agent_loop(lead_history)

# Inside Lead's tool dispatch
# spawn -> claim initial Task if supplied -> start runtime thread
# immediately return paired tool_result; later events use MessageBus

# Each teammate has its own messages, system and tools
state = "continue"
while state != "stop":
    if state == "idle" and not runtime.wait_for_work():
        break
    state = runtime.work()
# finally: release unfinished assignment and remove runtime registration
```

`work()` 中仍是 S01 的模型／工具循环；`wait_for_work()` 只在这轮没有工具后进入。消息、任务状态和生命周期各负责一个边界，不需要创造新的推理循环。

### 4.3 四个子章节各解决什么 {#team-subchapters}

| 子章节 | 我会在什么问题上回来看 |
|---|---|
| [S13.1 Agent Teams：队友通过消息协作](01-team-messaging/) | 文件放在哪里，结果怎样进入 Lead 和队友上下文 |
| [S13.2 Team Protocols：用结构化请求协调行动](02-team-protocols/) | request_id 怎么对应，计划为何能阻止执行，何时关机 |
| [S13.3 Task Claiming：空闲时认领可执行任务](03-task-claiming/) | 发现与认领为何分两步，依赖和 owner 如何保证 |
| [S13.4 Worktree Isolation：用独立工作目录隔离改动](04-worktree-isolation/) | 任务怎样绑定 cwd，路径和目录生命周期怎样处理 |

### 4.4 我的理解与本例边界 {#team-understanding}

我把 Team 看成几个熟悉循环之间的协调层：**消息决定下一轮收到什么，任务板决定谁能做什么，协议决定何时允许执行，worktree 决定默认在哪里做。**

它没有自动合并分支、自动判定结果正确或跨进程可靠投递保证。独立上下文不等于独立目录；线程常驻不等于重启后自动恢复所有会话。源码依赖 `fcntl` 和终端 `select`，应按当前 Unix 环境阅读，而不是把提示里的 Windows 分支当成完整跨平台支持。
