# 05 · 任务链路：把执行沙箱准备成题目工作区

> `prepare_workspace` 接住已有的沙箱、工作目录和题目资料，准备运行账号，按配置执行初始化，写入题目，再取得当前工作区的 Git 树标识。准备效果留在同一个沙箱，`baseline` 返回给调用方，供之后比较 Agent 的代码改动。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [本次收束](04-flow.md#prepare-workspace-step-closure) · [原占位记录](references/task-flow-before-summary.md)

## 1. 本步在整条任务中的位置

- Step 006 已交出安装好 CLI 的沙箱操作对象 `sb`。本步从 `_generate:285` 调用 `swe.prepare_workspace(sb, md["workdir"], md)` 进入。
- `sb` 提供执行命令和写文件的能力，`workdir` 指定现有代码目录，`md` 提供协议、准备命令及题目文字。
- 本页沿用 `scaleswe`、Sunabako / `proot` 场景，题目字段来自 auth0-python 例子。本例 `swepro=None`，`pre_commands` 有值；其他分支保留为对照，不混成同一次运行。

本步终点是 `baseline` 交回 `_generate`。后面的 `harness.run`、模型请求、补丁提取和独立评测只用于定位去向。

## 2. 已读部分怎样完成交接

图中缩进表示调用归属，条件决定是否执行。源码固定为 `18868a79`，省略多数实参与辅助包装。

```text
_generate:285 调用 prepare_workspace(sb, workdir, md)
└─ prepare_workspace [swe.py:187–209]
   ├─ 1. ensure_agent_user [195 → sandbox.py:409–420]
   │  └─ sb.exec：准备账号、按后端处理目录归属、配置 Git
   │     → 正常返回 None，继续使用原来的 sb
   ├─ 2. protocol == scaleswe 时读取准备配置 [196–203]
   │  ├─ swepro 有值 → apply_before_repo_set_cmd [200 → 212–222]
   │  │  → 读取指定命令、写 before.sh、执行；本例跳过
   │  └─ pre_commands 有值 → apply_pre_commands [203 → 225–235]
   │     → 整理文字、写 /tmp/__cagent_pre__.sh、在 workdir 执行
   ├─ 3. sb.write_file [204–208]
   │  → 以 agent 身份写入 workdir/PROBLEM_STATEMENT.md
   └─ 4. return await _repository_tree [209 → 241–262]
      → 组装临时索引与文件记录命令
      └─ sb.exec：执行整串 Git 命令，取得树标识
         → 检查标识形状，返回 tree 字符串
_generate:285 用 baseline 接住结果，仍持有同一个 sb
```

按节点回看：[父函数](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) · [账号与目录](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) · [swepro 准备命令](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md) · [pre_commands](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) · [快照与临时索引](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_repository_tree.md)。

两个准备条件独立：若都提供，会先执行 `swepro` 指定的命令，再执行 `pre_commands`。父函数的 Python 编排在 Slime 主机上运行，脚本和文件操作通过 `sb` 作用于执行环境。

## 3. 本步留下什么，交给谁

| 结果 | 所在位置与后续用途 |
| --- | --- |
| 账号、访问条件与 Git 设置 | 留在执行环境中，供后续以 agent 身份操作工作区 |
| 配置命令产生的准备效果 | 留在同一工作区；本例包括切到题目指定的基础代码状态 |
| `PROBLEM_STATEMENT.md` | 位于 `/workspace/auth0-python/`，供后续默认提示要求 Agent 读取 |
| `baseline` | 返回给 Slime 调用方的 Git 树标识，记录准备后、Agent 运行前参与比较的文件状态 |

`sb` 没有被换成新对象，`prepare_workspace` 返回的是树标识字符串。随后 `_generate:287` 把原来的 `sb` 交给 `harness.run`。

等待 `harness.run` 返回后，`git_diff:266` 再调用一次 `_repository_tree` 取得 `current`，比较两份状态生成补丁。`baseline` 和 `current` 保存各次快照的标识，工作区后来的变化不会自动改写旧树；`_run_turn` 没有按每轮生成这些快照的调用。这是后续用途，不是本步已经运行的动作。

## 4. 本步的收束与后续衔接

本轮正常主线已覆盖“接住 sb 与题目资料 → 按配置准备 → 放入题目 → 返回 baseline”，可以在这个边界收束。用户已对父函数、账号准备及配置初始化表达大致理解；关于 Git 操作、索引数量和调用时机的追问与澄清仍保存在记录中，不将本次收束扩大成全部机制已掌握。

继续保留的深入问题：

- Git 索引与对象的底层格式、复杂仓库及并发写入时的完整行为。
- 准备命令失败后的验收与恢复。当前可选命令使用 `check=False`，取得树标识不保证命令已达到题目要求。
- SDK 通信、真实部署及运行验证。取快照不会冻结后台活动，等待超时也不保证远端进程已经停止。

下一候选是回到 `_generate:287`，接续已有 **Step 008 的 `BaseHarness.run`**，看准备好的工作区怎样用于启动 CLI 和等待结果。本轮未开始 Step 008 的新版校准，也未改写其继承快照。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：[prepare_workspace:187–209](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)、[调用与后续交接:283–301](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L301)。
- [账号准备:409–420](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L409-L420)、[两种准备命令及快照:212–272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L212-L272)。
- [父函数反馈](04-flow.md#prepare-workspace-stage-two-comparison)、[配置初始化的理解](04-flow.md#before-repo-preparation-restatement)、[快照与调用次数澄清](04-flow.md#repository-tree-call-count)、[本次收束](04-flow.md#prepare-workspace-step-closure)。
- [Git 文件状态实验](references/repository-tree-example-18868a79.json)与[快照稳定性实验](references/repository-tree-snapshot-stability-18868a79.json)在隔离的本地仓库中完成；user=agent 只记录参数，没有切换系统账号或运行真实 Agent。本轮总结未追加运行。
- 完整旧函数卡片和 scope 保留各自版本；`03` 仍是原进入本步时的继承快照。总结串起当前记录，不回写旧版个人理解。

</details>
