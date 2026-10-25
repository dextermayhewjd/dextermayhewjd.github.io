# exec_and_wait

> **调用链面包屑**：[Step 7 范围](../../../../../01-scope.md) > [02 短期概览](../../../../overview.md) > 调用来源：[run_agent](../harness/common.py/run_agent.md)（本步 Agent 运行） · [install_npm_cli（Step 5 安装工具）](../../../../../03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) → **exec_and_wait**

- 源码定位：[slime/agent/sandbox.py:99–162](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L99-L162)（附配套轮询函数 `_await_done_marker:79–96`），由助手核对。
- 首次接触：Step 5 提及沙箱命令等待；Step 7 随 `run_agent:111` 首次独立建卡。
- 最近认识更新：2026-10-25，用户表示大致理解 launcher、脱机执行与防重、完成文件轮询三部分；主机仍参与等待、超时不等于进程停止的边界由助手补准，具体机制不扩大为全部掌握。

- 本轮局部校准：2026-10-24，`exec_and_wait` 本体未变，仅更新其依赖的完成文件读取、相关图示和源码位置；[更新前完整卡片](../../../../../references/exec-and-wait-before-read-file-update.md)保留，认识日期不变。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合（通用长任务基础设施）**：
   `exec_and_wait` 是 Slime 沙箱底层（`sandbox.py`）提供的**通用脱机长任务执行基础设施**，其职责远超出单个 `run_agent`：
   - **工具安装阶段（Step 5）**：[`install_npm_cli`](../../../../../03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) 委托它在沙箱安装 Node/CLI，指定 `want_output=True` 捕获安装日志，配合外层重试循环；
   - **Agent 运行阶段（Step 7 当前场景）**：[`run_agent`](../harness/common.py/run_agent.md) 委托它以 `user="agent"` 运行外部 CLI，重定向输出到 `trajectory.jsonl`，设置 `want_output=False` 防止内存膨胀；
   - **其他耗时任务**：未来评测、环境构建等任何无法承受 HTTP/2 网关长连接超时断开的重量级任务。

2. **具体内容**：
   - 生成带退出码捕获的 shell 启动脚本（`launcher_body = ... echo $? > {done_file}`）；
   - 执行短 RPC 清理旧状态，使用 `setsid bash {launcher} ... &` 完全脱机后台拉起；
   - 启动 `_await_done_marker` 循环，每隔 5 秒通过 `sb.read_file` 读取完成文件；文件缺失或内容为空时继续等待，直到读到退出码或超时；
   - 支持 `want_output` 控制输出全量返回还是通过 `tail -c 512` 仅截取尾部错误，返回 `(exit_code, output)` 二元组。

3. **建议构建的心智模型**：

   > `exec_and_wait` 是**沙箱长任务的“脱机运行器”与“保活心跳站”**。
   >
   > 它把对单条长连接的等待，拆成启动与后续完成文件读取三个阶段：
   > 1. **放风筝（Detached Spawn）**：用 `setsid` 让进程在沙箱后台脱离终端常驻运行，进程退出时自行把退出码写入 `.done` 文件；
   > 2. **拉心跳（Keepalive Polling）**：每隔 5 秒读取完成文件；这些读取同时具有让后端感知活动的设计用途；
   > 3. **收风筝（Reap Exit Code）**：从 marker 文件中读取整数退出码原样返回。

4. **调用代码**（本步 `slime/agent/harness/common.py:115–125`）：

   ```python
   exit_code, _ = await exec_and_wait(
       sb,
       cmd=start_cmd,
       user="agent",
       env=env,
       workdir=workdir,
       out_file=f"{meta_dir}/trajectory.jsonl",
       time_budget_sec=time_budget_sec,
       tag="run",
       want_output=False,
   )
   ```

## 本场景的输入与输出

接住 [run_agent](../harness/common.py/run_agent.md) 的启动参数：以 `agent` 用户身份运行 Claude Code CLI，并将输出定向到 `.harness/trajectory.jsonl`。

**输入：沙箱对象、待执行命令、超时预算、标签、用户、环境变量、工作目录与输出文件。**

```python
# sb: E2BSandbox 对象
cmd = "/usr/local/bin/claude -p '...' --permission-mode bypassPermissions"
time_budget_sec = 300
tag = "run"
user = "agent"
env = {"ANTHROPIC_BASE_URL": "http://adapter:18001", "ANTHROPIC_AUTH_TOKEN": "sid-demo"}
workdir = "/workspace/auth0-python"
out_file = "/workspace/auth0-python/.harness/trajectory.jsonl"
want_output = False
```

**输出：退出码与输出字符串的二元组 `tuple[int, str]`。**

```python
exit_code = 0  # int
output = ""    # str (因 want_output=False 且 exit_code==0，返回空串避免内存膨胀)
```

### 架构与执行流程

```
 宿主机 (Python: Slime)                                   远端沙箱容器 (E2B Container)
       │                                                              │
       │ 1. sb.write_file(launcher)                                   │
       │ ───────────────────────────────────────────────────────────> │ 写入 /tmp/.run.sh:
       │    (短 RPC: 写入启动脚本，含 echo $? > /tmp/.run.done)       │   cd /workspace/auth0-python
       │                                                              │   export HOME=/home/agent
       │                                                              │   /usr/local/bin/claude -p ...
       │                                                              │   echo $? > /tmp/.run.done
       │                                                              │
       │ 2. sb.exec("rm -rf ...")                                     │
       │ ───────────────────────────────────────────────────────────> │ 清理上一轮旧锁与旧 marker 文件
       │                                                              │
       │ 3. sb.exec("setsid bash launcher < /dev/null > out 2>&1 &")  │
       │ ───────────────────────────────────────────────────────────> │ 真正的脱机后台拉起 (setsid)
       │    (短 RPC: 触发后立即返回，不长久挂着连接)                   │  ├─ 外部 Agent CLI 开始独立运行
       │                                                              │  └─ stdout/stderr 写入 trajectory.jsonl
       │                                                              │
       │ 4. _await_done_marker 轮询与保活循环                         │
       │ ── sb.read_file("/tmp/.run.done")               ───────────> │ 探查 marker 是否生成
       │ <─ [文件缺失或内容为空] ──────────────────────────────────── │ (Agent 还在读题/改代码...)
       │    (每隔 5 秒读取文件；读取产生后端活动)                     │
       │                                                              │
       │ ── sb.read_file("/tmp/.run.done")               ───────────> │ 探查 marker 是否生成
       │ <─ [out="0\n"]       ─────────────────────────────────────── │ (Agent 退出，写入了 0)
       │                                                              │
       ▼                                                              ▼
 返回 (0, "")
```

### 1. 组装 launcher 脚本与清理旧状态（124–145）

```python
out_file = out_file or f"/tmp/.{tag}.out"
done_file = f"/tmp/.{tag}.done"
launcher = f"/tmp/.{tag}.sh"
lock_dir = f"/tmp/.{tag}.spawned"
prefix = f"cd {workdir}\nexport HOME=/home/{user}\n" if workdir else ""
launcher_body = f"#!/bin/bash\n{prefix}{cmd}\necho $? > {done_file}\n"
await sb.write_file(launcher, launcher_body, user=user)

await sb.exec(
    f"rm -rf {lock_dir}; rm -f {out_file} {done_file}",
    user=user,
    timeout=30,
    check=True,
    idempotent=True,
)
```

- **脚本捕获退出码**：`launcher_body` 结尾追加 `echo $? > {done_file}`，确保被执行进程退出时其退出状态一定落盘。
- **清理隔离**：先清理上一次 invocation 留存的锁和标记，避免复用旧的残留状态。

### 2. 脱机执行与幂等防护（146–155）

```python
await sb.exec(
    f"chmod +x {launcher}; "
    f"mkdir {lock_dir} 2>/dev/null || exit 0; "
    f"setsid bash {launcher} < /dev/null > {out_file} 2>&1 &",
    user=user,
    env=env,
    timeout=30,
    check=True,
    idempotent=True,
)
```

- **`setsid` 脱钩**：创建新的会话，断开进程与原控制终端的所有联系；
- **重定向守护**：`< /dev/null > {out_file} 2>&1 &` 将标准输入脱钩、输出打到轨迹文件并置入后台；
- **启动与等待分开**：该 RPC 负责触发后台启动，返回后主机中的 Slime 仍会读取完成文件，等待结果或达到预算；“脱机”不表示主机已退出整个流程。

### 3. 轮询完成文件（156；`_await_done_marker:79–96`）

```python
async def _await_done_marker(sb: Sandbox, done_file: str, *, user: str, time_budget_sec: int) -> int:
    deadline = time.time() + time_budget_sec
    while time.time() < deadline:
        await asyncio.sleep(5)
        try:
            out = await sb.read_file(done_file, user=user)
        except FileNotFoundError:
            continue
        if (out or "").strip():
            return int(out.strip())
    return EXIT_TIME_BUDGET_EXCEEDED  # -1
```

- **读取结果**：文件缺失时捕获 `FileNotFoundError`，内容为空也继续等待；读到非空文本后转成整数退出码。到达等待期限时返回 `-1`。
- **读取的作用与边界**：用短文件读取持续检查完成状态，源码也将这些读取用于后端保活。其他读取异常仍可向上传播；超时返回没有在此停止后台进程。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [run_agent，111–126](../harness/common.py/run_agent.md)：上层调用入口（本步） | 拿到 `exit_code`，返回给上游 `launch_and_wait` |
| [install_npm_cli，82–100](../../../../../03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)：上层调用入口（Step 5） | 拿到 `(exit_code, last_log)`，判断重试或进入下一步 |

## 我的直接表述（原话）

2026-10-25，对本函数三部分职责的反馈：

> 好的 我大概明白了
> 职责还是没有变化
> 还是这三个部分对吗?
> 我其实不是特别清楚了
> 感觉绝大多数内容都是在除了sandbox 内部到底需压迫执行什么
> 当然这里有你说的这几个组装launcher 还有脱机执行和迷瞪保护
> 还有轮训完成文件等一系列内容
> 这些其实我差不多都明白了
> 总的来说就是脱离了主机 让起能够在sandbox中自动运行直到结束的部分对吧
> 除此之外之外这一个step还有什么需要了解和看的吗?

“脱离主机”在本层需补准为后台运行与主机监控并存，见[本轮反馈与收束](../../../../../04-flow.md#harness-execution-closure-20261025)。

2026-10-23，用户针对本机制提出拆分主体与读面包屑的建卡建议：

> 好的那么请按照这种方式来写一下这里的主题函数以及独立卡片什么的吧

2026-10-23，用户明确指出跨函数链接、职责边界与面包屑处理需求：

> 我这里大概明白了那么这里是否需要考虑一下这里的run agent需要和exec_and_wait至少给一个链接呢？
> run agent的职责是这些 但是这里exec_and_wait的职责不止这些
>
> 以及考虑一下应该如何处理这里的面包屑问题吧

助手核对：
- 用户极其精准地指出了层次分工：`run_agent` 是 Harness 的上层特化调用者（职责仅为准备 `.harness` 目录赋权并传参启动），而 `exec_and_wait` 是底层通用长任务运行基座（职责涵盖安装重试、Agent 运行、防断连脱机与保活轮询），两者职责范围完全不同。
- 已建立双向相对超链接（修复相对跳转路径）；
- 在卡片顶部建立统一调用链面包屑（Breadcrumb Trail），指明当前业务入口与读完返回路径。

2026-10-23，整条启动链的复述节选（完整原话见[本次讨论](../../../../../04-flow.md#launch-restatement-and-http-entry)）：

> 2.1具体运行部分所需要做的内容
> 2.2第二是 脱机执行和幂等保护
> 2.3 第三各是轮训marker与防闲置gc的设定

助手校准：这几项属于被 `run_agent` 委派的执行机制。源码中的目录保护针对同一次启动的传输重试；轮询读取退出码，保活是源码注明的设计目的，未做远端验证。

## 尚不清楚

- 用户已能列出运行材料、脱机与防重、marker 轮询与保活三个阶段；launcher、`setsid`、5 秒轮询等具体关系由源码解释，尚未逐项确认或做远端验证。
- 尚不清楚：若 Agent 运行超时触发 `EXIT_TIME_BUDGET_EXCEEDED (-1)`，沙箱内的后台脱机进程由谁负责 `kill` 清理。

<details>
<summary>来源、验证与完整例子</summary>

- 当前源码定位：`slime/agent/sandbox.py:99–162` 与 `slime/agent/sandbox.py:79–96`；`exec_and_wait` 本体与旧版 AST 相同，变化位于调用的 `_await_done_marker`。完整旧版来源见[更新前卡片](../../../../../references/exec-and-wait-before-read-file-update.md)。
- 上层调用者：`slime/agent/harness/common.py:115–125`（`run_agent`）。
- 官方设计依据：Docstring 明确指出 `plain sb.exec keeps an HTTP/2 stream open for the command's whole runtime... the stream gets severed mid-run... polling doubles as an idle-GC keepalive`。
- 形成过程：[Step 7 · run_agent 与 exec_and_wait 脱机机制](../../../../../04-flow.md#run-agent-and-exec-and-wait)。

</details>
