# 04 · 问题与解释

<a id="prepare-workspace-entry"></a>

## 1. 2026-10-22：从已就绪的沙箱进入工作区准备

前一步用户表示已基本完成对 `boot_agent_sandbox` 的理解，Step 5 已按原范围总结准备、交付、使用与回收。`swe.prepare_workspace` 当时只作为下一处交接定位，尚未开始新一步。

本轮用户明确要求继续：

> 好的那么现在是否适合展开了呢？
> 也就是开始处理这里的swe.prepare_workspace吧

据此建立 Step 6。范围是 `generate.py:204 → swe.py::prepare_workspace:177–198`，围绕“已有沙箱与题目信息，怎样成为供 Agent 使用的任务工作区”展开。新 `03` 完整合并 Step 5 的 `03 + 02`，共 35 份记录；旧步骤保持原样。

### 本轮给出的观察材料

沿用 `image="example-image"`、`instance_id="issue-123"`、`workdir="/workspace/repo"` 的教学背景。`sb` 是前一步交出的对象；`md` 补入题目字符串和空的 `grading`，先走不含额外初始化命令的路径。

1. `ensure_agent_user(sb, workdir)` 准备使用者、已有目录的归属和 Git 设置，复用先前的函数记录。
2. `protocol == "scaleswe"` 时，按 `grading` 检查两个可选入口；本例 `grading` 为空，两项都跳过。父函数保留真实分支，暂不为辅助函数逐个建卡。
3. `sb.write_file` 将 `md["problem_statement"]` 的内容写到远端工作目录的 `PROBLEM_STATEMENT.md`，使用 `agent` 身份。
4. 正常返回 `None`，调用方在 `generate.py:205` 继续将原来的 `sb` 交给 Harness。默认任务提示会要求 Agent 读取题目文件。

本轮的关键区别是：安装 CLI 时 `write_file` 接到本机包文件的 `Path`，这里接到题目字符串；两者都将内容写入远端，但内容来源不同。

### 证据与停止位置

- 固定源码为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，核对 `generate.py:203–205`、`swe.py:61–67、177–224` 与 `sandbox.py:390–399`。
- 本机 `swe.py` 已有评测分支的一处空白字符差异，未影响本轮函数，也未在本次修改源码。
- 先建立三个输入、三段处理、输出文件及返回位置的模型；可选命令的具体内容、SDK 实现与 Agent 启动不在本轮深入。
- 用户尚未直接复述本函数机制。函数卡片中的场景和模型是助手说明；本轮未执行真实沙箱、脚本或 Agent，也未将本步标记为完成。

记录入口：[prepare_workspace 短期记忆](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)。

<a id="ensure-agent-user-entry"></a>

## 2. 2026-10-22：从工作区准备进入 ensure_agent_user

用户指定先展开这一处：

> 那么这里是否应该先考虑展开一下这里的agent_sandbox中的ensure_agent_user呢？

沿用 Step 6 范围，从 `prepare_workspace:185` 进入 `sandbox.py:390–399`。原 Step 2 已在评测沙箱 `ev` 的场景读过本函数；本次接住的是 `boot_agent_sandbox` 交出的执行沙箱 `sb`。两处复用同一实现，操作的是各自传入的环境。

### 本轮解释的对应关系

1. `agent_sandbox` 是模块别名，`sb` 是已有的沙箱对象，命令里的 `agent` 是 Linux 用户名。
2. 后续题目写入会指定 `user="agent"`；因此先通过一次 `sb.exec` 以 `root` 身份检查或创建账号，再设置 `/home/agent` 与 `workdir` 的归属，并配置 Git 可信目录。
3. 用户原先存在时，只跳过创建账号；后面的目录和 Git 准备仍继续执行。`chown` 修改已有目录的归属，工作目录应已存在。
4. Python 在本地调用，shell 命令在远端沙箱中执行。当前函数忽略 `exec` 的结果元组，正常返回 `None`；准备效果留在同一个远端环境中。
5. 读完返回 `prepare_workspace:186` 查看任务配置，之后才到题目文件写入。本轮未继续展开初始化子函数或 SDK 内部机制。

### 记录与证据边界

- 在当前 `02` 建立 [ensure_agent_user 卡片](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)，保存原先的首次接触、用户原话、未解问题和来源，并补入当前场景。
- 当前 `03` 与旧步骤保持原样；scope 和父函数卡片改为指向本次展开的位置。
- 核对固定源码 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `swe.py:35、185–198` 与 `sandbox.py:309–340、390–399`。命令连接和 Git 配置的文档依据收在卡片来源中。
- 本轮是静态源码与文档核对，没有运行远端命令或新增运行实验；Step 2 的替身验证保留原归属。用户尚无本轮机制复述，不据此将 Step 6 标为完成。

<a id="ensure-agent-user-restatement"></a>

## 3. 2026-10-22：已有沙箱中的运行准备

用户随后复述：

> 简单来说就是
> 1.确保这里folder的
> 2.配置好一系列需要的部分git
> 3.创建权限
>
> 在已经拿到的稳定连接sandbox中执行这些操作 为了后续能够正常运行

本次已将“已有沙箱 → 环境准备 → 后续运行”联系起来。助手根据 `sandbox.py:390–399` 补充三个对应关系：

1. 先确保 Linux 用户 `agent` 存在；不存在时创建账号。
2. 设置 `/home/agent` 与已有 `workdir` 的属主、属组。工作目录进入这里前应已存在；此处的 `chown` 负责调整归属。
3. 配置 Git 可信目录。整组准备通过 `sb.exec` 以 `root` 执行，为后续使用 `agent` 身份的操作提供条件。

“稳定连接”在当前层次先理解为已取得可操作远端沙箱的本地 `sb` 对象，具体网络连接的建立和复用尚未展开。函数正常返回 `None`，准备效果留在远端环境中；读完仍回到 `prepare_workspace:186` 查看任务配置。

本轮只保存职责层面的复述与源码校正；账号/目录归属的细分解释尚待反馈，没有新增运行实验，也没有结束 Step 6。卡片的场景、代码与完整输入输出沿用上一轮，只补原话、认识状态及来源。

<a id="workspace-initialization-next"></a>

## 4. 2026-10-22：继续查看任务初始化配置

收到账号、目录归属与 `sb` 操作入口的澄清后，用户反馈：

> 好的我大概理解了
> 那么现在继续吧
> 下一步是需要做什么呢？

本次将 `ensure_agent_user` 记为职责层面大致理解，返回 `prepare_workspace:186–193`。接下来需要接清的是每道题的可选初始化配置：

- `protocol == "scaleswe"` 时读取 `md["grading"]`；缺失或为空时使用空字典。
- `grading["swepro"]` 有值时调用 `apply_before_repo_set_cmd`；接着检查 `pre_commands`，有值时再调用 `apply_pre_commands`。两项互相独立，按源码顺序处理。
- 原教学例子使用 `grading={}`，因此两项都跳过，直接到 194 行写题目文件；不能由该例推断实际任务都没有初始化。

按阅读顺序 skill，建议下一处单函数入口为 `apply_before_repo_set_cmd`（`swe.py:201–211`）：它能回答“题目配置中的准备命令怎样变成沙箱里的操作”。最小前置是已有 `sb`、`workdir` 和非空 `swepro` 配置；准备命令本身仍可能缺失，届时函数直接返回。阅读时接清命令来源、脚本写入与执行即可，再回到父函数 191 行查看 `pre_commands`。

当前只定位调用条件、候选入口和阅读边界，尚未展开该辅助函数的教学或建立新卡片；继续留在 Step 6。没有新增运行实验，也未将整个 `prepare_workspace` 标为读完。

<a id="apply-before-repo-set-cmd-entry"></a>

## 5. 2026-10-22：将配置命令写成脚本并执行

用户确认上一轮推荐的函数：

> 好的那么请看一下这里 你想要读的这个function吧

本次从 `prepare_workspace:190` 进入 `apply_before_repo_set_cmd:201–211`。沿用已就绪的 `sb`、`agent` 用户和 `/workspace/repo`；为了观察这个分支，子卡将 `swepro` 设为含 `before_repo_set_cmd="mkdir -p .cache"` 的字典。这是教学构造，父卡原有空配置示例继续保留。

### 本轮建立的关系

1. 配置中的命令先变成 `before`，再与 `set -e`、`cd /workspace/repo` 拼成 `payload`。此时只是本地字符串；没有配置命令时函数直接返回。
2. 第一次 `sb.exec` 以 `root` 身份准备远端 `/workspace/swepro_setup` 目录及其归属，供 `agent` 写入脚本。
3. `sb.write_file` 以 `agent` 身份将文本保存为 `before.sh`；保存文本和执行其中的命令是两步。
4. 第二次 `sb.exec` 以 `agent` 身份运行 Bash 脚本。脚本位于 `/workspace/swepro_setup`，但其中的 `cd` 让本例准备命令在 `/workspace/repo` 生效，确保该目录下的 `.cache` 存在。
5. 最后执行使用 `check=False`，本函数没有检查其结果；正常返回 `None` 不能单独证明脚本执行成功。`set -e` 控制脚本内的退出行为，Python 是否检查退出码是另一层。
6. 完成后仍使用同一个沙箱，回到父函数 191 行查看 `pre_commands`。

### 证据与本轮边界

- 固定源码仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；核对 `swe.py:185–211` 与 `sandbox.py:309–376`，`set -e` 的依据收在卡片折叠来源中。
- [本函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)保存当前三个输入、脚本全文、两次执行与一次写入的关系。scope 和父卡链接此处，旧步骤及当前 `03` 保持原样。
- 本轮仅做静态核对，没有申请或运行真实沙箱；真实题目脚本、SDK 内部机制和完整失败处理继续留白。用户确认的是阅读对象，尚无本函数机制的直接复述，未结束 Step 6。

<a id="before-repo-set-purpose"></a>

## 6. 2026-10-22：命令来源与题目前置准备的用途

用户提出当前理解，并追问函数本身的用途：

> 好的 我可以简单理解为这里是根据这个
> swepro的这个格式
> 来生成一个before_repo_set_cmd 需要执行的指令吗
>
> 不过这个apply before repo set cmd具体是为了做什么呢？

### 先分开输入命令与生成脚本

`_metadata_scaleswe` 从 `sample.metadata` 取得 `swepro`，放入 `md["grading"]`。`apply_before_repo_set_cmd` 读取其中 `before_repo_set_cmd` 对应的现成命令，再添加 `set -e` 与 `cd`，生成并执行脚本。它承担配置落地的职责，具体要做哪些准备由题目数据给出。

上一轮的 `mkdir -p .cache` 只是示例：假设这道题要求先准备缓存目录，配置提供这条命令，本函数负责在工作目录执行它。不能把所有题目的准备都归纳为创建缓存目录。

### 为什么需要这个入口

- `ensure_agent_user` 准备通用的用户与目录归属；本函数进一步执行这道题额外指定的工作区准备。
- 工作阶段：`prepare_workspace:190` 对执行沙箱 `sb` 调用它，之后才写题目并启动 Agent。
- 评测阶段：采用 `swepro` 分支时，`_grade_scaleswe:273` 对独立评测沙箱 `ev` 调用它，之后才应用 Agent 的补丁、执行评测。

从这两处调用可知，框架在工作与评测阶段复用同一份题目准备配置。当前只需要理解它是落实题目前置准备的入口；评测的其他内部细节和每道题的真实命令继续按需查看。

源码证据为固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `swe.py:83–110、177–211、269–282`。本轮只静态核对来源和调用位置，没有运行新命令或打开新步骤。用户提出的“生成指令”已给出校正，尚待反馈；原有脚本全文、输入输出和执行顺序保留。

<a id="grading-input-context"></a>

## 7. 2026-10-22：先看 metadata 与 grading 的配置结构

用户在上轮澄清后反馈，并指出新的观察重点：

> 好的 我大概理解了 反正就是按照这个swe 单独配置一下需要提前执行的一系列操作对吗
> 我可以这么理解吗？
> 下面的pre commond也是类似的
> 那么这里的重点应该就是这里的grading也就是这个metadata中的信息
> 是否应该先处理一下这一部分呢？

本次沿用 Step 6，先补配置的来源和结构。用户已概括按题目配置执行提前准备的用途；对 `pre_commands` 的类比符合两者都承接预先给定命令的职责，具体实现仍未展开。

### 本轮补清的关系

1. `sample.metadata` 保存原始题目资料；当前 `scaleswe` 分支的 `get_metadata → _metadata_scaleswe` 将相关字段组织成 `md["grading"]`。原始输入与整理后的分组分别展示。
2. `before_repo_set_cmd` 在 `swepro` 内部；`pre_commands` 与 `swepro` 同级。两条准备路径都可以提供，并按顺序执行。
3. `grading` 同时包含评测资料：`swepro` 这一整组配置、`eval_cmd` 和 `f2p_script` 支持不同评测路径。它保存的是配置，实际分数在后面的评测中产生。
4. 当前 `prepare_workspace` 只取准备部分；后面 `_grade_scaleswe` 还会按 `swepro → eval_cmd → f2p_script` 选取一个评测分支。准备路径的并用与评测路径的选择分别说明。
5. 原父卡的空 `grading` 是教学省略。真实 `_metadata_scaleswe` 返回四个键，没有资料时可为 `None`；空字典与这些空值在父卡的准备场景中效果相同。

### 记录位置与停止点

- 新说明当时放入本步 references/grading.md（[现已合入 md 输入说明](references/metadata.md#grading)），链接回 Step 4 已有的 `md` 说明；scope、父函数与当前子函数只增加入口，原有代码和输入输出示例保留。
- 配置是跨函数共享的输入背景，当前不把它伪装成单个函数卡片，也不新开 step；本步仍为三份函数卡片，旧步骤与 `03` 不改写。
- 核对固定源码 `swe.py:77–110、177–224、253–338`。示例用于字段整理与职责说明，没有实际运行准备命令或评测，也没有将整个 Step 6 标为完成。
- 从原源码提取字段整理函数，以简单字段对象完成本地纯数据核对：参考页示例与实际输出一致，空配置保留四个 `None`，回退及顶层优先规则符合表格。这个局部验证不代表真实数据集加载、脚本执行或沙箱运行。
- 看清数据结构后可回到 `prepare_workspace:191–193` 接 `pre_commands`；本轮尚未开始该辅助函数的独立阅读。

<a id="real-task-preparation-example"></a>

## 8. 2026-10-22：用真实题目补回准备函数的输入与输出

用户对字段来源与整体职责仍感到困惑，要求真实例子：

> 这里的eval cmd和f2p script是哪里来的呢？
> 我不是特别理解
> 主要是是否能够哪一个真实的例子
> 否则我梳理不清楚这里到底在做什么
> 感觉这里的这个prepare workspace function 我根本不清楚到底是在做什么

### 本次修正了什么

此前把准备与评测的字段一起展开，但父卡使用空配置示例，未让用户看到一道实际任务怎样经过准备。用户对两个辅助函数用途的初步理解继续保留，不能据此推断已理解整个 `prepare_workspace`。

- 找到公开 Scale-SWE 的真实题目 `auth0_auth0-python_pr671`，从固定版本 JSONL 读取原始记录，并与公开 Viewer 核对一致；保存本步需要的七个原始字段。
- 分开三类资料：`pre_commands` 让仓库回到指定基础版本；`problem_statement` 告诉 Agent 要修复请求格式；`f2p_script` 提供之后检查请求行为的测试代码。
- `prepare_workspace` 只准备用户与工作区、按配置执行准备命令、写题目文件。它不执行 `eval_cmd` 或 `f2p_script`，也不计算 reward；调用后同一个 `sb` 才交给 Harness 启动 Agent。
- `eval_cmd` 从输入 `metadata["eval_cmd"]` 取出；`f2p_script` 从输入 `metadata["remote_env_info"]["f2p_script"]` 取出。它们由题目数据提供，不由准备函数或模型生成。真实公开行的字段在顶层，本轮显式展示了将其映射到 Slime 输入布局的教学操作，没有冒称仓库已提供该数据转换器。
- Slime 自带的 CPU 测试 fixture 使用 `eval_cmd="true"`。它是实际存在的集成测试输入，但使用假环境检查流程，不能当作评估代码修复正确性的真实标准。

### 保存与验证

- [父函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)采用真实题目作为当前主例，原先的空配置教学例保留在折叠来源中；原有栏目、阶段和子函数入口保留。
- [真实例子参考](references/scaleswe-auth0-example.md)保存来源、输入映射、准备与后续评测的分工；[JSON 节选](references/scaleswe-auth0-example.json)保存未经改写的原始字段。`grading` 参考和 scope 只补接续入口或更换主例的说明，没有新增函数卡片。
- 局部执行提取出的真实 `_metadata_scaleswe`、`prepare_workspace` 及准备辅助函数，以只记录调用的假沙箱替代远端操作。断言通过：原始字段正确映射，顺序是用户准备命令 → 写准备脚本 → 执行准备脚本 → 写题目文件，返回 `None`，没有写入或执行评测脚本。没有执行记录中的任何 shell 命令。
- 原始 `f2p_script` 的末尾直接调用 `pytest.main`，未把结果传给进程退出码；当前 Slime 用退出码评分。因此这条原始记录仍有评测适配工作，不能宣称原样接入即可得到有效奖励。公开镜像在 E2B 中的可用性也未验证。上述限制集中保存在参考页，未混入准备函数的执行步骤。
- 此次只补当前 Step 6 的阅读材料，保留前序步骤和 `03`。用户对新例子尚无理解反馈，本步没有结束，也没有将 `apply_pre_commands` 标为独立读完。

<a id="prepare-workspace-reading-order"></a>

## 9. 2026-10-22：从已处理的用户准备接续阅读

用户要求根据真实题目的讨论重新确定阅读顺序与优先级：

> 那么现在考虑一下 按照这个顺序 重新看一下这里的prepare workspace的内容吧
> 我的意思是拆分出来的一系列函数的讲解
> 我需要了解一个我应该按照顺序好好读的不份额n这里的ensure agent use已经处理完了
>
> 请根据我们刚才的对话中宠幸确定一下应该阅读的顺序和优先级

此次沿用阅读顺序 skill，当前问题收敛为：**已有可操作的沙箱，题目提供的准备命令怎样改变工作区，然后如何把题目交给 Agent？** 用户对 `ensure_agent_user` 的处理状态按本次表述保留，不重开其内部讲解。

1. 简短回到 `prepare_workspace:186–193` 核对当前输入：真实题目没有 `swepro`，有 `pre_commands`。因此先检查的分支会跳过，下一处实际交接是 193 行。
2. 下一处重点推荐 `apply_pre_commands:214–224`。它直接回答“给定准备命令如何变成工作区里的操作”，沿用本例的命令，不另造数据。建议未来卡片保留命令输入、脚本文本和路径、执行目录、返回值与状态变化，并点明 `check=False` 的限制。
3. 读完后返回父函数 194–198 行，在父卡中接清 `problem_statement → PROBLEM_STATEMENT.md`。`write_file` 与 `exec` 复用已有能力认识，暂不递归进入 SDK。
4. 最后把本函数的三个阶段串起来，说明返回 `None` 后同一个 `sb` 如何交给 `generate.py:205` 的 Harness；读通之后再写 task flow。

`apply_before_repo_set_cmd` 已有卡片且在本例不触发，列为按需回顾的另一配置分支，不作为重读的必经步骤。`eval_cmd`、`f2p_script` 留在后续评测阶段；完整 metadata 加载链和 SDK 细节不列为本轮新前置。

以上是针对当前理解缺口的阅读推荐。真实执行仍按源码先检查 `swepro`、再检查 `pre_commands`；两项有值时都会执行。此次更新 [scope 的局部导航](01-scope.md)，保留函数卡片和历史记录，没有提前创建下一张卡片或标记 Step 6 完成。顺带按源码修正了整体骨架中 `boot_agent_sandbox` 名称内误插的空格。

<a id="metadata-before-preparation-functions"></a>

## 10. 2026-10-22：先读完整输入，再读对应操作

用户指出输入背景本身尚未讲清，修正上一轮的优先级：

> 我在想的问题是
> 这里不应该是优先看一下这里的md文件是什么吗？
>
> 这个md里面应该是需要包括grading是什么
> 特别是这里的grading需要包括
> swepro
> pre command
> 然后在这个基础上再看一下这里的apply before repo set cmd
> 以及这里的
> apply_pre_commands
>
> 最后再看一下这里sb writefile这个function具体是在做什么
>
> 这样子的md文件里面其实也需要包含problem statemenmt
>
> 那么应该把这里的md文件里面的problem statement也写清楚才对对吗？
>
> 总之是需要考虑吧这里的启动项的信息写清楚后续的操作才能明白

### 对上一轮建议的修正

上一轮优先按真实题目的实际分支推荐 `apply_pre_commands`，只安排简短核对输入。但用户需要先理解输入本身，以及每个字段与后续操作的对应关系。Step 4 的旧 `md` 说明为当时的会话准备省略了问题描述和评测字段，不能直接承担当前的完整输入说明。

本次不把“先看输入”扩成递归阅读全部数据加载代码，而是先补工作区准备必需的字段含义、来源和去向。真实题目没有 `swepro`，也不能因此省去本函数另一准备入口的职责说明。

### 本轮确定的顺序

1. `ensure_agent_user` 沿用已处理状态。
2. 优先看当前 [md 输入说明](references/metadata.md)：`workdir`、`grading`、`swepro.before_repo_set_cmd`、`pre_commands` 和 `problem_statement`。代码中的 `md` 是字典；说明文件负责解释它。题目文字与 `grading` 同级，前者最终交给 Agent 阅读，后者按字段分别服务于准备和评测。
3. 对照输入回顾 `apply_before_repo_set_cmd`，再读 `apply_pre_commands`。两者分别接住哪项配置、怎样写入和执行命令，是后续观察重点；已有前者卡片继续复用。
4. 最后接清 `sb.write_file` 的本次调用：路径、题目文本、执行身份与远端文件。若继续读实现，沿当前 E2BSandbox 的字符串内容路径展开，其他内容类型与通信重试后置。
5. 上述关系读通后再收拢父函数和 task flow；本次补充输入说明不等于后续函数已经读完。

本次只在 Step 6 补 `references/metadata.md`，更新 scope、入口和父卡的参考链接；Step 4 原记录、已有例子及继承记忆保留。字段及消费者依据固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `swe.py:77–110、177–224` 和 `sandbox.py:342–377` 核对。没有新建函数卡片、执行远端操作或结束本步，输入模型解释尚待用户反馈。

<a id="merge-grading-into-metadata"></a>

## 11. 2026-10-22：统一 md 输入入口

用户确认希望从一份输入说明开始：

> 好的那么应该把这里的grading删掉了对吗？
> 这样子我一开始先看清楚这里的md文件包含了什么

已将原独立 grading 文档中的字段来源、教学例子、准备与评测分工、验证及来源并入 [md 输入说明](references/metadata.md)。正文先展示整体输入和操作对应，补充细节放入折叠区；删除独立的 `references/grading.md`，相关入口与历史引用改为指向合并后的内容。

删除的是重复的说明入口；代码里的 `md["grading"]` 仍是本页要解释的一个配置分组。没有改动源码、数据结构、旧步骤或继承记忆，当前阅读顺序仍从 md 开始。

<a id="apply-pre-commands-function-card"></a>

## 12. 2026-10-22：准备命令怎样写入并执行

在统一 md 输入入口后，用户确认继续：

> 好的再看一下这里的apply pre commands吧

本轮从 `prepare_workspace:191–193` 进入 `apply_pre_commands:214–224`，继续使用真实题目 `auth0_auth0-python_pr671` 的完整 `pre_commands`，不换成另一条构造命令。

### 本次解释的关系

1. 输入来自 `md["grading"]["pre_commands"]`，命令已经由题目数据提供；函数将字符串中的字面换行标记转为实际换行，或将列表中的非空条目按行连接。当前真实题目走字符串分支。
2. `write_file` 以 `agent` 身份把 `set -e` 和完整命令写成远端 `/workspace/__cagent_pre__.sh`。这一步保存文本，尚未运行其中的 Git 操作。
3. `exec` 设置脚本权限，进入 `/workspace/auth0-python`，再用 Bash 执行脚本。脚本的存放路径与命令工作的目录不同。
4. 本例命令包含清理、切换题目指定基础版本及 Git 状态整理；正文只展开切换版本的用途，完整命令原样保留在卡片折叠区，不逐项讲解所有选项。
5. `check=False` 且函数不检查命令结果，因此正常返回 `None` 不能证明准备成功。返回后接回 `prepare_workspace:194` 写题目文件；本辅助函数不写入题目说明，也不运行评测。

### 记录与验证范围

- 新建 [apply_pre_commands 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md)，包含来源、LLM 四项、完整输入的定位、输出与副作用、两段内部处理、用户原话、未知和折叠来源。本步 `02` 增至四份函数卡片。
- 核对固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `swe.py:57、191–224、274–275`，以及 `sandbox.py:309–340`。评测也复用相同准备入口，当前不深入其后续流程。
- 从真实源码提取函数，以只记录操作的对象替代沙箱，验证真实字符串的换行转换、完整脚本、写入与执行的先后、执行目录、用户、超时与 `check` 参数；另用教学列表核对空条目过滤，并模拟返回非零退出码，函数仍返回 `None`。未执行任何记录下来的 shell 命令，没有创建远端沙箱。
- 当前是用户确认进入本函数，尚无对内部机制的复述；卡片生成与局部核对不算个人掌握，也未结束 Step 6。

<a id="preparation-effects-and-sandbox-handoff"></a>

## 13. 2026-10-22：准备效果留在哪里，接下来读什么

用户在两个准备入口讲解后反馈，并追问下一处：

> 好的 我大概明白了
> 那么按照当前的这两个步骤的话都解决了的话
> 那么目前应该看哪一块呢？
> 我可以理解为这里其实就是把swe的一系列逻辑全部写到这里的agent sandbox里面了
> 然后吧这样子sandbox将给下面呢？

本次澄清：

1. 两个入口根据题目配置，把已有命令写成远端脚本并执行。例如当前真实题目的 `pre_commands` 用于切换基础版本和整理工作区；未提供的可选配置会跳过。
2. 远端留下脚本及命令执行产生的工作区变化。选择步骤、读取配置和组织调用的 SWE Python 代码仍在本地；评测字段也没有在本阶段全部写入或执行。
3. 下一处回到 `prepare_workspace:194–198`，看 `sb.write_file` 如何接住目标路径、`md["problem_statement"]` 和 `user="agent"`，得到远端题目文件。前面的脚本用于准备工作区，最后的文件用于告诉 Agent 要解决什么问题。
4. `prepare_workspace` 正常返回 `None`。`generate:204–206` 保持原来的 `sb`，等待准备函数结束后，把同一个本地沙箱对象传给 `HARNESS_CLS().run`，继续操作同一远端沙箱。

本次阅读建议仍在原 scope 内：先读题目写入这一处调用的输入与结果，需要实现时只展开 `E2BSandbox.write_file` 的字符串路径；其他内容类型和通信重试后置。这里先定位下一处，没有新建函数卡片或提前结束 Step 6，task flow 留待父函数读通后整理。

用户的“大概明白了”已补入本步函数记录；上述边界澄清属于助手说明，尚无逐项确认。本轮静态核对固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `swe.py:177–224`、`generate.py:203–212` 与 `sandbox.py:375–378`，没有运行远端命令。

<a id="run-cross-process-communication"></a>

## 14. 后续通信问题：已独立到 Step 7

用户在本步交接处追问信息怎样在调度、沙箱、Adapter 与 SGLang 之间流动，随后明确要求单独创建 step。原始问题与当时的解释已完整迁入 [Step 7 的形成过程](../step-008-harness-communication/04-flow.md#run-cross-process-communication)，跨组件说明见 [Step 7 通信参考](../step-008-harness-communication/references/run-communication-path.md)。

本步继续保留工作区准备的记录与未收束项；[独立成步的确认](../step-008-harness-communication/04-flow.md#separate-communication-step)不表示 Step 6 已全部完成。
