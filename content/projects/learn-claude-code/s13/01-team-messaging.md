---
title: "S13.1 Agent Teams：队友通过消息协作"
weight: 10
ShowToc: false
compactDiagramLegends: true
hideMeta: true
ShowPostNavLinks: false
---

{{< chapter-outline id="s13-messaging-outline" title="本节目录" >}}

我想先弄清楚：**消息放在哪里，谁把它读出，怎样变成下一次模型请求的输入？**

[返回 S13 总览与三图对照](../#team-architecture)。源码基准为本地 `ce8f9f1` 的 [s13_agent_teams/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s13_agent_teams/code.py)。代码按真实函数摘录，类方法保留 `self`；本页片段用于分步阅读，不是可独立运行的完整程序。按 [MIT 许可](/examples/s13-repo/NOTICE.txt)使用。


## 1. 消息在模型上下文之外暂存 {#message-storage}

### 1.1 独立历史，共享邮箱总线 {#message-position}

Lead、config、tests 各有自己的 messages。`BUS` 不把它们合并，而是在 `.mailboxes/<recipient>.jsonl` 写入待投递消息；收信后才进入收件人的上下文。

```text
workspace/
  .tasks/task_1234abcd.json
  .mailboxes/lead.jsonl
  .mailboxes/config.jsonl
  .mailboxes/tests.jsonl
```

邮箱文件只在有待处理消息时存在；消费后文件被删除，不是永久聊天记录。

### 1.2 本地最小流程 {#message-diagram}

{{< architecture from="/projects/learn-claude-code/s13" width="1000" src="images/team-messaging.svg" legend="evolution" label="消息从发送者经文件邮箱进入收件人的私有历史" caption="MessageBus 只负责排队与读取；运行时决定何时注入上下文。 点击函数名定位下方代码。" >}}


### 1.3 消息字段与几种不同用途 {#message-fields}

| 字段 | 用途 |
|---|---|
| from / to | 发送者与收件人 |
| content | 普通协作内容或汇报 |
| type | message、result、idle_notification 或协议类型 |
| ts | 发送时间 |
| metadata | request_id、approve 等协议字段 |

例如下列是**消息结构示意**，不是模型 tool_result：

```json
{"from":"config","to":"lead","content":"配置任务完成，测试通过。","type":"result","ts":0,"metadata":{}}
```

`spawn_teammate` 的 tool_result 仍配对 Lead 当前那次调用 ID。队友最终结果是稍后独立投递的事件；两个消息属于不同时间和不同接口。

## 2. MessageBus 内部怎样收发 {#message-implementation}

### 2.1 初始化与路径检查 {#message-path}

**所属层：** MessageBus 内部状态与辅助方法。名字限 1–64 个字母、数字、下划线或连字符，解析后的路径必须位于 mailbox 根目录。这里验证格式和位置，不负责确认收件人正在运行；普通发送工具另查 active_teammates。

```python
def __init__(self):
    self._lock = threading.RLock()
    self._changed = threading.Condition(self._lock)
```

```python
def _path(self, agent: str) -> Path:
    if not is_valid_agent_name(agent):
        raise ValueError(f"Invalid mailbox recipient: {agent!r}")
    path = (MAILBOX_DIR / f"{agent}.jsonl").resolve()
    if not path.is_relative_to(MAILBOX_ROOT):
        raise ValueError(f"Mailbox path escapes directory: {agent!r}")
    return path
```

### 2.2 send：追加一行并通知等待者 {#message-send}

**输入：** 双方名字、正文、可选类型与 metadata。**副作用：** 在目标文件追加 JSON 行，Condition.notify_all 唤醒本进程的等待者；没有调用模型。

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

### 2.3 read：消费所有消息 {#message-read}

**输入：** 收件人名字。**输出：** 按文件行序读出的消息列表。**副作用：** 删除邮箱文件。`read_inbox` 在锁内调用 `_read_unlocked`，后者不能独立绕过锁使用。

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

### 2.4 wait：等待到消息或超时 {#message-wait}

`peek` 只检查是否有内容，不消费；`wait_for_messages` 在 Condition 上等待，醒来后再次检查条件。有消息才消费，否则超时返回空列表。

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

## 3. 模型何时看到这些消息 {#message-delivery}

### 3.1 队友与 Lead 的消费边界不同 {#message-context}

| 收件人 | 谁读 | 进入什么上下文 |
|---|---|---|
| 队友 WORK | 每次模型请求前的 handle_inbox | 本队友 messages 的 user 内容 |
| 队友 IDLE | wait_for_messages 返回后 | handle_inbox 处理协议或追加工作消息 |
| Lead | CLI 等待入口发现邮件，consume_lead_inbox 消费 | `[Team events]` 作为 Lead 的 user 内容 |

主章保留 [handle_inbox](../#team-inbox)、[wait_for_work](../#team-idle) 和 [CLI 唤醒](../#team-wake) 的完整代码。消息无法中断正在执行的 API 请求或 Bash；它会等到收信边界。

### 3.2 普通消息不等于任务重新分配 {#message-assignment}

“再检查一下错误路径”会进入历史，但不会自动调用 claim_task、改变 owner 或推进 assignment_versions。新的任务归属必须通过任务系统；新的计划要求通过协议入口设置闸门。

文件邮箱提供可见的通信介质，但没有消费 ACK、错误重投或完整重启恢复会话。锁只覆盖同一进程，不能据此认为多个独立进程可以可靠共享这套邮箱。需要更强投递保证时，应另设计消费状态和跨进程协调。
