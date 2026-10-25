# _repository_tree

- 源码定位：[examples/coding_agent_rl/swe.py:241–262](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L241-L262)。
- 首次接触：2026-10-23，Step 002 阅读 `git_diff` 时作为依赖定位；2026-10-24 在 Step 007 独立建卡。
- 最近认识更新：2026-10-24，用户概括为给当前内容额外做一份 Git 快照，同时明确表示仍不理解这些 Git 操作；快照职责与实现机制分开记录。

[返回 prepare_workspace 的 baseline 交接](prepare_workspace.md#prepare-workspace-baseline) · [另一调用方：git_diff](../../../../../../step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：工作区准备完成后，需要记下 Agent 开始修改之前的代码状态；调用方等待 `harness.run` 返回后，`git_diff` 还会复用本函数再取一次状态。
2. **具体内容**：在执行环境中使用临时 Git 索引，先载入 `HEAD`，再按路径名单记录工作区的当前内容，写成 Git 树，取回并检查树标识。
3. **建议构建的心智模型**：

   > 给工作区做一份可比较的 Git 快照：临时索引负责组织要记录的文件版本，原暂存区保持原样，最后交回快照的标识。

4. **调用代码**（`prepare_workspace:209`）：

   ```python
   return await _repository_tree(sb, workdir)
   # 外层 _generate:285 用 baseline 接住 prepare_workspace 的返回值。
   ```

## 本场景的输入与输出

输入是已有的沙箱操作对象 `sb` 和其中的 Git 仓库目录 `workdir`，仓库需要有可读取的 `HEAD`。为了看清三份状态的区别，本页使用独立的小型 Git 实验，展示路径写作 `/workspace/repo`；它与父卡的 auth0-python 题目分开，不把实验标识当成真实题目的结果。

Git 的索引（index）记录“路径对应哪份文件版本”，平常也是暂存区的依据。本例只展示同一个 `source.py`，完整实验文件见下方来源。

| 位置 | 调用前的 source.py 内容 |
| --- | --- |
| `HEAD` 指向的提交 | `result = 0` |
| 原暂存区 | `result = 1` |
| 工作区文件 | `result = 2` |

**返回值**是本地实验实际取得的 Git 树标识：

```python
tree = "ca43c1d572c91fd0a65fbccc2f3876240af68b0a"
```

这棵树记录工作区中的 `result = 2`；原暂存区仍是 `1`，`HEAD` 仍指向原提交。写入的 Git 对象留在仓库对象库中，临时索引等辅助文件在 Shell 退出时清理；业务文件没有被本函数改写。树标识对应[完整实验](../../../../../references/repository-tree-example-18868a79.json)，不只对应表格中的一个文件。

**下面前两段是源码拼出的 `cmd` 展开成 Shell 后的内容**，只把实验路径展示为 `/workspace/repo`。Python 先拼好这整串命令，到第 3 段的 `sb.exec` 才一次执行；不是分三次提交。Shell 中的动作发生在执行环境，Python 的调用与结果处理在 Slime 进程中。

<a id="repository-tree-temporary-index"></a>

### 1. 准备临时索引，以 HEAD 为起点（245–250）

```bash
set -e
cd /workspace/repo
agent_index=$(mktemp)
rm -f "$agent_index"
trap 'rm -f "$agent_index" "$agent_index.lock" "$agent_index.paths"' EXIT
export GIT_INDEX_FILE="$agent_index"
git read-tree HEAD
```

- `agent_index` 保存临时文件路径；先移除 `mktemp` 产生的空文件，让 Git 随后创建有效索引。`trap` 登记退出时清理索引、锁文件和路径名单。
- `GIT_INDEX_FILE` 让这次 Shell 中的 Git 命令使用临时索引，原暂存区不参与更新。
- `git read-tree HEAD` 先把原提交的文件状态装进临时索引。本例临时索引中的 `source.py` 此时是 `result = 0`，工作区文件仍是 `2`。

<a id="repository-tree-write-tree"></a>

### 2. 按工作区更新临时索引，再生成 Git 树（251–254）

```bash
git ls-files -z --cached --others --exclude-standard -- . \
  ':(top,exclude)PROBLEM_STATEMENT.md' \
  ':(top,exclude).harness' > "$agent_index.paths"
git update-index --add --remove -z --stdin < "$agent_index.paths"
git write-tree
```

- `git ls-files` 列出临时索引中的已跟踪路径，以及未被忽略的未跟踪路径，写进 `.paths` 名单；题目文件和 `.harness` 不参与这次路径更新。
- `git update-index` 按名单读取工作区当前内容；`--add` 纳入新增文件，`--remove` 处理已删除文件。`-z` 让路径以 NUL 分隔，与上一步对应。本例临时索引中的 `source.py` 变为 `result = 2`，原暂存区中的 `1` 不动。
- `git write-tree` 根据临时索引写出树对象，并把树标识打印到标准输出。它没有生成新的提交，也没有把 `HEAD` 移到别处。

<details>
<summary>文件筛选的一处边界</summary>

这里过滤的是“从工作区更新哪些路径”。如果题目文件原本已被 `HEAD` 跟踪，`read-tree HEAD` 装入的旧条目仍可能留在树中；不能说这棵树绝对不含题目文件。本轮实验中，工作区的题目文字已改为 `new prompt`，树里保留的仍是 `HEAD` 中的 `old prompt`。

未跟踪的忽略文件和 `.harness` 文件没有纳入实验中的新树。后续 `git_diff` 还会在比较时显式排除 `PROBLEM_STATEMENT.md` 与 `.harness`，两层作用需要分清。

</details>

<a id="repository-tree-return"></a>

### 3. 一次执行命令，取回并检查树标识（258–262）

```python
_, out, _ = await sb.exec(cmd, user="agent", timeout=600, check=True)
tree = out.strip()
if len(tree) not in (40, 64) or any(c not in "0123456789abcdef" for c in tree):
    raise RuntimeError(f"Invalid repository snapshot: {tree!r}")
return tree
```

- `sb.exec` 执行前两段组成的完整命令，使用 `agent` 身份，超时参数为 600 秒，并检查命令失败。三项结果里只接住标准输出 `out`。
- `out` 是树标识加换行；`strip()` 去掉两端空白。随后检查长度为 40 或 64，且只含小写十六进制字符；这一步检查标识的形状。
- 返回到 `prepare_workspace`，再由它交给 `_generate` 的 `baseline`。同一函数在 `git_diff:266` 返回时叫 `current`，区别来自调用时机：前者在调用 `harness.run` 前取得，后者在该调用返回后取得。

`baseline` 和 `current` 各自保存一次快照的标识。工作区文件后来可以改变，已经取得的树标识和它对应的旧内容不会跟着更新；`current` 也不是 `_run_turn` 中维护的实时状态。

<details>
<summary>调用次数、索引数量与 run_turn 的关系</summary>

- 一次调用只新建一份临时索引，使用完后清理；本例仓库原有的索引保持原样。`baseline` 和 `current` 保存的是树标识，不是两份长期保留的索引。
- 一次调用返回一个根树标识。当前框架在准备完成后和 `harness.run` 返回后各调用一次；若两次记录的内容相同，两个标识也可能相同。这个数量不代表 Git 对象库里只有一棵或两棵树。
- 当前路径为：准备并保存 `baseline` → 等待 `harness.run` → 收集统计 → `git_diff` 取得 `current` 并比较。CLI 在运行期间发出模型请求，由 Adapter 的 `_run_turn` 处理；CLI 的工具操作可以继续修改工作区。
- `current` 是 `git_diff` 的局部变量，仅在 `swe.py:266` 赋值一次。`_run_turn` 更新会话、提示前缀和轨迹记录，不引用此变量。取快照以后若文件继续变动，也不会改写已取得的旧树。
- 取快照不会冻结文件系统。`_await_done_marker` 在等待超时后可返回超时码，这段等待路径没有同时停止远端进程；`shutdown_session` 也在后面的 `finish_session` 中才调用。因此不能把 `harness.run` 的所有返回情况都解释为所有后台任务已经停止。
- 本轮[快照稳定性实验](../../../../../references/repository-tree-snapshot-stability-18868a79.json)在第一次取树后修改文件，验证旧树内容保持原样、再次取树反映新内容。实验没有运行真实 CLI、`_run_turn` 或并发写入。

调用位置见 [generate.py:283–330](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L330)，等待边界见 [sandbox.py:79–162](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L79-L162)，请求处理见 [BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L387-L475)。

</details>

读完回到[父函数的第 4 段](prepare_workspace.md#prepare-workspace-baseline)，接清准备效果留在环境、树标识交回调用方这两种结果。

## 我的直接表述（原话）

2026-10-24，阅读新卡后的反馈：

> 这里怎么感觉就只是吧当前的部分额外做一份git快照
> 目前其实我不是特别理解这里到底在做什么了的感觉?
> 应为这里都是git的操作

本轮先在聊天中接清快照与后续补丁比较的关系，讲解主体保持不变；[问题与解释](../../../../../04-flow.md#repository-tree-purpose-gap)记录在本步过程文件。

随后引用助手的三步流程并追问（此处仅摘录用户的问题，不把引用内容记为用户复述）：

> 这个是在这个函数里面做的事情吗?
> 还是这一部分而只是为了生成一个baseline呢?
>
> 这个baseline 之后还会改变吗?

单次快照调用与整个比较流程的区别、`baseline` 在当前任务中的稳定性，见[职责范围澄清](../../../../../04-flow.md#repository-tree-call-boundary)。

继续追问 `current` 与请求处理的关系：

> 你确定吗 请全面的看一下当前的slime中到底这个current 之后难道不会在run turn的过程中发生变化吗?
> 还是说并不会有这些事情呢?

本次调用链核对与后台活动边界见[运行时机核对](../../../../../04-flow.md#snapshot-current-run-turn-audit)。

随后询问调用与对象数量：

> 回答我几个问题
> 1. 当前这里只有一个repository tree对吗?
> 2. 这里的内容是只有一个两个索引吗?
> 我不是特别理解
>
> 之后在run turn的过程中会自行生成不同阶段的tree吗?
> 还是说并不会呢?

一次调用的临时索引、返回的根树标识与整条流程的两处快照调用，见[数量关系澄清](../../../../../04-flow.md#repository-tree-call-count)。

2026-10-23，在 Step 002 讨论 `git_diff` 时的相关节选：

> 虽然我没有具体看这里的repository_tree
> 但我的理解是这里做的事情是获得这里的这个repository tree 应该是和git相关的一个东西
> 获取一个类似于repository 到底有哪些内容

[完整原话](../../../../../../step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)还包含对提交历史的疑问，继续保留原有边界。2026-10-24 用户确认独立建卡，尚无对本轮临时索引机制的复述，见[本次范围确认](../../../../../04-flow.md#repository-tree-function-card)。

## 尚不清楚

- 用户明确表示仍不理解这里的 Git 操作；已识别“额外做快照”的职责，临时索引、树标识与比较用途的具体联系仍需继续建立。Git 内部格式与对象回收暂不展开。
- 真实 SDK 传输、大仓库开销、并发文件修改及特殊 Git 配置的完整行为未验证。

<details>
<summary>完整 Python 源码、来源与验证</summary>

以下为固定提交 `18868a79` 的完整函数；前面两段 Shell 就来自其中的 `cmd`。

```python
async def _repository_tree(sb: Sandbox, workdir: str) -> str:
    # Images can contain modified tracked files and untracked build artifacts.
    # Snapshot the actual workspace with a temporary index, preserving HEAD and
    # the agent's real index. This also captures staged edits and new files.
    cmd = (
        f"set -e\ncd {shlex.quote(workdir)}\n"
        'agent_index=$(mktemp)\nrm -f "$agent_index"\n'
        'trap \'rm -f "$agent_index" "$agent_index.lock" "$agent_index.paths"\' EXIT\n'
        'export GIT_INDEX_FILE="$agent_index"\n'
        "git read-tree HEAD\n"
        "git ls-files -z --cached --others --exclude-standard -- . "
        "':(top,exclude)PROBLEM_STATEMENT.md' ':(top,exclude).harness' > \"$agent_index.paths\"\n"
        'git update-index --add --remove -z --stdin < "$agent_index.paths"\n'
        "git write-tree"
    )
    # Large repositories may need several minutes to hash their initial tree
    # under concurrent sandbox load. The whole-rollout deadline still applies.
    _, out, _ = await sb.exec(cmd, user="agent", timeout=600, check=True)
    tree = out.strip()
    if len(tree) not in (40, 64) or any(c not in "0123456789abcdef" for c in tree):
        raise RuntimeError(f"Invalid repository snapshot: {tree!r}")
    return tree
```

- 本轮[独立实验记录](../../../../../references/repository-tree-example-18868a79.json)使用原样提取的函数，以本地 Bash/Git 执行器替代 `sb`。核对工作区版本、新文件、删除、忽略项、被排除的已跟踪条目，以及原索引、`HEAD` 和业务文件的保留。
- 实验只在 `/tmp` 的独立仓库运行，`user="agent"` 仅记录参数，没有切换系统用户，也没有调用真实沙箱、Agent 或评测。临时仓库已清理；此处的运行证据不代表用户已经理解全部实现。
- Step 002 的[历史验证](../../../../../../step-002-agent-results/references/git-diff-example-18868a79.json)继续保留其场景与标识，不能与本页实验混成一次运行。
- [本轮形成过程](../../../../../04-flow.md#repository-tree-function-card)。

</details>
