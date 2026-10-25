# 一个真实题目：准备工作区与执行评测各用哪些资料

[回到 prepare_workspace](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) · [md 输入说明](metadata.md) · [原始字段节选](scaleswe-auth0-example.json)

**版本范围**：真实题目字段与来源继续保留；下文执行流程绑定原 `2f231865`，其中 `None` 返回和 `/workspace` 脚本路径属于旧版。当前 `18868a79` 的准备后快照、`baseline` 返回与 `/tmp` 脚本位置见上方父函数卡片。

## 1. 先看题目本身

例子来自公开数据集 [AweAI-Team/Scale-SWE](https://huggingface.co/datasets/AweAI-Team/Scale-SWE)，题目编号为 `auth0_auth0-python_pr671`。任务要求修复 `auth0-python` 的请求格式：按题目描述，PAR 请求应采用表单编码，携带 client secret。

| 这道题提供的字段 | 实际内容或含义 |
| --- | --- |
| `image_url` | `aweaiteam/scaleswe:auth0_auth0-python_pr671` |
| `workdir` | `/workspace/auth0-python` |
| `parent_commit` | `5564a75cd2a85c0a919be6c17883e4c418a7960c`，任务的基础版本 |
| `problem_statement` | 描述请求格式问题和期望行为的文字 |
| `pre_commands` | 清理工作区、切到上述版本并整理 Git 状态的命令 |
| `f2p_script` | Python 测试源码，检查请求头、请求体及不同类型的 client secret |

这里有三个不同的输入：**准备命令决定从哪个状态开始，题目文字告诉 Agent 要修什么，测试脚本检查修复后的行为。**

## 2. 它们怎样进入当前 Slime 代码

这份公开数据的字段在顶层；Slime 当前入口要求 `Sample.metadata`。下面是为讲解明确写出的字段映射，**不是在仓库中找到的现成数据转换程序**：

```python
# row 来自本页链接的 JSON 中的 row；字段值保留原文。
metadata = {
    "instance_id": row["instance_id"],
    "image": row["image_url"],
    "workdir": row["workdir"],
    "problem_statement": row["problem_statement"],
    "pre_commands": row["pre_commands"],
    "remote_env_info": {"f2p_script": row["f2p_script"]},
}
```

真实加载路径是：训练数据行中的 `metadata` → `Sample.metadata` → `get_metadata` → `_metadata_scaleswe` → `md["grading"]`。数据加载器和字段整理函数读取已有资料；它们不根据题目临时生成测试代码。

这次映射后，`grading` 中有 `pre_commands` 和 `f2p_script`；`swepro`、`eval_cmd` 都是 `None`。这道题不需要同时提供两种评测入口。

## 3. 当前 prepare_workspace 到底做什么

前提仍是已取得可操作的 `sb`，其中存在 `/workspace/auth0-python`。本次没有实际启动该镜像。

```text
已有 sb 和题目 md
  → ensure_agent_user：准备 agent 用户、目录归属与 Git 设置
  → swepro 为空：跳过 apply_before_repo_set_cmd
  → pre_commands 非空：在工作区执行题目提供的准备命令
  → 将 problem_statement 写入 PROBLEM_STATEMENT.md
  → 返回 None，generate 用同一个 sb 启动 Agent
```

实际 `pre_commands` 中包含这一句（从长命令中节选，未改写）：

```bash
git checkout 5564a75cd2a85c0a919be6c17883e4c418a7960c -f
```

它让 Agent 从题目指定的基础版本开始。完整命令还包含清理工作区、重置、分支和引用整理；原文在 JSON 节选中。`apply_pre_commands` 将命令保存为 `/workspace/__cagent_pre__.sh`，再通过 `sb.exec` 在 `workdir` 中执行。

随后写出的题目文件为：

```text
/workspace/auth0-python/PROBLEM_STATEMENT.md
```

其内容来自同一条数据的 `problem_statement`。到此，工作区和任务说明已交给后续 Agent；本函数没有执行测试、生成奖励，也没有把 `f2p_script` 写入工作沙箱。

## 4. f2p_script 和 eval_cmd 留到哪里用

**`f2p_script` 是测试代码的字符串。** 这道题的真实脚本包含以下断言（原脚本节选）：

```python
assert headers.get("Content-Type") == "application/x-www-form-urlencoded"
```

`f2p` 指 fail-to-pass：目标是修复前失败、修复后通过。这里说明测试意图，没有实际测得这道题修复前后的结果。

在 Agent 结束后，`_grade_scaleswe` 才会创建独立评测沙箱，重做准备并应用 Agent 的 diff。选择该分支时，`_run_f2p_script` 把脚本文本写到 `/workspace/__cagent_f2p__.py`，通过 Python 运行，再根据进程退出码形成分数。

**`eval_cmd` 则直接提供一条评测命令。** 它来自 `Sample.metadata["eval_cmd"]`，不是从 `f2p_script` 自动生成的。Slime 仓库自己的真实测试 fixture 在 `_base_sample` 中填写了 `"eval_cmd": "true"`；该用例使用假沙箱和假模型来检查整个流程，不能当成真实修复任务的评分标准。参见 [test_agent_rollout_cpu.py:96–105](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L96-L105)。

| 输入形式 | 后续消费者 | 执行方式 |
| --- | --- | --- |
| `metadata["eval_cmd"]`：命令字符串 | `_run_eval_cmd` | 在 `workdir` 中直接执行命令 |
| `metadata["remote_env_info"]["f2p_script"]`：Python 源码字符串 | `_run_f2p_script` | 先写成 `.py` 文件，再运行 Python |

当前协议优先选择 `swepro`，其次 `eval_cmd`，最后 `f2p_script`。两种字符串的最终来源都是调用方提供的题目数据；本例只演示有 `f2p_script` 的那条路径。

<details>
<summary>固定来源、字段接入与验证边界</summary>

- 数据集固定版本：`d8db20390a936bbda9c96d88b97cc4778dff1481`，文件 [processed_to_upload.jsonl](https://huggingface.co/datasets/AweAI-Team/Scale-SWE/blob/d8db20390a936bbda9c96d88b97cc4778dff1481/processed_to_upload.jsonl) 的第一条记录。2026-10-22 读取固定版本原文件首行，并与 Dataset Viewer 第 0 行逐字段核对一致；原始首行 SHA-256 为 `1461f0087da1a9edcea95d59f175f094e89c425a2f64f20b08cf3684d7593453`。本地 JSON 只保留上文涉及的七个字段，值未改写。
- Slime 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。加载器见 [data.py:230–274](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/data.py#L230-L274)；字段整理见 [swe.py:83–110](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L83-L110)；工作区准备见同文件 177–224 行，独立评测见 253–287 行，两种执行入口见 341–352 行。
- **原始数据不等于已经适配完成的 Slime 任务。** 本例显式补了字段布局；没有验证公开 Docker 镜像在当前 E2B 服务中的可用性。本函数示例以前一步已经交付 `sb` 为前提。
- **测试退出码还有一个实际缺口。** 此数据行的脚本末尾是 `pytest.main(["-v", __file__])`，没有将返回值交给进程退出码；当前 Slime 却根据进程退出码评分。若接入真实训练，必须另外处理，例如由适配后的入口使用 `sys.exit(pytest.main(...))`。本次保留原始脚本，未改写或运行它，也不声称已测得有效奖励。
- 局部核对只提取 Slime 的真实字段整理与准备函数，用记录调用的假沙箱检查传入字段、调用次序和写入内容。它验证了准备函数未写入或执行评测脚本；不验证 shell 命令、镜像启动和修复结果。
- 讨论来源：[Step 6 · 用真实题目补回准备函数的输入与输出](../04-flow.md#real-task-preparation-example)。

</details>
