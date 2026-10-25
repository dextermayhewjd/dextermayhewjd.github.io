> 2026-10-24 更新 Step 007 scope 前的完整快照。原稿绑定 `2f231865`，仅调整相对链接；原有返回值与行号保留其版本语境。当前范围见 [01-scope.md](../01-scope.md)。

---

# 01 · 阅读范围：准备任务工作区

[本步入口](../README.md) · [前一步任务总结](../../step-006-agent-sandbox/05-task-flow.md) · [前序记忆](../03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent / Coding RL 的目标。本步准备弄清：**沙箱和 CLI 已就绪后，`swe.prepare_workspace` 怎样整理现有工作目录，并放入 Agent 要读取的题目？**

继续使用 `scaleswe` 场景，先理解用户与目录准备、可选初始化、题目文件这三项交接。假定镜像中的 `workdir` 已存在；它如何进入镜像不在本轮展开。

## 2. 指挥官函数与本步入口

整体编排仍是 `examples/coding_agent_rl/generate.py::generate`（182 行）。本步从 [204 行的工作区准备调用](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L213)进入 [swe.py::prepare_workspace（177–198）](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L177-L198)。它串联工作区使用者、任务初始化与题目写入，作为本步局部入口。

源码固定为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。完整场景和输入输出见 [prepare_workspace 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 3 项

以下沿用 `evaluation=False` 正常路径的教学裁剪：省略参数、配置解析、前置检查、日志计时、超时异常和失败包装，暂不展开外层清理；保留实际顺序与上下文嵌套。

```python
state.adapter.open_session(...)                          # 1. 登记会话配置；Step 5
async with boot_agent_sandbox(...) as sb:                 # 2. 沙箱与 CLI 就绪；Step 6
    await swe.prepare_workspace(...)                     # 3. 本步：准备任务工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Agent；接回 Step 1
    diff_text = await swe.git_diff(...)                   # 5. 取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；Step 3
samples = await state.adapter.finish_session(...)        # 7. 导出训练样本；Step 4
...  # generate 检查空结果，并给每个样本补 agent_exit_code
return samples
```

<a id="prepare-workspace-local-skeleton"></a>

### 3.2 展开 prepare_workspace 的局部骨架

调用者传入的 `sb` 就是前一步 `as sb` 接到的对象；`workdir` 来自 `md["workdir"]`，`md` 沿用 Step 5 整理的题目信息，本步新增的字段关系见 [md 输入说明](metadata.md)。下面从 `swe.py:185–198` 裁剪，省略调用参数，保留决定执行内容的分支。

```python
await agent_sandbox.ensure_agent_user(...)               # 185：准备用户、目录归属与 Git 设置
if md.get("protocol") == PROTOCOL_SCALESWE:               # 186：此协议支持任务初始化配置
    grading = md.get("grading") or {}
    swepro = grading.get("swepro")
    if swepro:
        await apply_before_repo_set_cmd(...)             # 190：处理 swepro 的准备命令
    pre_commands = grading.get("pre_commands")
    if pre_commands:
        await apply_pre_commands(...)                    # 193：执行额外准备命令
await sb.write_file(...)                                 # 194–198：写入题目文件
```

本函数正常返回 `None`，准备效果留在同一沙箱中。随后回到 `generate.py:205`，由 `HARNESS_CLS().run` 组织 Agent 执行。

### 3.3 阅读导航与停止位置

用户已说明 `ensure_agent_user` 处理完毕，并进一步明确：先把 `md` 中的准备配置和题目说明读清楚，再依次读对应操作。输入模型覆盖本函数支持的两类准备配置；[auth0-python 真实题目](scaleswe-auth0-example.md)用于对照具体字段值，不因该题目没有 `swepro` 就略过另一入口的职责。

| 顺序与优先级 | 读哪里 | 本次要弄清什么，读到哪里停 |
| --- | --- | --- |
| 已处理：直接接续 | `swe.py:185` 的 [ensure_agent_user](../02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 保留“agent 用户、目录归属与 Git 设置已准备”的前提；有具体疑问时再回查 |
| 1 · 当前优先 | [md 输入说明](metadata.md)，必要时对照 `swe.py:77–110` | 先理解 `workdir`、`grading`、`swepro.before_repo_set_cmd`、`pre_commands` 与 `problem_statement` 的含义、来源和去向；`problem_statement` 与 `grading` 同级 |
| 2 · 对照输入回顾 | [apply_before_repo_set_cmd，201–211](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)，由父函数 190 行调用 | 接到 `swepro` 后取哪条命令、怎样写成脚本并执行；复用已有卡片，读完回到 191 行 |
| 3 · 展开准备命令 | [apply_pre_commands，214–224](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md)，由父函数 193 行调用 | 接到字符串或列表后，怎样整理、写入脚本、在工作目录执行；接清返回值和实际效果，保留 `check=False` 的边界后回到 194 行 |
| 4 · 接清题目写入 | `prepare_workspace:194–198` 的 `sb.write_file` 调用 | 先对应输入路径、题目字符串、`user="agent"` 与远端文件；需要展开实现时看 [E2BSandbox.write_file，342–377](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L342-L377) 的字符串路径，其他内容类型与重试机制按需后置 |
| 5 · 收拢本函数 | `prepare_workspace:177–198` → `generate.py:205` | 将准备命令和题目文字各自的去向串起来；函数返回 `None`，同一个 `sb` 交给 Harness。读通后再整理 task flow |

**两种配置与例子分别保留**：`apply_before_repo_set_cmd` 卡片中的命令是独立教学配置；真实 auth0-python 题目的 `swepro=None`，只触发 `pre_commands`。两份例子用于解释不同条件，不能拼成一次真实执行。实际源码先检查 `swepro`、再检查 `pre_commands`，两项有值时都可执行。

**当前后置**：`eval_cmd`、`f2p_script` 的内部执行，数据集完整加载链及 Sandbox SDK 的通信与重试细节。先看清 `md` 输入的内容和来源即可，不要求递归展开全部创建过程。

**停止位置**：能说明本函数接到的三个输入、三段处理、远端状态变化与后续接收方。按用户对真实例子的追问，父卡主例现用 [auth0-python 的真实题目字段](scaleswe-auth0-example.md)，展示准备命令、题目文字和评测脚本的不同去向；原空配置例子保留在折叠来源中。`apply_before_repo_set_cmd` 子卡继续保留另一条教学配置，不与本例混用。SDK 内部机制与后续 Agent 启动暂不深入，不因出现子调用就预建所有函数卡片。
