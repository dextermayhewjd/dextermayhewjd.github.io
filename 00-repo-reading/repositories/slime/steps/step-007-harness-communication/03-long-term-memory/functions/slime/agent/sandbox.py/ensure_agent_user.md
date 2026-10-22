# ensure_agent_user

- 源码定位：[slime/agent/sandbox.py:390–399](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L390-L399)，由助手核对。
- 首次接触：Step 2，2026-10-21，从 `_grade_scaleswe` 中 `ev` 的第一次使用处进入。
- 最近认识更新：2026-10-22，用户在概括已有沙箱中的目录、Git 与权限准备，并收到账号/目录归属的澄清后，反馈“大概理解了”，希望继续。记录为本函数职责层面的大致理解；具体 shell 语法与 SDK 实现仍未展开。Step 2 的原有复述继续保留。
- 前序记录：[累计记忆中的完整卡片](../../../../../../step-006-prepare-workspace/03-long-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)，源自 [Step 2](../../../../../../step-002-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)。本页保留原话与未知，使用当前执行沙箱的场景解释。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`boot_agent_sandbox` 已交出安装好 CLI 的 `sb`。`prepare_workspace` 在执行任务初始化、以 `agent` 身份写入题目文件前，先调用本函数准备这个用户及目录归属。

2. **具体内容**：把 `workdir` 拼入一条组合命令，通过 `sb.exec` 以 `root` 身份执行，确保 Linux 用户 `agent` 存在，设置目录归属和 Git 安全目录配置。正常返回 `None`。

3. **建议构建的心智模型**：

   > `ensure_agent_user` 接住已有沙箱和工作目录，为后续以 `agent` 身份进行的操作准备账号、目录归属和 Git 设置。
   >
   > 它把准备命令交给 `sb.exec` 在远端执行；返回后，调用方继续使用同一个沙箱。

4. **调用代码**（`swe.py:185–187`，本函数返回后继续查看任务配置）：

   ```python
   await agent_sandbox.ensure_agent_user(sb, workdir)
   if md.get("protocol") == PROTOCOL_SCALESWE:
       grading = md.get("grading") or {}
   ```

## 本场景的输入与输出

承接 [prepare_workspace 的输入示例](../../../examples/coding_agent_rl/swe.py/prepare_workspace.md)：执行沙箱和 CLI 已就绪，镜像中的 `/workspace/repo` 已存在。以下变化按正常路径推导，未在真实远端执行。

**输入：已有沙箱对象与工作目录。**

```python
# sb：boot_agent_sandbox 交出的 E2BSandbox 对象
workdir = "/workspace/repo"
await agent_sandbox.ensure_agent_user(sb, workdir)
```

<a id="sandbox-protocol"></a>

调用处的 `agent_sandbox` 是 `sandbox.py` 模块的别名；`agent` 则是沙箱操作系统里的用户名。

| 名称 | 在本次调用中的含义 |
| --- | --- |
| `Sandbox` | 参数类型所约定的沙箱接口；本函数只需要其中的 `exec` 能力 |
| `sb` | 已有的本地 `E2BSandbox` 对象，通过它操作此前创建的远端沙箱 |
| `sb.exec(...)` | 本例进入 `E2BSandbox.exec`，把命令提交到对应的远端沙箱执行 |

对象与远端的关系可回查 [E2BSandbox 类卡片](../../../../classes/slime/agent/sandbox.py/E2BSandbox.md)；这里沿用已有对象。

**输出：返回 `None`，准备效果留在远端沙箱。**

| 项目 | 正常完成后的结果 |
| --- | --- |
| Linux 用户 | `agent` 已存在；原先没有时创建，并建立其主目录、指定默认 shell |
| 目录归属 | `/home/agent` 与 `/workspace/repo` 及其下内容的属主、属组设为 `agent:agent` |
| Git 配置 | 系统级 `safe.directory` 增加 `*`，将所有仓库视为可信目录，避免因目录归属不同而拒绝操作 |
| 返回与交接 | 本函数返回 `None`；`prepare_workspace` 用原来的 `sb` 继续到 186 行查看任务配置 |

**源码与上述结果的对应关系（390–399）：**

```python
async def ensure_agent_user(sb: Sandbox, workdir: str) -> None:
    """Create the unprivileged 'agent' user that owns workdir + can git diff."""
    await sb.exec(
        f"id agent >/dev/null 2>&1 || useradd -m -s /bin/bash agent && "
        f"chown -R agent:agent /home/agent {workdir} && "
        f"git config --system --add safe.directory '*' && id agent",
        user="root",
        check=True,
        timeout=60,
    )
```

- **检查或创建账号**：`id agent` 检查用户是否存在，检查输出被丢弃；失败时才执行 `useradd`，其中 `-m` 创建主目录，`-s /bin/bash` 指定默认 shell。
- **准备已有目录**：检查或创建成功后，`chown -R` 将 `/home/agent` 和本例的 `/workspace/repo` 递归设为 `agent:agent`。即使用户原先存在，这一步仍会执行；它修改目录归属，工作目录本身需要已存在。
- **配置 Git 并检查身份**：前一步成功后添加 Git 可信目录设置，再执行最后的 `id agent`。Git 设置影响 Git 的信任检查，目录的操作权限仍由操作系统决定。
- **一次提交、远端执行**：上面三段字符串组成一条 shell 命令，通过一次 `sb.exec` 提交。Python 函数在本地运行，创建用户、修改目录和 Git 配置都发生在远端沙箱中。
- **由 root 做准备**：本次 `exec` 使用 `user="root"` 来创建账号和修改归属；后面的题目写入另行指定 `user="agent"`。`timeout=60` 是命令超时参数，`check=True` 使本例实现对非零退出抛出异常。
- **返回调用方**：`exec` 返回的退出码、标准输出和标准错误没有被本函数保存，最后的 `id agent` 输出也不会成为本函数返回值。正常结束返回 `None`；异常向外传播。随后回到 `prepare_workspace:186`，继续查看初始化配置。

## 我的直接表述（原话）

2026-10-21，在 Step 2 对调用关系的理解（节选，保留问句）：

> 然后这里的ensure agent user 是执行这个exec 并且是某一条特定的指令？

随后对整体顺序的复述：

> 简单来说就是创建好的了之后 在远端的这个sandbox需要执行这个sandbox的exec的操作
> 具体的含义是下面的一系列内容

2026-10-22，在 Step 6 指定当前阅读入口：

> 那么这里是否应该先考虑展开一下这里的agent_sandbox中的ensure_agent_user呢？

随后对职责的复述：

> 简单来说就是
> 1.确保这里folder的
> 2.配置好一系列需要的部分git
> 3.创建权限
>
> 在已经拿到的稳定连接sandbox中执行这些操作 为了后续能够正常运行

助手核对：这次表述已联系已有沙箱、环境准备与后续运行。这里的“创建权限”具体对应准备 `agent` 账号、设置已有目录的属主和属组；`workdir` 本身应已存在。“稳定连接”在本层可表述为已持有能操作远端沙箱的 `sb` 对象；具体连接机制尚未展开。这些细分说明当时尚待用户反馈。

收到澄清后，用户反馈并要求继续：

> 好的我大概理解了
> 那么现在继续吧
> 下一步是需要做什么呢？

## 尚不清楚

- 具体 shell 语法尚未逐项讨论；当前先建立这组命令的目的与结果。
- `E2BSandbox.exec` 怎样调用 SDK、处理结果和故障，仍作为下一层实现保留。
- 用户已反馈大致理解本函数的准备职责；协议与实际对象的语言机制、本地调用与远端通信的实现仍未逐项展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码同页首；当前调用与后续题目写入见 `swe.py:185–198`，模块别名见 `swe.py:35`，执行接口与实现见 `sandbox.py:28–59、309–340`。原评测场景见 `swe.py:269–270`。
- 原 Step 2 的局部验证从真实源码提取本函数，用替身记录 `exec` 调用，确认组合命令、一次调用、`user="root"`、`check=True`、`timeout=60` 和返回 `None`；没有执行 shell 或申请真实沙箱。本轮只复核源码、调用场景和记录链接。
- [Bash 手册](https://www.gnu.org/s/bash/manual/html_node/Lists.html)说明 `&&` 与 `||` 同优先级、从左结合。对应本例，检查或创建用户成功后，仍继续后面的目录与 Git 准备；不能把整串后续命令都理解为“仅用户不存在时执行”。
- [Git 的 safe.directory 文档](https://git-scm.com/docs/git-config#Documentation/git-config.txt-safedirectory)说明 `*` 的含义；此配置与 `chown` 的文件归属作用分别记录。
- [协议含义与语言依据](../../../../../../step-002-swe-evaluation/references/sandbox-entry.md#protocol-contract)保存《Fluent Python》的双语原文及本仓库的对应关系。
- 原始 Step 2：[名称与阅读层次](../../../../../../step-002-swe-evaluation/04-flow.md#module-function-exec-boundary) · [卡片与协议背景](../../../../../../step-002-swe-evaluation/04-flow.md#ensure-agent-user-card) · [创建完成后执行准备命令](../../../../../../step-002-swe-evaluation/04-flow.md#sandbox-ready-then-command)。
- 原用户表述及记录边界见[当时的讨论](../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#sandbox-memory-entry-boundary)。
- 本轮形成过程：[Step 6 · 从工作区准备进入 ensure_agent_user](../../../../../../step-006-prepare-workspace/04-flow.md#ensure-agent-user-entry)。
- 后续复述与澄清：[Step 6 · 已有沙箱中的运行准备](../../../../../../step-006-prepare-workspace/04-flow.md#ensure-agent-user-restatement)。
- 理解反馈与返回主线：[Step 6 · 继续查看任务初始化配置](../../../../../../step-006-prepare-workspace/04-flow.md#workspace-initialization-next)。

</details>

<details>
<summary>同一函数的前序评测场景：完整记录保留</summary>

以下保留合并前的评测场景、解释与未知；上文为 Step 6 的执行沙箱场景，二者不是同一次运行。

# ensure_agent_user

- 源码定位：[slime/agent/sandbox.py:390–399](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L390-L399)，由助手核对。
- 首次接触：Step 2，2026-10-21，从 `_grade_scaleswe` 中 `ev` 的第一次使用处进入。
- 最近认识更新：2026-10-21，用户已复述“沙箱创建后调用 exec 执行准备内容”的顺序；具体命令、协议关系与本地/远端运行位置仍在核对。

- 本次继承自：[Step 2 的完整记录](../../../../../../step-002-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_grade_scaleswe` 已取得评测环境对象 `ev`，在应用补丁、执行测试前，先准备执行用户和工作目录权限。

2. **具体内容**：将 `workdir` 拼入一条组合命令，通过传入对象的 `exec` 以 root 身份执行，确保 `agent` 用户存在，设置目录归属和 Git 安全目录配置。成功后返回 `None`。

3. **建议构建的心智模型**：

   > `ensure_agent_user` 使用已经创建好的沙箱，准备后续操作需要的用户、目录权限和 Git 设置。
   >
   > 它决定执行什么准备命令；命令怎样在远端运行，由传入对象的 `exec` 方法完成。

4. **调用代码**（`swe.py:269–270`，节选）：

   ```python
   async with E2BSandbox(image) as ev:
       await agent_sandbox.ensure_agent_user(ev, workdir)
   ```

## 本场景的输入与输出

承接 [E2BSandbox.__aenter__](E2BSandbox.__aenter__.md) 的教学场景，假定镜像中的 `/workspace/repo` 已存在。以下环境变化按成功路径推导，未在真实远端执行。

**输入：已有沙箱对象与工作目录。**

```python
# ev：上一张卡片返回的 E2BSandbox 对象；传入后由形参 sb 引用。
workdir = "/workspace/repo"
```

<a id="prior-evaluation-sandbox-protocol"></a>

**参数 `sb: Sandbox` 中的协议关系：**

| 名称 | 在本次调用中的含义 |
| --- | --- |
| `Sandbox` | 约定沙箱应提供的接口，包括 `exec`、文件读写、进入和退出等；本函数只使用其中的 `exec` |
| `sb` | 引用传入的 `ev`；本例实际对象的类型仍为 `E2BSandbox` |
| `sb.exec(...)` | 调用该对象提供的方法，本例执行 `E2BSandbox.exec` |

- `sb: Sandbox` 表达对参数能力的要求；进入本函数时直接使用已有对象。`Sandbox.exec` 的协议声明用于说明接口，具体执行体在 `E2BSandbox.exec` 中。
- 调用处的 `agent_sandbox` 是 `sandbox.py` 模块的别名，用于定位这里的 `ensure_agent_user` 函数。

**成功后的输出与环境变化：**

| 项目 | 结果 |
| --- | --- |
| 当前函数的返回值 | `None`；后续继续使用原来的 `ev` |
| 远端用户 | 已存在 `agent` 用户；缺少时创建 |
| 目录归属 | `/home/agent` 和 `/workspace/repo` 及其下内容的属主、属组设为 `agent:agent` |
| Git 配置 | 系统级 `safe.directory` 增加 `*`，允许 Git 操作不同归属的仓库 |

**本函数怎样使用 `exec`（第 390–399 行）：**

```python
async def ensure_agent_user(sb: Sandbox, workdir: str) -> None:
    """Create the unprivileged 'agent' user that owns workdir + can git diff."""
    await sb.exec(
        f"id agent >/dev/null 2>&1 || useradd -m -s /bin/bash agent && "
        f"chown -R agent:agent /home/agent {workdir} && "
        f"git config --system --add safe.directory '*' && id agent",
        user="root",
        check=True,
        timeout=60,
    )
```

- **用户准备**：先用 `id agent` 检查用户；检查失败时尝试 `useradd`，创建主目录并指定 bash。
- **目录准备**：本例把 `workdir` 替换为 `/workspace/repo`，用 `chown -R` 设置该目录和 `/home/agent` 的归属。
- **Git 准备**：设置 `safe.directory '*'`，最后再执行 `id agent`。这些操作被拼成一条命令字符串，通过一次 `exec` 提交。
- **执行位置**：`ensure_agent_user` 和这里的 `sb.exec` 在本地调用方进程中执行；命令字符串描述的 shell 操作在远端沙箱中执行。
- **执行条件**：以 `root` 执行上述准备，命令时间预算为 60 秒；`check=True` 要求底层在命令失败时报告异常。
- **返回主线**：`exec` 返回的退出码、标准输出和标准错误在这里没有保存；本函数正常结束时返回 `None`，随后回到 `_grade_scaleswe`。异常则向外传播，不在这里转为评分。

## 我的直接表述（原话）

2026-10-21，对当前调用关系的理解（节选，保留问句）：

> 然后这里的ensure agent user 是执行这个exec 并且是某一条特定的指令？

随后对整体顺序的复述：

> 简单来说就是创建好的了之后 在远端的这个sandbox需要执行这个sandbox的exec的操作
> 具体的含义是下面的一系列内容

## 尚不清楚

- 具体 shell 语法尚未逐项讨论；当前先建立这组命令的目的与结果。
- `E2BSandbox.exec` 怎样调用 SDK、处理结果和故障，仍作为下一层实现保留。
- 用户已表达创建后执行准备内容的顺序；协议与实际对象的对应、本地调用与远端执行的位置区别仍待进一步确认。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码同页首；配套定位：`swe.py:35、269–270`，`sandbox.py:28–59、160、309–340`。
- 局部验证从真实源码提取本函数，用替身记录 `exec` 调用，确认组合命令、一次调用、`user="root"`、`check=True`、`timeout=60` 和返回 `None`；没有执行 shell 或申请真实沙箱。
- [协议含义与语言依据](../../../../../../step-002-swe-evaluation/references/sandbox-entry.md#protocol-contract)保存《Fluent Python》的双语原文及本仓库的对应关系。
- 原始 Step 2：[名称与阅读层次](../../../../../../step-002-swe-evaluation/04-flow.md#module-function-exec-boundary) · [本次卡片与协议背景](../../../../../../step-002-swe-evaluation/04-flow.md#ensure-agent-user-card)。
- 本次复述与位置澄清：[创建完成后执行准备命令](../../../../../../step-002-swe-evaluation/04-flow.md#sandbox-ready-then-command)。
- 用户原话及记录边界见[当时的讨论](../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#sandbox-memory-entry-boundary)。

</details>

</details>
