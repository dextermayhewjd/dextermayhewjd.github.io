# git_diff

- 源码定位：[examples/coding_agent_rl/swe.py:265–272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L265-L272)，由助手核对。
- 首次接触：2026-10-23，Step 002 · 运行统计与补丁提取，首次单独展开。
- 最近认识更新：2026-10-23，用户已复述比较工作区内容变化，并将 `_repository_tree` 与 Git 联系起来；快照与提交记录的区别为本轮澄清，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前调用场景与源码整理，作为理解参考。

1. **使用场合**：`_generate` 已等待 CLI 结束并收集运行统计，执行沙箱仍可访问。现在要把 Agent 运行期间的工作区变化提取出来，交给后续独立评测。

2. **具体内容**：接收沙箱 `sb`、仓库路径 `workdir`、运行前的 Git 树标识 `baseline`；取得结束时的树标识 `current`，在沙箱中执行两份快照的 Git 比较。排除题目文件与 `.harness`，返回补丁字符串 `diff_text`。

3. **建议构建的心智模型**：

   > - 开始前的工作区状态已经用 `baseline` 保存；现在再给结束时的工作区取一份快照 `current`。
   > - 比较这两个状态，提取本次运行带来的改动，排除题目文件和运行记录目录。
   > - 把改动作为补丁文本返回；应用补丁、运行测试和计算奖励由后续评测完成。

4. **调用代码**（`generate.py:285–303`，省略 CLI 调用细节、统计收集和追踪包装）：

   ```python
   baseline = await swe.prepare_workspace(sb, md["workdir"], md)
   ...  # harness.run 执行 CLI，然后收集 agent_metrics
   diff_text = await swe.git_diff(sb, md["workdir"], baseline)
   ```

## 本场景的输入与输出

### 输入：执行沙箱、仓库路径和运行前快照

`sb` 是刚运行完 CLI 的沙箱操作对象。以下是教学场景；树标识和补丁来自本地真实 Git 验证，展示时将临时仓库路径写为 `/workspace/repo`。没有运行真实 Agent 或远端沙箱。

```python
workdir = "/workspace/repo"
baseline = "843995093bd53493edd1141a8eb6fdaab4ff9234"
```

`baseline` 是一个指向 Git 树对象的字符串，用来找到开始前保存的文件状态。它由 `prepare_workspace:209` 调用 `_repository_tree` 后返回，保存在调用方；不是完整文件内容，也不是本函数重新选择的 `HEAD`。

- `_repository_tree` 将当前工作区中纳入记录的文件状态保存成 Git 树，并返回标识；这份快照能找到目录、文件及其对应内容，不只是文件名清单。
- 这里比较的是两份快照的最终内容差异，不是逐条查看 `baseline` 之后的提交记录。Agent 没有执行 `git add` 或 `git commit`，已保存到工作区的改动也能被记录。Git 命令通过 `sb.exec` 在沙箱中的仓库执行。

运行前，`baseline` 对应的 `source.py`：

```python
# image setup
result = 0
```

CLI 结束后，当前工作区里的 `source.py`：

```python
# image setup
result = 42
```

`# image setup` 在准备阶段就已存在，不应作为本次 Agent 新增内容。

即使 CLI 只把 `result = 42` 保存进文件而没有提交，下面的补丁仍能包含这处改动。

### 输出：一份补丁字符串

本例内部取得：

```python
current = "93f569ad263d3cc61637dfa2ed87a5737ebc09b2"
```

`baseline` 和 `current` 是同一类标识。函数返回的 `diff_text` 则是以下文本，完整保留本地验证输出：

```diff
diff --git a/source.py b/source.py
index 7fe73d4..f130532 100644
--- a/source.py
+++ b/source.py
@@ -1,2 +1,2 @@
 # image setup
-result = 0
+result = 42
```

- `-` 标记旧行，`+` 标记新行；没有前缀改动标记的 `# image setup` 只是上下文。
- 本例还修改了 `PROBLEM_STATEMENT.md` 并写入 `.harness/compaction.json`，二者均未进入补丁。
- 没有需要输出的差异时返回空字符串 `""`。
- 快照辅助函数会生成 Git 对象，保留已有 `HEAD` 和真实索引；这里不修改业务文件、不提交改动，也不应用这份补丁。

### 函数内部：取快照 → 比较 → 返回

下面保留完整函数：

```python
async def git_diff(sb: Sandbox, workdir: str, baseline: str) -> str:
    current = await _repository_tree(sb, workdir)
    cmd = (
        f"cd {shlex.quote(workdir)} && git diff --binary {shlex.quote(baseline)} {shlex.quote(current)}"
        " -- . ':(top,exclude)PROBLEM_STATEMENT.md' ':(top,exclude).harness'"
    )
    _, out, _ = await sb.exec(cmd, user="agent", timeout=120, check=True)
    return out
```

- **266 行，取得结束时状态**：把 `sb` 和 `workdir` 交给 `_repository_tree`，接回 `current`。本轮先使用其接口：当前工作区 → Git 树标识，内部临时索引细节留待需要时展开。
- **267–270 行，构造比较命令**：进入仓库目录，按 `baseline → current` 的方向提取差异。`-- .` 指定当前目录范围，两个排除项过滤根目录下的题目文件与 `.harness`。`--binary` 让二进制文件的改动也能输出为 Git 可应用的补丁；返回值仍是字符串，本例只有文本改动。
- **271 行，在沙箱执行**：`sb.exec` 使用 `agent` 用户运行命令，超时为 120 秒并检查失败。返回的三项是退出码、标准输出、标准错误；这里只接住标准输出 `out`。
- **272 行，返回补丁**：`out` 直接交回调用方的 `diff_text`，不是一个补丁文件路径。`_generate:301–303` 随后把它作为 `diff_text=` 传给 `swe.run_evaluation`。

| 需要进一步展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [_repository_tree，241–262 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L241-L262)：当前文件怎样成为可比较的树对象 | 把返回标识作为 `current`，继续比较命令 |

`agent_metrics` 与 `diff_text` 是两份不同结果；本函数不读取压缩统计。执行失败或快照无效时异常向外传播，本函数没有自己的异常兜底。

## 我的直接表述（原话）

首次确认阅读入口：

> 好的
> 那么我们心在看一下这里的swe.git_diff的部分吧

2026-10-23，对工作区变化与 Git 记录的初步理解：

> 我可以简单理解为
> 这里需要通过swe来看一下workdir上两个git记录上到底变多或者变少了什么
> 可以这么理解吗？
> 虽然我没有具体看这里的repository_tree
> 但我的理解是这里做的事情是获得这里的这个repository tree 应该是和git相关的一个东西
> 获取一个类似于repository 到底有哪些内容
> 能够获取如果本地安装了一个git的话 当前本地的baseline 之后的提交区别之类的？
> 这是我的一系列理解

## 尚不清楚

- 用户已抓住比较内容变化的用途；“两份工作区快照的差异”与“基线之后的提交历史”的区别已由助手说明，尚待个人反馈。
- `_repository_tree` 怎样使用临时索引保存实际工作区、处理新文件和已暂存内容，尚未逐句阅读；本轮验证不等于已掌握其实现。
- 二进制文件、删除与重命名的详细补丁格式，以及后续怎样在评测沙箱应用，当前不展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本地源码 `/home/hongshi/projects/slime`。
- 本函数：`swe.py:265–272`；快照接口：241–262 行；运行前来源：`prepare_workspace:209`；调用与下游：`generate.py:285、298、301–303`。
- [完整局部验证](../../../../../references/git-diff-example-18868a79.json)：提取未改写的 `git_diff` 与 `_repository_tree`，在 `/tmp` 的独立 Git 仓库执行。覆盖无差异、文本改动、排除项、准备阶段已有修改不算本次改动、已暂存或已提交后仍提取同一补丁，并检查读取保留索引和 HEAD。
- 验证中的初始快照直接由 `_repository_tree` 取得，模拟 `prepare_workspace` 的返回；`sb` 替身只在本地执行 Bash，记录 `user="agent"` 但不切换本机用户。没有运行真实 Agent、远端沙箱或评测。
- 原仓库相关测试：`tests/test_agent/test_swe_workspace_diff.py`，本轮只阅读测试意图；不能把其中二进制补丁应用等断言记成本轮已执行。
- Git 语义依据：[git-diff](https://git-scm.com/docs/git-diff) 支持比较树对象，`--binary` 输出可应用的二进制补丁；[git-write-tree](https://git-scm.com/docs/git-write-tree) 从索引生成树对象并将标识写到标准输出。此处只借助文档确认接口，不要求本轮深入 Git 对象内部。
- [本轮形成过程](../../../../../04-flow.md#git-diff-first-read) · [回到本步 scope](../../../../../01-scope.md)。
- [快照与提交记录的澄清](../../../../../04-flow.md#git-diff-snapshots-not-commits)：保留本轮原话、源码依据与尚未确认的区别。

</details>
