---
title: "S13.3 Task Claiming：空闲时认领可执行任务"
weight: 30
ShowToc: false
compactDiagramLegends: true
hideMeta: true
ShowPostNavLinks: false
---

{{< chapter-outline id="s13-claim-outline" title="本节目录" >}}

**任务板保存可执行工作，扫描发现候选，锁内认领决定归属。** 队友等待时可以接手 ready task；不是依赖另一轮 LLM 调度。

[返回 S13 总览与三图对照](../#team-architecture)。源码基准为本地 `ce8f9f1` 的 [s13_agent_teams/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s13_agent_teams/code.py)。代码按真实函数摘录，类方法保留 `self`；本页片段用于分步阅读，不是可独立运行的完整程序。按 [MIT 许可](/examples/s13-repo/NOTICE.txt)使用。


## 1. 沿用 S10 的依赖图，增加共享执行约束 {#claim-position}

### 1.1 先建节点，后连依赖，再认领 {#claim-dependencies}

Lead 先 create_task 得到真实 ID，再 update_task(addBlockedBy=[...]) 加依赖。队友只有 list_tasks、claim_task、complete_task，不能修改依赖结构。

```python
# 使用教学源码函数的调用示意，ID 取真实返回值
config = create_task("重构配置加载")
tests = create_task("测试新的配置入口")
update_task(tests.id, addBlockedBy=[config.id])
# config 可认领；tests 要等 config.status == "completed"
```

`Task` 比 S10 多了可选 worktree 字段。没有绑定时 cwd=WORKDIR；绑定失效时任务不可认领，不悄悄退回仓库根目录。

### 1.2 候选发现与最终认领的局部流程 {#claim-diagram}

{{< architecture from="/projects/learn-claude-code/s13" width="1000" src="images/team-claiming.svg" legend="evolution" label="空闲扫描候选，在任务锁内重新校验，保存 owner 与 assignment，完成后释放" caption="扫描可以过时；认领在锁内重新验证状态、依赖和目录。自然语言汇报与任务完成是两件事。 点击函数名定位下方代码。" >}}


## 2. 发现、认领、完成各负责什么 {#claim-functions}

### 2.1 scan_unclaimed_tasks：找候选 {#claim-scan}

**输入：** 共享磁盘任务板。**输出：** pending、无 owner、依赖完成且可选 worktree 有效的 Task 列表。这里只扫描，任务仍可能被别的队友先认领。

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

### 2.2 claim_next_task：尝试当前仍可用的任务 {#claim-next}

**输入：** 队友名字。**输出：** 成功认领的 Task，或 None。已有 assignment / in_progress task 时不再领取第二项；逐个候选调用 claim_task，认领失败就继续。

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

### 2.3 claim_task：锁内验证并绑定 owner / cwd {#claim-atomic}

**所属层：** 任务板内部方法。检查 pending、无 owner、该 owner 无其他归属、依赖已完成、目录有效。成功写入 owner、in_progress，保存任务文件，登记 assignment，并推进工作版本。

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

这就是为什么两个队友同时扫描到一个任务也不应同时领到：最终判断和保存位于同一个 task_store_lock 临界区。示例按列表顺序尝试任务，没有承诺公平、优先级或按角色匹配。

### 2.4 complete_task：只有当前 owner 能完成 {#claim-complete}

**输入：** task_id 与实际调用者 owner。**输出：** 完成说明，以及任务板上当前依赖已满足的待处理任务。**副作用：** 写 completed；要求任务正在进行、属于调用者，且计划闸门允许完成。

```python
def complete_task(task_id: str, owner: str = "agent") -> str:
    """Complete an assignment only when the caller owns it."""
    with task_store_lock():
        task = load_task(task_id)
        if task.status != "in_progress":
            return f"Task {task_id} is {task.status}, cannot complete"
        if task.owner != owner:
            return (f"Task {task_id} is owned by {task.owner}, "
                    f"not {owner}; cannot complete")
        gate = globals().get("plan_gates", {}).get(owner, "not_required")
        if gate in {"required", "pending", "rejected"}:
            return f"Task {task_id} cannot complete while plan status is {gate}"
        assignment = teammate_assignments.get(owner)
        if not assignment or assignment.get("task_id") != task.id:
            cwd, error = task_worktree_cwd(task)
            if error:
                return f"Task {task_id} cannot complete: {error}"
            teammate_assignments[owner] = {"task_id": task.id, "cwd": cwd}
        task.status = "completed"
        save_task(task)
        unblocked = [t.subject for t in list_tasks()
                     if t.status == "pending" and t.blockedBy and can_start(t.id)]
    print(f"  [complete] {task.subject}")
    msg = f"Completed {task.id} ({task.subject})"
    if unblocked:
        msg += f"\nUnblocked: {', '.join(unblocked)}"
        print(f"  [unblocked] {', '.join(unblocked)}")
    return msg
```

这里不会立刻清掉 assignment：同一模型回合后续工具仍需原 cwd。释放发生在一轮工作结束的边界，而不是刚调用 complete_task 的那一刻。

### 2.5 两种释放：正常回合结束与异常退出 {#claim-release}

已完成任务的 assignment 到回合结束才释放。退出时尚未完成的工作则改回 pending、owner=None，可让后续队友重新认领。

```python
def release_completed_assignment(owner: str) -> bool:
    """Release a completed cwd lease only at a model turn boundary."""
    with task_lock:
        assignment = teammate_assignments.get(owner)
        if not assignment:
            return False
        task = load_task(str(assignment["task_id"]))
        if task.status != "completed" or task.owner != owner:
            return False
        teammate_assignments.pop(owner, None)
        advance_assignment_version(owner)
        if owner in globals().get("plan_gates", {}):
            globals()["plan_gates"][owner] = "not_required"
        return True
```

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

## 3. 锁与文件：与邮箱的保证不同 {#claim-storage}

### 3.1 task_store_lock：线程锁加文件锁 {#claim-lock}

**所属层：** 存储互斥辅助。`RLock` 序列化同进程线程；`.tasks/.lock` 的 fcntl.flock 序列化遵守同一契约的其他进程。线程局部 depth 允许嵌套调用，最外层才开锁和解锁。

```python
@contextmanager
def task_store_lock():
    """Serialize task mutations across threads and host processes."""
    with task_lock:
        depth = getattr(_task_store_state, "depth", 0)
        if depth == 0:
            TASKS_DIR.mkdir(parents=True, exist_ok=True)
            handle = TASK_LOCK_PATH.open("a+", encoding="utf-8")
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            _task_store_state.handle = handle
        _task_store_state.depth = depth + 1
        try:
            yield
        finally:
            _task_store_state.depth -= 1
            if _task_store_state.depth == 0:
                handle = _task_store_state.handle
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()
                del _task_store_state.handle
```

认领、创建、更新依赖和保存等使用这条存储锁契约。不是所有读取、worktree Git 操作或内存注册都因此具有跨进程事务性；MessageBus 的锁也只是当前进程里的另一把锁。

### 3.2 save_task：完整替换单个任务文件 {#claim-save}

**输入：** Task。**副作用：** 序列化到临时文件，再 os.replace 更新任务 JSON；finally 清理临时文件。它避免半写入文件，不代表一次更新多个任务的全局事务。

```python
def save_task(task: Task):
    with task_store_lock():
        path = _task_path(task.id)
        temporary = path.with_name(
            f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        try:
            temporary.write_text(
                json.dumps(asdict(task), indent=2), encoding="utf-8"
            )
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
```

### 3.3 从 IDLE 接回工作循环 {#claim-loop}

主章 [wait_for_work](../#team-idle) 先等待邮件，两秒超时才 claim_next_task。认领成功追加 `[Auto-claimed task ...]` 与目录，然后返回 WORK。

任务分配、模型运行和完成检查仍是不同步骤。某个队友如果无工具退出了本轮却未 complete_task，它的任务仍 in_progress，不能直接自动接手另一项。依赖判断和 DAG 创建详见 [S10 Task System](../../s10/)。
