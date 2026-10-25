# prepare_workspace

- 源码定位：[examples/coding_agent_rl/swe.py:187–209](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)。
- 首次接触：Step 5 总结中定位为下一处；Step 6，2026-10-22 开始函数记录，旧编号保留历史语境。
- 最近认识更新：2026-10-24，用户反馈“差不多理解了”，并追问第二部分相对旧版的变化；这是整体理解反馈，内部机制未逐项确认。原 2026-10-22 表述继续保留。
- 本轮源码校准：2026-10-24，接入当前后端、脚本位置、题目写入和 `baseline` 返回；[旧版完整卡片](../../../../../references/prepare-workspace-at-2f231865.md)保留，版本校准不改变认识日期。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_generate` 已从 `boot_agent_sandbox` 取得就绪的 `sb`，接下来让 Agent 在本题工作区中运行。
2. **具体内容**：准备运行账号与 Git 设置，按题目配置执行可选初始化，写入题目说明，再取得当前工作区的 Git 树标识。
3. **建议构建的心智模型**：

   > 把已有沙箱布置成这道题的工作区，再记下 Agent 动手前的代码状态。准备效果留在沙箱，比较基准 `baseline` 交回调用方。

4. **调用代码**（`_generate:285`，省略周围追踪包装）：

   ```python
   baseline = await swe.prepare_workspace(sb, md["workdir"], md)
   # 随后把同一个 sb 交给 harness.run；运行结束后 git_diff 使用 baseline。
   ```

## 本场景的输入与输出

继续使用 [auth0-python 真实题目的字段](../../../../../references/scaleswe-auth0-example.json)，问题是修复 PAR 请求格式。`row` 指该 JSON 中的 `row`。这里只列本函数需要的字段；[原题目与旧版映射说明](../../../../../references/scaleswe-auth0-example.md)保留完整来源。

- **`sb`**：Step 006 已准备好的 Sunabako 操作对象，本例沿用默认 `proot`。假定所需代码仓库已在执行环境中；没有实际启动该题目镜像。
- **`workdir`**：下面的 `md["workdir"]`，指定本题代码目录。
- **`md`**：提供协议、准备配置与题目文字。此处的命令和题目直接取自原始字段，不另造一套任务。

```python
md = {
    "protocol": "scaleswe",
    "workdir": "/workspace/auth0-python",
    "grading": {
        "swepro": None,
        "pre_commands": row["pre_commands"],
    },
    "problem_statement": row["problem_statement"],
}
```

**正常交接的结果**：本函数返回 `baseline` 字符串；可选命令产生的变化和 `PROBLEM_STATEMENT.md` 留在同一个工作区。`baseline` 是 Git 树标识，本轮没有取得这道真实题目的具体标识值。下面先按准备命令成功的场景阅读，失败边界单独保留。

<a id="prepare-workspace-user"></a>

### 1. 准备工作区的使用者（195）

```python
await agent_sandbox.ensure_agent_user(sb, workdir)
```

继续使用原来的 `sb` 和 `workdir`，准备 `agent` 账号与 Git 安全目录设置。目录归属处理取决于后端；本例 Sunabako / `proot` 会跳过递归 `chown`。这一步不创建缺失的题目代码仓库。

需要回顾时看本步 [ensure_agent_user 卡片](../../../slime/agent/sandbox.py/ensure_agent_user.md)，已接入当前执行沙箱的后端条件与命令预算，原认识保留。返回后继续 `196` 行的题目配置。

<a id="prepare-workspace-commands"></a>

### 2. 按这道题的配置整理工作区（196–203）

```python
if md.get("protocol") == PROTOCOL_SCALESWE:
    grading = md.get("grading") or {}
    swepro = grading.get("swepro")
    if swepro:
        await apply_before_repo_set_cmd(sb, workdir, swepro)
    pre_commands = grading.get("pre_commands")
    if pre_commands:
        await apply_pre_commands(sb, workdir, pre_commands)
```

**跟住本例**：`swepro=None`，跳过第一项；`pre_commands` 非空，进入第二项。原命令包含 `git checkout 5564a75cd2a85c0a919be6c17883e4c418a7960c -f`，用于切到题目指定的基础版本。完整清理与 Git 命令仍见原始字段，本页不逐个展开。

两项条件独立检查；如果都提供，就先处理 `swepro`，再处理 `pre_commands`。准备命令在执行环境中运行，选择分支和组织调用的 Python 代码仍在 Slime 主机上。

按需进入 [apply_before_repo_set_cmd](apply_before_repo_set_cmd.md) 后回到 `201`；进入 [apply_pre_commands](apply_pre_commands.md) 后回到 `204`。两张卡片已校准当前定位，独立教学例子与原话保留。**当前 `pre_commands` 脚本路径为 `/tmp/__cagent_pre__.sh`**；函数体与旧版相同，但 `_PRE` 常量已改变。

第二段的条件判断、调用顺序和两个辅助函数体均未改变。移动的是脚本文件的存放位置，命令执行目录仍是 `workdir`。源码注释给出的原因是 `/workspace` 在某些后端可能归 root 所有，而脚本由 `agent` 写入；新版使用各沙箱自己的 `/tmp`。父函数新增的 `baseline` 返回在第 4 段，和这里的准备分派分别理解。

<details>
<summary>配置字段与准备失败的边界</summary>

- 非 `scaleswe` 协议跳过这一段，仍进行账号准备、题目写入和快照返回。
- `eval_cmd` 与 `f2p_script` 不被本函数读取，留给后续独立评测；放在同一份 `grading` 中不表示要同时执行。
- 两个可选准备入口的最终命令使用 `check=False`，父函数没有验收其退出码。因此正常返回并不保证这些命令已经达到预期效果；后面的快照也可能记录了非预期的工作区状态。

</details>

<a id="prepare-workspace-problem-file"></a>

### 3. 把题目文字放进工作区（204–208）

```python
await sb.write_file(
    f"{workdir}/PROBLEM_STATEMENT.md",
    md.get("problem_statement") or "",
    user="agent",
)
```

本例写入 `/workspace/auth0-python/PROBLEM_STATEMENT.md`，内容是原题目的问题描述。这里交给 `write_file` 的是字符串；此前安装 CLI 时传的是本机包文件的 `Path`。

写入使用 `agent` 身份。后续默认 `SWE_PROMPT` 要求 Agent 读取这个文件再解决问题；本次写入只放好说明，尚未运行 Agent。写完继续到最后一行。

<a id="prepare-workspace-baseline"></a>

### 4. 记下准备后的代码状态，交回 baseline（209）

```python
return await _repository_tree(sb, workdir)
```

`_repository_tree` 记录当前工作区中纳入比较的文件状态，返回 Git 树标识。**取基准的时间是准备完成之后、Agent 运行之前**，所以准备阶段已有的改动属于起点，后续比较关注 Agent 运行期间的变化。

返回 `_generate:285` 后，调用方用 `baseline` 接住字符串；原来的 `sb` 继续交给 `harness.run`。运行结束后，`_generate:298` 把同一个 `baseline` 传给 `git_diff`，与结束时的状态比较。

此处复用 [Step 002 对 baseline 与 current 的说明](../../../../../../step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)。本轮已确认下钻 [_repository_tree 卡片](_repository_tree.md)，沿临时索引、文件状态和树标识阅读，读完返回这里继续交回 `baseline`。

<details>
<summary>快照的内容与返回边界</summary>

当前路径名单不更新根目录的 `PROBLEM_STATEMENT.md` 和 `.harness`；如果它们已在 `HEAD` 中，旧条目仍可能留在树里，后续比较还会显式排除其差异。快照不要求 Agent 先生成 Git 提交；返回的是标识字符串，不是补丁文本。

快照调用检查自身命令执行结果与标识形状，但不验收前面的可选初始化是否符合题意。具体实现见 [_repository_tree:241–262](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L241-L262)。

</details>

<details>
<summary>四段分别变了什么，回顾时重点看哪里</summary>

| 部分 | `2f231865` → `18868a79` 的变化 |
| --- | --- |
| 1. 用户与目录准备 | 父函数的调用不变；`ensure_agent_user` 增加后端条件，按需跳过递归 `chown`，并改进路径引用及命令预算 |
| 2. 按配置执行准备命令 | 分支、顺序和两个辅助函数体不变；`pre_commands` 脚本的运行时路径由 `/workspace` 改为 `/tmp`，执行目录仍是 `workdir` |
| 3. 写入题目文件 | 调用及其参数不变，仍把题目字符串写入 `PROBLEM_STATEMENT.md` |
| 4. 返回初始状态 | 新增 `_repository_tree` 调用，返回 `baseline` 字符串供后续比较；旧版返回 `None` |

这里的路径变化指脚本在沙箱内的保存位置，源码文件仍在 `swe.py`。阅读时可复用第 2、3 段的已有理解，第 1 段只补后端差异，第 4 段重点接清返回值与后续比较；这不是要求重新读完全部辅助函数。

</details>

## 我的直接表述（原话）

2026-10-24，本轮讲解后的反馈与追问：

> 我觉得我差不多理解了
> 这里相比之前有什么变化吗 我时说这里第二prepare workspace的部分

第二段的版本对比与整个函数返回值的区别见[本轮核对](../../../../../04-flow.md#prepare-workspace-stage-two-comparison)。这是对整体内容的反馈，不据此认定所有分支和 SDK 机制已掌握；[本次展开](../../../../../04-flow.md#prepare-workspace-card-18868a79)保留最初范围。

随后对改动范围的确认与追问：

> 也就是说这里相对应的代码模块除了位置 内容没有改变对吗?
> 那么如果没有改变的话我觉得应该每一个部分差别大?

各段差异与回顾重点见[后续澄清](../../../../../04-flow.md#prepare-workspace-change-scope)。这次追问不作为所有部分均未变化或已掌握的确认。

<details>
<summary>2026-10-22 的原始表述与澄清</summary>

本轮确认阅读对象：

> 好的那么现在是否适合展开了呢？
> 也就是开始处理这里的swe.prepare_workspace吧

后续反馈与本次问题：

> 这里的eval cmd和f2p script是哪里来的呢？
> 我不是特别理解
> 主要是是否能够哪一个真实的例子
> 否则我梳理不清楚这里到底在做什么
> 感觉这里的这个prepare workspace function 我根本不清楚到底是在做什么

两个准备入口讲解后的反馈：

> 好的 我大概明白了
> 那么按照当前的这两个步骤的话都解决了的话
> 那么目前应该看哪一块呢？
> 我可以理解为这里其实就是把swe的一系列逻辑全部写到这里的agent sandbox里面了
> 然后吧这样子sandbox将给下面呢？

用户已反馈对前述讲解“大概明白了”，并尝试连接下游。上文“题目提供的命令在远端执行、Python 编排仍在本地、调用方继续使用同一个 `sb`”是本次助手补充的澄清，不记为用户已逐项确认。

</details>

## 尚不清楚

- 用户已反馈整体差不多理解；第二段的版本差异与具体分支、失败行为尚未逐项确认。
- `_repository_tree` 的临时索引已在独立卡片展开，理解尚待反馈；Git 底层存储、SDK 文件传输与准备失败的完整处理未深入，另一条 `swepro` 真实题目配置尚未选例。
- 本例没有真实沙箱运行结果；原数据的镜像接入、评测脚本退出码与部署适配仍保留原未知，字段映射不表示已经跑通评测。

<details>
<summary>源码、历史与验证范围</summary>

- 当前固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：[完整父函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)、[调用与后续使用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298)。
- [路径常量与默认提示](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L60-L74)、[两种准备入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L212-L235)。函数体 AST 未变不代表其引用的常量也未变。
- [旧版完整卡片](../../../../../references/prepare-workspace-at-2f231865.md)保存原 E2B 场景、完整字段映射、空配置例子和旧版 `None` 返回。数据参考保留原版本，本轮当前接口以上述固定源码为准。
- 原题目来自固定数据集版本 `d8db20390a936bbda9c96d88b97cc4778dff1481` 的[原始字段节选](../../../../../references/scaleswe-auth0-example.json)。本轮沿用字段，不宣称该镜像名已接入 Sunabako，也没有执行其中的命令或测试。
- 本轮静态核对父函数及调用关系；历史替身与本地 Git 验证保留在原卡和 Step 002，不算本轮新增的远端运行。
- [本次展开与版本校准](../../../../../04-flow.md#prepare-workspace-card-18868a79)。

</details>
