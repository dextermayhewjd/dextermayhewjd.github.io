# md：先看清工作区准备要使用的题目资料

[本步阅读范围](../01-scope.md) · [prepare_workspace](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) · [Step 4 的 md 记录](../../step-005-agent-preparation/references/metadata.md)

**代码中的 `md` 是一个字典，由 `swe.get_metadata(base_sample, protocol)` 返回。** 本页是这个字典在 Step 6 的输入说明。它汇集一道题在不同阶段要使用的资料；先知道这些资料是什么，再读操作它们的函数。

## 1. 当前先建立这张字段地图

下面展示 `scaleswe` 分支的相关结构。说明文字不是字段值；`swepro` 可以为 `None`，其中的准备命令也可以缺失。

```text
md
├─ protocol                         使用哪种题目处理约定
├─ workdir                          在沙箱的哪个目录准备和工作
├─ grading                          准备与评测配置的分组
│  ├─ swepro                        SWE-bench Pro 相关配置，可为空
│  │  └─ before_repo_set_cmd         其中可选的准备命令
│  ├─ pre_commands                  另一项准备命令：字符串或字符串列表
│  ├─ eval_cmd                      后续评测使用的命令
│  └─ f2p_script                    后续评测使用的 Python 测试源码
└─ problem_statement                给 Agent 阅读的题目说明字符串
```

`problem_statement` 与 `grading` 同级。`grading` 不只用于评分，它也保存准备阶段要读取的配置；`swepro` 除准备命令外还可以带有其他评测资料。

完整 `md` 还有 `instance_id`、`image`、`looks_swebench` 等字段，分别服务于题目标识、沙箱创建和协议检查。本步已取得 `sb`，先聚焦上图中会影响工作区准备的资料。

<a id="grading"></a>

## 2. 每份输入对应哪项操作

| 要先理解的输入 | 它具体是什么 | 后面由谁使用 |
| --- | --- | --- |
| `protocol` | 本例为 `"scaleswe"` | `prepare_workspace:186` 决定是否进入可选初始化部分 |
| `workdir` | 远端代码工作目录，本例为 `/workspace/auth0-python` | 调用者作为第二个参数传入；准备命令在此工作，题目文件也写到这里 |
| `grading.swepro` | 一组可选配置，内部可以带 `before_repo_set_cmd` | 非空时进入 `apply_before_repo_set_cmd`，再取出其中的现成命令 |
| `grading.pre_commands` | 题目提供的准备命令，可能包含切换代码版本等操作 | 非空时进入 `apply_pre_commands`，整理、写入脚本并执行 |
| `problem_statement` | 问题描述、期望行为等文字，不是要执行的 shell 命令 | 最后的 `sb.write_file` 把它保存为 `PROBLEM_STATEMENT.md` |

两个准备入口是先后检查的独立条件，不是互斥选择；一份任务若两项都有值，就先处理 `swepro` 的准备命令，再处理 `pre_commands`。配置缺失时，跳过对应操作。

`eval_cmd` 和 `f2p_script` 在这一步只需要知道用途与去向：它们留给后续独立评测，不是当前准备函数要执行的内容。

`grading` 这一层由 `_metadata_scaleswe` 整理生成：从原始 `sample.metadata` 取得相关资料，再放入 `md["grading"]`。当前分支总会返回 `swepro`、`pre_commands`、`eval_cmd`、`f2p_script` 四个键，缺失资料的值可以是 `None`。字段来源和原有小例子保留在下方折叠区。

## 3. problem_statement 要说清楚什么

- **来源**：当前整理函数优先取 `base_sample.metadata["problem_statement"]`；没有有效内容时，再从 `base_sample.prompt` 提取题目文字。
- **含义**：这是“让 Agent 解决什么问题”的文字。刚才真实题目的中文概括是：修复 `auth0-python` 的 PAR 请求格式，使请求按要求使用表单编码并携带 client secret。中文是阅读辅助，实际写入的是原始题目字符串。
- **去向**：`prepare_workspace` 将其写入 `f"{workdir}/PROBLEM_STATEMENT.md"`，使用 `user="agent"`。本例对应 `/workspace/auth0-python/PROBLEM_STATEMENT.md`。
- **写入行为**：写的是文件内容，未执行这些文字，也未因此修复代码；后续 Agent 才会读取题目并开始工作。若传入 `md` 中该字段缺失或为空，当前写入调用使用空字符串。

因此，本步要同时接住两类内容：**准备命令告诉框架怎样安排工作区，题目说明告诉 Agent 要完成什么任务。**

## 4. 用已有例子读，保持各自的范围

- [真实 auth0-python 题目](scaleswe-auth0-example.md)有 `pre_commands`、`problem_statement` 和 `f2p_script`，映射后的 `swepro=None`。它适合观察“先切到指定代码状态，再放入题目说明”的关系。
- 另一条 `swepro.before_repo_set_cmd` 路径，继续对照已有的 [apply_before_repo_set_cmd 卡片](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)。卡片的命令是单独的教学配置，不是这条真实题目自带的数据。
- 真实样例缺少某字段，不等于可以省去整个函数对该字段的支持说明。先看全相关输入，再分别理解各条件下的处理；无需把两份例子伪装成同一次运行。

<details>
<summary>grading 的字段来源与原有小例子</summary>

此处合并原独立 grading 说明中的来源与示例。`m` 表示 `sample.metadata`，`rem` 表示其中的 `remote_env_info`；缺失时源码按空字典处理。

| grading 字段 | 原始来源 |
| --- | --- |
| `swepro` | `m.get("swepro")` |
| `pre_commands` | 优先取 `m.get("pre_commands")`；为空时取 `rem.get("pre_commands")` |
| `eval_cmd` | `m.get("eval_cmd")` |
| `f2p_script` | `rem.get("f2p_script")` |

原始资料经过 `get_metadata → _metadata_scaleswe` 整理为 `md`，其中的命令和测试文本来自输入，不由整理函数生成。

以下保留原来的教学构造，只观察字段如何整理；省略 SWE-bench Pro 的评测脚本与测试集合，不是完整可运行任务，也不是上面的真实 auth0-python 题目。

原始 `sample.metadata` 中的相关字段：

```python
metadata = {
    "swepro": {
        "before_repo_set_cmd": "mkdir -p .cache",
    },
    "pre_commands": ["mkdir -p .task-data"],
}
```

整理后的 `md["grading"]`：

```python
grading = {
    "swepro": {
        "before_repo_set_cmd": "mkdir -p .cache",
    },
    "eval_cmd": None,
    "f2p_script": None,
    "pre_commands": ["mkdir -p .task-data"],
}
```

- `before_repo_set_cmd` 属于 `swepro`，`pre_commands` 与 `swepro` 同级；两项准备配置可依次使用。
- 父函数卡片折叠区的旧例 `grading={}` 省略了空值；它和四个值均为空的配置都不会触发额外准备命令。
- 后续 `_grade_scaleswe` 在独立评测沙箱中重做相应准备、应用补丁，再按 `swepro → eval_cmd → f2p_script` 选择一个评测分支。准备配置可并用，评测分支按优先顺序选择。
- 另一种 `swebench` 协议使用 `sweb_instance` 结构；本页四字段结构只对应当前 `scaleswe` 分支。

</details>

<details>
<summary>源码与记录边界</summary>

- 固定源码提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- [get_metadata 与 _metadata_scaleswe，swe.py:77–110](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L77-L110)：`grading.swepro` 来自原始 metadata 的 `swepro`；`pre_commands` 优先取原始 metadata 的同名字段，再取 `remote_env_info` 的同名字段；题目说明优先取 metadata，再回退到 prompt。
- [prepare_workspace 与两个准备函数，swe.py:177–224](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L177-L224)：核对字段消费与实际顺序。`workdir` 是独立参数，调用者在 `generate.py:204` 传入 `md["workdir"]`。
- 评测字段的消费见 [_grade_scaleswe，swe.py:253–338](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L253-L338)；另一协议结构见同文件 113–137 行。
- 本页补充 Step 6 所需的输入模型，前序 Step 4 的记录保留原样。它是数据参考，不新建伪装成函数的卡片；本文解释尚待用户反馈。
- 真实数据的字段映射、镜像和评测适配边界沿用已有参考；本轮没有新增沙箱或评测运行。
- 合并前已做的局部验证：提取真实 `_metadata_scaleswe` 与 `_coerce_prompt`，核对教学示例、空配置四个 `None`、`remote_env_info` 回退和顶层 `pre_commands` 优先。该验证只涉及字段整理，没有运行 shell 或评测；本次文档合并不增加运行证据。
- 形成过程：[Step 6 · 先读完整输入，再读对应操作](../../step-007-prepare-workspace/04-flow.md#metadata-before-preparation-functions)。
- 原 grading 讨论：[Step 6 · 配置来源与结构](../../step-007-prepare-workspace/04-flow.md#grading-input-context)；本次合并：[统一 md 输入入口](../../step-007-prepare-workspace/04-flow.md#merge-grading-into-metadata)。

</details>
