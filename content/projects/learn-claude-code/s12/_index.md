---
title: "S12 Cron Scheduler：按时间表触发任务"
weight: 120
summary: "保存调度规则，到期先入队，Agent 空闲后交付 prompt；模型接收后确认，失败恢复并重投。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s12-chapter-outline" title="S12 本章目录" >}}

## 1. 定位：按时间启动一轮 Agent {#cron-position}

### 1.1 我想弄清楚的问题 {#cron-question}

S11 让已经启动的 Bash 在后台跑，但“明天早上再开始”需要另一种机制：谁检查时间，到点后怎样把工作交给模型？

我的理解是：**Cron Scheduler 保存时间规则和待执行 prompt，到点先排队，再等 Agent 空闲交付一轮；首次模型响应后才确认接收。** 时钟线程不直接执行 Bash，也不每秒调用模型。

源码基准为本地 `ce8f9f1` 的 [s12_cron_scheduler/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s12_cron_scheduler/code.py)。函数按真实源码摘录，伪代码另行注明；按 [MIT 许可](/examples/s12-repo/NOTICE.txt)使用。

### 1.2 与 S10、S11 的区别 {#cron-comparison}

| 机制 | 解决什么 | 保存／交付什么 |
|---|---|---|
| S10 Task System | 工作依赖和进度 | 任务 JSON、状态和 owner |
| S11 Background Tasks | 已启动命令的等待 | bg_id 与后续完成结果通知 |
| S12 Cron Scheduler | 未来何时启动工作 | cron 规则，到期后交付 prompt |

`[Scheduled] run tests` 是待执行任务；S11 的 completed 通知是执行结果。Cron ID、后台 ID 和 S10 任务 ID 没有自动绑定。

### 1.3 整体过程：从 S11 到 S12 {#cron-architecture}

#### 图 1：回顾 S11 的默认总览

{{< architecture from="/projects/learn-claude-code/s11" width="1200" src="images/background-agent-integration.svg" mode="baseline" modified="model,decision,tools,system,handler,pre-event" folded="background-start,background-worker,background-ready" label="图 1：保留 S11 原结构，标出调度注册、模型接收与权限的改造位置" caption="图 1：节点和连线仍是 S11 默认总图。橙色将在本章扩展调度工具、首次响应的接收确认和非交互权限处理；灰色后台启动、worker、结果队列的细节在图 2 回到 S11 索引，通知接口保留。" >}}

#### 图 2：定时 prompt 怎样进入已有系统

{{< architecture-explorer id="s12-cron-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/cron-agent-integration.svg" legend="evolution" label="图 2：定时规则匹配入队，Agent 空闲后交付 Scheduled 用户消息，首个响应后确认接收" caption="图 2：紫色是规则、时间检查、排队、空闲门控和接收状态。调度线程到期只入队；取得会话锁后，prompt 经原消息入口交给模型。首次请求成功确认接收，失败恢复队列；旧后台结果注入接口作为 S11 复习索引保留。" >}}

**比较范围：** 总图延续累积学习骨架；独立 S12 脚本实际只有 S04 的五个基础工具、Hooks，以及三个调度工具，不含 S11 的后台 Bash 或 Memory、Skills、Compact。图里的旧机制不是该脚本已经合入的功能。

这里新增两个线程：计时线程判断是否到期，队列线程等待 Agent 空闲。它们只在启动 CLI 运行时创建；导入模块不会自动启动线程。

#### 图 3：从规则到交付的最小核心

{{< architecture figureId="s12-cron-core" functionExplorer="s12-cron-explorer" width="1000" src="images/cron-core.svg" legend="evolution" label="图 3：登记、轮询、持久入队、空闲交付与接收确认，失败重新入队" caption="图 3：上方是规则到 prompt 的交付过程，下方是持久化、确认和失败恢复。确认表示模型已返回首个响应，不表示测试或其他工作已经完成。点击内部函数名可就近查看源码。" >}}

{{< mechanism-function-index id="s12-cron-functions" explorer="s12-cron-explorer" >}}

## 2. 规则与时间匹配：先记录何时做什么 {#cron-rules}

### 2.1 CronJob 和两个不同的状态 {#cron-state}

```python
@dataclass
class CronJob:
    id: str
    cron: str
    prompt: str
    recurring: bool
    durable: bool
    pending_delivery: bool = False
    last_fired: str | None = None
```

| 字段 | 含义 |
|---|---|
| id / cron / prompt | 哪条规则、何时匹配、交给模型做什么 |
| recurring | True 周期触发；False 首次成功交付后删除 |
| durable | 是否保存到工作目录的 `.scheduled_tasks.json` |
| pending_delivery | 已到期，尚未确认模型接收 |
| last_fired | 最近入队的本地分钟标记，避免同分钟重复触发 |

`scheduled_jobs` 保存已登记规则，`cron_queue` 保存当前待交付项。`cron_lock` 保护这些状态与文件更新；`agent_lock` 另负责序列化会话回合。两把锁解决的问题不同。

### 2.2 校验五字段表达式 {#cron-match}

表达式顺序是 minute、hour、day-of-month、month、day-of-week。支持通配、步长、整数、范围和逗号列表的简单形式：

| 表达式 | 本例含义 |
|---|---|
| `* * * * *` | 每分钟 |
| `0 9 * * *` | 每天本地 09:00 |
| `*/5 * * * *` | 分钟字段为 0、5、10……时匹配 |
| `0 9 * * 1-5` | 周一到周五本地 09:00 |

`validate_cron` 在登记和加载时检查五个字段与范围；内部辅助函数检查每个字段：

```python
def validate_cron(cron_expr: str) -> str | None:
    fields = cron_expr.strip().split()
    if len(fields) != 5:
        return f"Expected 5 fields, got {len(fields)}"

    field_rules = [
        ("minute", 0, 59),
        ("hour", 0, 23),
        ("day-of-month", 1, 31),
        ("month", 1, 12),
        ("day-of-week", 0, 6),
    ]
    for field, (name, minimum, maximum) in zip(fields, field_rules):
        error = _validate_cron_field(field, minimum, maximum)
        if error:
            return f"{name}: {error}"
    return None
```

```python
def _validate_cron_field(field: str, minimum: int, maximum: int) -> str | None:
    if field == "*":
        return None
    if field.startswith("*/"):
        step = field[2:]
        if not step.isdigit() or int(step) <= 0:
            return f"Invalid step: {field}"
        return None
    if "," in field:
        for part in field.split(","):
            error = _validate_cron_field(part.strip(), minimum, maximum)
            if error:
                return error
        return None
    if "-" in field:
        start, end = field.split("-", 1)
        if not start.isdigit() or not end.isdigit():
            return f"Invalid range: {field}"
        start_value, end_value = int(start), int(end)
        if start_value > end_value:
            return f"Range start is greater than end: {field}"
        if start_value < minimum or end_value > maximum:
            return f"Range {field} is outside [{minimum}-{maximum}]"
        return None
    if not field.isdigit():
        return f"Invalid field: {field}"
    value = int(field)
    if value < minimum or value > maximum:
        return f"Value {value} is outside [{minimum}-{maximum}]"
    return None
```

这是教学解析器，不覆盖所有 cron 扩展；星期只接受 0–6，0 表示星期日。步长是在字段取值上匹配，不是“从现在起等 N 分钟”。

### 2.3 登记规则，创建失败时回滚 {#cron-schedule}

**所属层：** `schedule_job` 是 Harness 内部登记逻辑。先校验表达式和非空 prompt，再在锁内分配 ID、登记规则，按需保存。

```python
def schedule_job(cron: str, prompt: str, recurring: bool = True,
                 durable: bool = True) -> CronJob | str:
    error = validate_cron(cron)
    if error:
        return error
    if not prompt.strip():
        return "Prompt cannot be empty"

    with cron_lock:
        job = CronJob(
            id=new_cron_id(),
            cron=cron,
            prompt=prompt,
            recurring=recurring,
            durable=durable,
        )
        scheduled_jobs[job.id] = job
        try:
            if durable:
                save_durable_jobs()
        except Exception:
            scheduled_jobs.pop(job.id, None)
            raise
    print(f"  [cron] scheduled {job.id}: {cron} -> {prompt[:60]}")
    return job
```

```python
def new_cron_id() -> str:
    for _ in range(100):
        job_id = f"cron_{secrets.token_hex(4)}"
        if job_id not in scheduled_jobs:
            return job_id
    raise RuntimeError("Could not allocate a cron job ID")
```

默认 recurring、durable 都为 True。持久保存失败会移除刚登记的规则并抛出异常，工具入口会将它转成错误回复；不会留下一个“说保存成功但只在内存”的新任务。

### 2.4 读取本地时间并判断匹配 {#cron-clock}

计时线程每秒检查一次，实际匹配是分钟级：

```python
def cron_scheduler_loop(stop_event: threading.Event = RUNTIME_STOP):
    while not stop_event.wait(1.0):
        poll_due_jobs(datetime.now())
```

```python
def cron_matches(cron_expr: str, moment: datetime) -> bool:
    fields = cron_expr.strip().split()
    if len(fields) != 5:
        return False

    minute, hour, day, month, weekday = fields
    cron_weekday = (moment.weekday() + 1) % 7
    if not (
        _cron_field_matches(minute, moment.minute)
        and _cron_field_matches(hour, moment.hour)
        and _cron_field_matches(month, moment.month)
    ):
        return False

    day_matches = _cron_field_matches(day, moment.day)
    weekday_matches = _cron_field_matches(weekday, cron_weekday)
    if day == "*" and weekday == "*":
        return True
    if day == "*":
        return weekday_matches
    if weekday == "*":
        return day_matches
    return day_matches or weekday_matches
```

```python
def _cron_field_matches(field: str, value: int) -> bool:
    if field == "*":
        return True
    if field.startswith("*/"):
        return value % int(field[2:]) == 0
    if "," in field:
        return any(_cron_field_matches(part.strip(), value)
                   for part in field.split(","))
    if "-" in field:
        start, end = field.split("-", 1)
        return int(start) <= value <= int(end)
    return value == int(field)
```

分钟、小时、月份必须匹配；日和星期同时受限制时采用 OR。例如 `0 9 1 * 1` 是每月 1 日或每个周一的 09:00，不是必须两者同时满足。计时线程使用 `datetime.now()` 的进程本地时间，不另设时区。

## 3. 到期到交付：排队、空闲与确认 {#cron-delivery}

### 3.1 先持久标记，再放进队列 {#cron-poll}

`poll_due_jobs` 跳过已经 pending 或当前分钟已触发的规则。只有新的匹配才调用内部入队方法：

```python
def poll_due_jobs(moment: datetime):
    minute_marker = moment.strftime("%Y-%m-%d %H:%M")
    with cron_lock:
        for job in list(scheduled_jobs.values()):
            try:
                if job.pending_delivery or job.last_fired == minute_marker:
                    continue
                if cron_matches(job.cron, moment):
                    _enqueue_due_job(job, minute_marker)
                    print(f"  [cron] due {job.id}: {job.prompt[:60]}")
            except Exception as error:
                print(f"  [cron] could not enqueue {job.id}: {error}")
```

```python
def _enqueue_due_job(job: CronJob, minute_marker: str | None = None):
    old_pending = job.pending_delivery
    old_last_fired = job.last_fired
    job.pending_delivery = True
    if minute_marker is not None:
        job.last_fired = minute_marker
    try:
        if job.durable:
            save_durable_jobs()
    except Exception:
        job.pending_delivery = old_pending
        job.last_fired = old_last_fired
        raise
    cron_queue.append(job)
```

`_enqueue_due_job` 先保存 pending_delivery 和 last_fired，成功后才追加内存队列。保存失败恢复旧字段，轮询层记录错误；失败项不会以未保存的新状态交给 Agent。

只要仍 pending，下一分钟也不会再入队。确认后恢复周期触发，同时 last_fired 防止在原分钟内重触发。

### 3.2 取得 Agent 锁后启动回合 {#cron-dispatch}

**所属层：** 队列线程不判断时间，只看队列和 `agent_lock`。无法立即取得锁就继续等待，不打断当前回合。

```python
def queue_processor_loop(stop_event: threading.Event = RUNTIME_STOP):
    while not stop_event.wait(0.2):
        if not has_cron_queue() or not agent_lock.acquire(blocking=False):
            continue
        try:
            if has_cron_queue():
                run_agent_turn_locked()
        finally:
            agent_lock.release()
```

```python
def has_cron_queue() -> bool:
    with cron_lock:
        return bool(cron_queue)
```

内部回合编排函数如下。它虽叫 `run_agent_turn_locked`，却不是模型工具入口，不在 TOOL_HANDLERS 中；调用者已经持有 agent_lock：

```python
def run_agent_turn_locked(user_query: str | None = None):
    if user_query is not None:
        trigger_hooks("UserPromptSubmit", user_query)
        session_history.append({"role": "user", "content": user_query})
    agent_loop(session_history)
    print_latest_assistant_text(session_history)
    print()
```

用户主线程也是 `with agent_lock` 后调用同一函数，所有回合共享 `session_history`。等待键盘输入时没有占用这把锁，所以调度线程可以在用户没有新输入时推进。用户回合入口也可能取到尚未消费的定时队列。

### 3.3 首次响应成功才确认接收 {#cron-ack}

Agent Loop 入口先取走队列，追加 `[Scheduled]` 用户消息。取走并不马上清 pending；调用模型成功后才确认：

```python
def consume_cron_queue() -> list[CronJob]:
    with cron_lock:
        jobs = list(cron_queue)
        cron_queue.clear()
    return jobs
```

```python
def acknowledge_cron_jobs(jobs: list[CronJob]):
    changed: list[tuple[CronJob, bool]] = []
    removed: list[CronJob] = []
    with cron_lock:
        for delivered in jobs:
            current = scheduled_jobs.get(delivered.id)
            if current is None:
                continue
            changed.append((current, current.pending_delivery))
            if current.recurring:
                current.pending_delivery = False
            else:
                removed.append(current)
                scheduled_jobs.pop(current.id)

        try:
            if any(job.durable for job, _ in changed):
                save_durable_jobs()
        except Exception:
            for job in removed:
                scheduled_jobs[job.id] = job
            for job, pending in changed:
                job.pending_delivery = pending
            queued_ids = {job.id for job in cron_queue}
            for job, _ in changed:
                if job.id not in queued_ids:
                    cron_queue.append(job)
            raise
```

周期任务清除 pending，一次性任务删除。确认的时机是模型返回首个响应，工具调用尚可能没有执行；它不代表工作产物已完成。

若确认持久化失败，函数回滚规则状态并重新入队。外层 Agent Loop 记录该错误，仍处理已收到的响应，因此后续可能重复交付。

### 3.4 请求失败怎样恢复 {#cron-restore}

首次模型请求失败时，Agent Loop 删除本次附加的定时消息，并将尚未确认的规则重新入队：

```python
def restore_cron_jobs(jobs: list[CronJob]):
    with cron_lock:
        queued_ids = {job.id for job in cron_queue}
        for delivered in jobs:
            current = scheduled_jobs.get(delivered.id)
            if current is None:
                continue
            current.pending_delivery = True
            if current.id not in queued_ids:
                cron_queue.append(current)
                queued_ids.add(current.id)
```

取消过的规则不会再恢复；恢复时检查队列已有 ID，避免追加重复队列项。它恢复的是交付状态，不回滚模型已经执行过的工作。

完整流程示例：09:00 匹配规则，先保存 pending=True 并排队；Agent 忙就等待。空闲后将 prompt 送给模型，成功响应后确认；若首次请求失败则保留规则并重投。规则“完成交付”和实际任务“完成工作”是两个状态。

## 4. 持久化、工具入口与真实边界 {#cron-integration}

### 4.1 三个工具与内部实现 {#cron-tools}

| 模型工具名 | 工具入口 | 内部实现 |
|---|---|---|
| schedule_cron | run_schedule_cron | schedule_job：登记并按需保存 |
| list_crons | run_list_crons | 锁内读取规则快照，格式化文本 |
| cancel_cron | run_cancel_cron | cancel_job：删除规则和待交付项 |

schema 和内部函数的对应关系如下，省略原来的五个工具：

```python
TOOL_HANDLERS.update({
    "schedule_cron": run_schedule_cron,
    "list_crons": run_list_crons,
    "cancel_cron": run_cancel_cron,
})
```

schedule_cron 的参数是 cron、prompt，另有可选 recurring、durable 两个 boolean。模型收到的是 schema；本地函数不通过 tools 字段发送。

取消的内部实现会同时过滤队列，持久保存失败则恢复原规则和队列：

```python
def cancel_job(job_id: str) -> str:
    with cron_lock:
        job = scheduled_jobs.get(job_id)
        if job is None:
            return f"Job {job_id} not found"

        previous_queue = list(cron_queue)
        scheduled_jobs.pop(job_id)
        cron_queue[:] = [queued for queued in cron_queue if queued.id != job_id]
        try:
            if job.durable:
                save_durable_jobs()
        except Exception:
            scheduled_jobs[job_id] = job
            cron_queue[:] = previous_queue
            raise
    print(f"  [cron] cancelled {job_id}")
    return f"Cancelled {job_id}"
```

取消不能撤销已经发给模型的 prompt，也没有停止当前工具进程的操作。实际工具执行继续通过原统一入口：

```python
def execute_tool(block) -> str:
    blocked = trigger_hooks("PreToolUse", block)
    if blocked is not None:
        return str(blocked)

    handler = TOOL_HANDLERS.get(block.name)
    try:
        output = handler(**block.input) if handler else f"Unknown: {block.name}"
    except Exception as error:
        output = f"Error: {error}"
    trigger_hooks("PostToolUse", block, output)
    return str(output)
```

### 4.2 保存与启动恢复 {#cron-durable}

**所属层：** 内部持久化。只写 durable 规则，文件也包含 pending_delivery 和 last_fired：

```python
def save_durable_jobs():
    with cron_lock:
        payload = [
            asdict(job)
            for job in scheduled_jobs.values()
            if job.durable
        ]
        temporary = DURABLE_PATH.with_name(
            f"{DURABLE_PATH.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        try:
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.replace(temporary, DURABLE_PATH)
        finally:
            temporary.unlink(missing_ok=True)
```

使用临时文件和 `os.replace` 替换，避免直接覆盖时留下半份 JSON。cron_lock 是进程内的可重入锁，因为登记或确认函数可能在已经持锁时再次调用保存；这不是多个 Agent 进程之间的文件锁。

启动恢复会报告损坏文件，并跳过不合法的条目；pending 规则直接重新进入交付队列：

```python
def load_durable_jobs():
    if not DURABLE_PATH.exists():
        return
    try:
        payload = json.loads(DURABLE_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("expected a JSON list")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"  [cron] could not load {DURABLE_PATH.name}: {error}")
        return

    loaded = 0
    with cron_lock:
        for item in payload:
            try:
                job = CronJob(**item)
                error = validate_cron(job.cron)
                if error:
                    raise ValueError(error)
                if not job.id.startswith("cron_"):
                    raise ValueError("invalid job ID")
                if not job.prompt.strip():
                    raise ValueError("prompt cannot be empty")
            except (TypeError, ValueError) as error:
                print(f"  [cron] skipped invalid saved job: {error}")
                continue
            scheduled_jobs[job.id] = job
            if job.pending_delivery:
                cron_queue.append(job)
            loaded += 1
    if loaded:
        print(f"  [cron] loaded {loaded} durable job(s)")
```

如果进程在模型已经收到 prompt、确认状态尚未写入时退出，重启可能再交付同一项。这是至少一次交付的边界；不能保证外部工作只执行一次。

### 4.3 Agent Loop 和运行线程 {#cron-loop}

实际循环如下。到期队列只在进入 `agent_loop` 时消费，不在每次工具回传后的 while 顶部重复注入：

```python
def agent_loop(messages: list, context: dict | None = None):
    fired = consume_cron_queue()
    scheduled_start = len(messages)
    for job in fired:
        messages.append({"role": "user", "content": f"[Scheduled] {job.prompt}"})
        print(f"  [cron] delivered {job.id}: {job.prompt[:60]}")

    waiting_for_ack = list(fired)
    while True:
        try:
            response = client.messages.create(
                model=MODEL,
                system=SYSTEM,
                messages=messages,
                tools=TOOLS,
                max_tokens=8000,
            )
        except Exception as error:
            if waiting_for_ack:
                del messages[scheduled_start:]
                restore_cron_jobs(waiting_for_ack)
            print(f"  [error] {type(error).__name__}: {error}")
            return context

        messages.append({"role": "assistant", "content": response.content})
        if waiting_for_ack:
            try:
                acknowledge_cron_jobs(waiting_for_ack)
            except Exception as error:
                print(f"  [cron] acknowledgement failed: {error}")
            waiting_for_ack = []

        tool_calls = [
            block for block in response.content if block.type == "tool_use"
        ]
        if not tool_calls:
            force = trigger_hooks("Stop", messages)
            if force:
                messages.append({"role": "user", "content": force})
                continue
            return context

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

控制流程伪代码：

```text
scheduler: match local time -> persist pending -> queue prompt
processor: queue exists and agent_lock available -> start turn
turn entry: take queue -> append Scheduled user messages
first model call:
    success -> acknowledge receipt -> normal tool loop
    failure -> remove added messages -> restore queued jobs
```

两个运行线程只在 CLI 调用 start_runtime_threads 后创建；导入模块不启动：

```python
def start_runtime_threads():
    global runtime_started
    with runtime_lock:
        if runtime_started:
            return
        load_durable_jobs()
        RUNTIME_STOP.clear()
        runtime_threads.extend([
            threading.Thread(
                target=cron_scheduler_loop,
                name="cron-scheduler",
                daemon=True,
            ),
            threading.Thread(
                target=queue_processor_loop,
                name="cron-queue-processor",
                daemon=True,
            ),
        ])
        for thread in runtime_threads:
            thread.start()
        runtime_started = True
```

```python
def stop_runtime_threads():
    global runtime_started
    with runtime_lock:
        if not runtime_started:
            return
        RUNTIME_STOP.set()
        for thread in runtime_threads:
            thread.join(timeout=1)
        runtime_threads.clear()
        runtime_started = False
```

退出设置 stop_event 并短暂 join 运行线程，不是操作系统常驻调度器。durable 只让下次启动能恢复规则；关机期间不会到点执行，也不补跑已错过的时间。

### 4.4 权限与我的理解 {#cron-boundaries}

队列处理线程运行的回合不能在终端弹出交互确认，否则会和用户输入竞争：

```python
def request_permission(block, reason: str) -> str | None:
    if threading.current_thread() is not threading.main_thread():
        return "Permission denied: scheduled turns cannot request interactive approval"

    print(f"\n\033[33m[permission] {reason}\033[0m")
    print(f"   Tool: {block.name}({block.input})")
    choice = input("   Allow? [y/N] ").strip().lower()
    if choice not in ("y", "yes"):
        return "Permission denied by user"
    return None
```

因此，需要确认的破坏性命令或工作区外文件访问，在队列处理线程中直接拒绝。这个判断看的是当前线程，不是 prompt 的 `[Scheduled]` 前缀；若用户主线程的回合一起消费了队列，仍按主线程的正常确认逻辑处理。

| 边界 | 本节行为 |
|---|---|
| Agent 忙 | 队列等待，不抢占，不同时改同一会话 |
| Agent 进程关闭 | 不触发；durable 保存规则，不补跑停机时间 |
| 首个模型请求失败 | 恢复待交付项，没有独立的指数退避或最大重试计数 |
| 交付确认 | 只代表首次模型响应成功，不代表工作完成 |
| 重启或确认失败 | 可能重复交付，需要区分交付与外部副作用 |
| 线程来源 | CLI 启动计时和队列线程，模块导入不启动 |

**我的一句话理解：时间线程只负责把未来的 prompt 变成待交付事件，会话空闲后才交给原 Agent Loop；成功接收再确认，失败重投，持久化保存的是规则和交付状态。**
