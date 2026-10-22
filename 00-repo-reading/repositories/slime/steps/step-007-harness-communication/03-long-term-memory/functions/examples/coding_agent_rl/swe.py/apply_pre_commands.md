# apply_pre_commands

- 源码定位：[examples/coding_agent_rl/swe.py:214–224](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L214-L224)，由助手核对。
- 首次接触：Step 6 的 `prepare_workspace` 局部骨架；2026-10-22 经用户确认，首次单独展开。
- 最近认识更新：2026-10-22，用户在本函数讲解后反馈“大概明白了”，并尝试概括两个准备入口与下游的交接；远端命令执行和本地编排的区别在父卡中继续澄清，未据此认定全部内部细节已掌握。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`prepare_workspace` 已准备好用户与目录，发现 `md["grading"]["pre_commands"]` 非空，调用本函数执行题目指定的准备命令。后面的独立评测也复用它，使工作与评测从相应的代码基线开始。

2. **具体内容**：接收一段命令字符串或命令列表，整理为脚本文本；加上 `set -e`，写入远端 `/workspace/__cagent_pre__.sh`；再以 `agent` 身份进入 `workdir`，用 Bash 执行这个脚本。

3. **建议构建的心智模型**：

   > `apply_pre_commands` 把题目已经提供的准备命令整理成脚本，先保存到同一个沙箱，再进入代码工作目录执行。
   >
   > 返回值是 `None`；真正留下的是远端脚本以及命令对工作区产生的改变。函数本身不生成新的准备要求，也不返回命令执行结果。

4. **调用代码**（`prepare_workspace:191–193`）：

   ```python
   pre_commands = grading.get("pre_commands")
   if pre_commands:
       await apply_pre_commands(sb, workdir, pre_commands)
   ```

## 本场景的输入与输出

继续使用父卡中的真实题目 `auth0_auth0-python_pr671`，输入背景见 [md 说明](../../../../../../step-006-prepare-workspace/references/metadata.md)。命令来自[原始数据节选](../../../../../../step-006-prepare-workspace/references/scaleswe-auth0-example.json)，本页保留完整输入；只挑其中的切换版本动作解释用途，不逐项展开 Git 清理选项。没有运行远端命令。

**输入：已有沙箱、代码目录、该题目的准备命令。**

```python
# sb：已就绪的 E2BSandbox；agent 用户与工作目录归属已准备
workdir = "/workspace/auth0-python"
pre = md["grading"]["pre_commands"]  # 真实题目提供的一整段命令字符串
```

`pre` 包含清理工作区、切换版本、整理 Git 状态等操作，其中一个实际子命令是：

```bash
git checkout 5564a75cd2a85c0a919be6c17883e4c418a7960c -f
```

这条子命令让仓库回到题目指定的基础版本。它是完整命令串的一部分；本函数执行时不会只保留这一句。

**输出：返回 `None`，准备效果留在沙箱中。**

| 项目 | 本例对应的结果 |
| --- | --- |
| 远端脚本 | `/workspace/__cagent_pre__.sh` |
| 脚本内容 | `set -e` 加上换行整理后的完整准备命令；全文保留在折叠区 |
| 执行目录 | `/workspace/auth0-python`，与脚本存放位置不同 |
| 命令成功时的效果 | 工作区按题目要求清理，代码切到指定基础版本，并完成命令中的 Git 状态整理 |
| 函数返回值 | `None`；没有向上交付退出码或输出文本，不能仅凭返回就断言命令成功 |
| 回到调用方 | `prepare_workspace:194`，接着写入题目文件 `PROBLEM_STATEMENT.md` |

### 1. 命令字符串或列表 → 脚本文本（219–222）

```python
if isinstance(pre, str):
    body = pre.replace("\\n", "\n")
else:
    body = "\n".join(c for c in (pre or []) if c)
```

- **当前走字符串分支**：把输入中“反斜杠加 n”这两个字符替换为真正的换行。本例命令末尾就有这样一处标记。
- **列表是另一种输入形式**：保留非空条目，用换行连接成多行脚本文本；本例不走该分支。
- **此时仍是本地文字整理**：`body` 是 Python 字符串，尚未改动远端仓库，也没有根据题目另造命令。

### 2. 脚本文本 → 远端文件 → 工作区操作（223–224）

下面只调整源码排版；`_PRE` 的实际值是 `/workspace/__cagent_pre__.sh`。

```python
await sb.write_file(_PRE, "set -e\n" + body, user="agent")
await sb.exec(
    f"chmod 755 {_PRE} && cd {workdir} && bash {_PRE}",
    user="agent", check=False, timeout=600,
)
```

- **先保存脚本**：`write_file` 把内容写入远端文件，第一行是 `set -e`。这一步保存命令文字，尚未执行其中的 Git 操作。
- **再执行脚本**：`exec` 设置脚本权限，进入 `workdir`，再用 Bash 读取并执行脚本。`cd` 在这一行中，因此脚本虽存放在 `/workspace`，其中的命令却在 `/workspace/auth0-python` 生效。
- **身份和时间参数**：写入与执行都使用 `agent`；执行调用的 `timeout` 为 600 秒。
- **结果处理边界**：`check=False` 使 E2B 实现可将非零退出作为结果返回；本函数没有保存或检查该结果，随后正常返回 `None`。`set -e` 是脚本内部的执行选项，不能替代调用方检查结果；通信或文件操作仍可能抛出异常。

这里复用 [E2BSandbox 的操作接口](../../../../classes/slime/agent/sandbox.py/E2BSandbox.md)，本轮不继续展开 SDK。题目文件的写入属于返回后的父函数操作，不在这个辅助函数中。

## 我的直接表述（原话）

本次确认阅读：

> 好的再看一下这里的apply pre commands吧

随后反馈节选：

> 好的 我大概明白了

用户接着追问两个准备入口是否把 SWE 逻辑全部写入沙箱并交给下游，完整原话与澄清见 [prepare_workspace](prepare_workspace.md)。此前对共同用途的类比保留在 [apply_before_repo_set_cmd](apply_before_repo_set_cmd.md) 的原话中；本次反馈不扩大为逐项机制均已掌握。

## 尚不清楚

- 用户已反馈对讲解“大概明白了”；准备命令与完整 SWE 编排的区别在父卡中补充，尚待进一步反馈。
- 真实题目中各项 Git 清理选项、完整失败处理与 SDK 内部实现未逐项展开。
- 没有取得真实沙箱执行后的仓库状态；后续评测仍沿用原始数据参考中的适配限制。

<details>
<summary>来源、验证与完整例子</summary>

- Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：`_PRE` 见 `swe.py:57`，本函数见 214–224 行，工作沙箱的调用见 191–193 行，评测沙箱的调用见 274–275 行。`E2BSandbox.exec` 的结果处理见 `sandbox.py:309–340`。
- 数据集、固定版本、原始字段和映射范围见 [真实题目参考](../../../../../../step-006-prepare-workspace/references/scaleswe-auth0-example.md)。脚本完整内容如下；只把原始命令末尾的字面换行标记转换成换行，并按源码添加首行，没有删掉其他命令：

```bash
set -e
git clean -fd -e '*.egg-info' -e '.tox' -e '.venv' && git checkout 5564a75cd2a85c0a919be6c17883e4c418a7960c -f && git reset --hard HEAD && git checkout -b scaleswe && git config user.email 'scaleswe@example.com' && git config user.name 'scaleswe-engine' && rm -f .git/packed-refs && find .git/refs/heads -type f ! -name 'scaleswe' -delete && rm -rf .git/refs/tags .git/refs/remotes && git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

- 局部验证：从真实源码提取函数，用只记录调用的对象替代沙箱。核对真实字符串的换行转换、教学列表的非空条目连接、脚本完整内容、两次远端操作的参数；另令执行返回退出码 1，核对函数仍返回 `None`。所有命令仅作为字符串记录，没有实际执行 shell、启动沙箱或运行评测。
- 形成过程：[Step 6 · 准备命令怎样写入并执行](../../../../../../step-006-prepare-workspace/04-flow.md#apply-pre-commands-function-card)。
- 后续反馈：[Step 6 · 准备效果留在哪里，接下来读什么](../../../../../../step-006-prepare-workspace/04-flow.md#preparation-effects-and-sandbox-handoff)。

</details>
