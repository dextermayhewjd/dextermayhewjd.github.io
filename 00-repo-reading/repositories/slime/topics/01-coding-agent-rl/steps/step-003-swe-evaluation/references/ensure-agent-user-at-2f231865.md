# ensure_agent_user

- 源码定位：[slime/agent/sandbox.py:390–399](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L390-L399)，由助手核对。
- 首次接触：Step 2，2026-10-21，从 `_grade_scaleswe` 中 `ev` 的第一次使用处进入。
- 最近认识更新：2026-10-21，用户已复述“沙箱创建后调用 exec 执行准备内容”的顺序；具体命令、协议关系与本地/远端运行位置仍在核对。

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

承接 [E2BSandbox.__aenter__](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) 的教学场景，假定镜像中的 `/workspace/repo` 已存在。以下环境变化按成功路径推导，未在真实远端执行。

**输入：已有沙箱对象与工作目录。**

```python
# ev：上一张卡片返回的 E2BSandbox 对象；传入后由形参 sb 引用。
workdir = "/workspace/repo"
```

<a id="sandbox-protocol"></a>

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
- [协议含义与语言依据](sandbox-entry.md#protocol-contract)保存《Fluent Python》的双语原文及本仓库的对应关系。
- 原始 Step 2：[名称与阅读层次](../04-flow.md#module-function-exec-boundary) · [本次卡片与协议背景](../04-flow.md#ensure-agent-user-card)。
- 本次复述与位置澄清：[创建完成后执行准备命令](../04-flow.md#sandbox-ready-then-command)。
- 用户原话及记录边界见[当时的讨论](../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#sandbox-memory-entry-boundary)。

</details>
