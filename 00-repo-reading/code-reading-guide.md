# 代码阅读指南

[方法入口](README.md) · [完整工作流](workflow.md)

2026-10-20，用户提供并要求采用、保存以下阅读准则。原文保留在下方；当前 Slime 源码的对应关系单列在文末，不改写原文。

- [方法一：先剪枝，再沿主线下钻](#方法一先剪枝再沿主线下钻)
- [方法二：读代码时记录什么](#方法二读代码时记录什么)
- [方法三：有了骨架后，怎样选择阅读顺序](#方法三有了骨架后怎样选择阅读顺序)

将第一条方法用于本步 `01-scope.md` 时，使用 [repo-reading-scope skill](../.agents/skills/repo-reading-scope/SKILL.md)；详细方法与紧凑 scope 样例在该 skill 的 `references/` 中。

## 方法一：先剪枝，再沿主线下钻

### 使用方式

1. 先定位组织主流程的函数，名称作为线索，结合实际调用判断职责。
2. 第一遍只提取正常路径：配置、检查、日志、异常和失败包装暂时折叠，保留理解主线必要的上下文。这是阅读裁剪，不修改或删除实际代码。
3. 沿核心调用按需下钻，本轮深度不超过两层；弄清输入、输出和交接后返回主线。更深的问题先留下，后续另定阅读单元。

每轮具体讨论的函数与问题仍按既有规则由用户确认；已经明确指定时直接沿用。这里只规定读法，不把浏览过的函数自动记成已掌握。

### 用户提供的准则原文

面对一个充斥着几十个函数的复杂模块，资深工程师的第一反应不是“从上往下看”，而是先进行**“残酷剪枝（Pruning）”**。

以你本地的 generate.py 为例，里面有配置类、沙盒启动、各种 _abort、_log 工具函数。资深工程师会用一套非常标准的三步法来决定阅读顺序。

──────

#### 第一步：找出“指挥官函数”（Orchestrator）

在绝大多数工程中，一个文件里 80% 的函数都是**“仆人函数”（辅助做字符串拼接、记日志、校验入参），只有 1 到 2 个是“指挥官函数”**（负责串联主流程）。

• 怎么找？
  • 找没有下划线前缀、名字代表主动作的公共函数：如 run()、step()、execute()、generate()。
  • 在当前文件里，唯一的指挥官函数就是 第 203 行的 async def generate()。
  • 原则：直接跳过前面 200 行的所有函数，第一眼只看 generate()！

──────

#### 第二步：开启“脑内过滤器”，残酷忽略 5 类噪音代码

打开 generate() 后，资深工程师在第一遍读的时候，眼睛会自动把以下 5 种代码涂黑/视而不见：

1. 环境与配置解析（忽略）：CONFIG = SweConfig.from_env()
2. 前置安全检查（Guard Clauses）（忽略）：if not md["image"]: return ...
3. 日志与耗时统计（Telemetry）（忽略）：logger.info(...)、t0 = time.time()
4. 超时与异常兜底（Error Handling）（忽略）：try...except asyncio.TimeoutError:、_log_timeout_diagnostic()
5. 失败分支包装（Abort Wrappers）（忽略）：所有的 return _abort_result(...)

##### 💡 过滤后的神奇效果：

原本将近 100 行的 generate()，被大厂工程师大脑过滤后，其实只剩下了这 7 行真正干活的核心骨架：

```python
# 这才是 generate() 的真正灵魂（只看这 7 句）：
adapter.open_session(session_id, ...)              # 1. 开启一个会话通道
async with boot_agent_sandbox(...) as sb:          # 2. 启动沙盒虚拟机
    baseline = await swe.prepare_workspace(...)    # 3. 准备代码仓库
    await harness.run(sb, adapter_url=..., ...)    # 4. 让 Agent 在沙盒里开工修改代码！
    diff_text = await swe.git_diff(...)            # 5. 提取改动补丁 (git diff)

reward = await swe.run_evaluation(diff_text, ...)  # 6. 跑单元测试算得分 (Reward)
samples = await adapter.finish_session(..., reward)# 7. 打包成样本返回给训练器
```

──────

#### 第三步：绝对精简的函数跳转顺序表（按需深潜）

看完了上面骨架中的 7 句话后，整个 Coding Agent 的轮廓已经 100% 建立了。接下来，才按照**“顺藤摸瓜”**的顺序，依次去看调用的子函数。

##### 建议的精准阅读顺序：

```text
Step 1: 【骨架层】generate.py 中的 generate() (只读上述 7 行)
   │
   ├──> Step 2: 【执行层】跳转看 harness.run()
   │     └── 文件：slime/agent/harness/claude_code.py (或 common.py)
   │     └── 目的：只看一件事 —— 它在沙盒里敲了什么 shell 命令把 Agent 启动起来的？
   │              (你会看到它传了 --permission-mode bypassPermissions 并且把 API 地址指向了 adapter)
   │
   ├──> Step 3: 【捕获层】跳转看 adapter.open_session() 与 adapter 处理请求
   │     └── 文件：slime/agent/adapters/anthropic.py
   │     └── 目的：看 Agent 发给它的工具调用，它是怎么转给 SGLang 并拿到 logprob 的。
   │
   ├──> Step 4: 【评测层】跳转看 swe.run_evaluation()
   │     └── 文件：examples/coding_agent_rl/swe.py
   │     └── 目的：看它怎么把 git diff 打到测试沙盒里执行 pytest，如果测试全通就返回 reward=1.0。
   │
   └──> Step 5: 【收尾层】看 adapter.finish_session()
         └── 目的：看它怎么把刚才生成的全部 token、loss_mask 和 reward 拼成一个 Sample 对象。
```

──────

#### 总结：下次读任何新代码的心智口诀

1. 射人先射马：先找最核心的公共入口函数（如 generate、main、step），忽略所有开头定义的辅助类和小工具函数；
2. 只看快乐路径（Happy Path）：闭上眼睛跳过所有 try...except、if error、assert 和 logger；
3. 调用深潜不超过 2 层（DFS Depth <= 2）：追函数调用时，跳进子函数弄懂它返回什么就立刻跳出来，绝不在子函数的子函数的子函数里无限迷路。

### 当前 Slime 版本的对应关系

核对版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。原文中的比例保留为强调阅读重点的表达，不作为本仓库函数统计或学习完成度。

- `generate` 在本机版本的 [generate.py 第 182 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L182)，不是原文所举的第 203 行。
- 当前调用是 `await swe.prepare_workspace(...)`，函数返回 `None`，没有接收 `baseline`；实际执行入口写作 `HARNESS_CLS().run(...)`。
- 当前评测调用接收 `md` 和 `diff_text`，返回值解包为 `reward, applied_cleanly`。[run_evaluation](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L239)按协议分派评测，具体分支可以使用评测 harness、shell 命令或 pytest 脚本。
- `open_session` 和 `finish_session` 的共同实现位于 `slime/agent/adapters/common.py`；Anthropic 的协议差异在 `anthropic.py` 中。
- 下方骨架选择 `evaluation=False` 的正常路径；省略输入准备、日志、失败分支、附加元数据与最后清理。它是教学裁剪，不是完整可运行函数。

```python
state.adapter.open_session(session_id, sampling_defaults=sampling_params, max_context_tokens=...)
async with boot_agent_sandbox(md["image"], instance_id) as sb:
    await swe.prepare_workspace(sb, md["workdir"], md)
    agent_exit_code = await HARNESS_CLS().run(
        sb, workdir=md["workdir"], session_id=session_id,
        adapter_url=state.adapter_url, time_budget_sec=..., prompt=swe.SWE_PROMPT,
    )
    diff_text = await swe.git_diff(sb, md["workdir"])

reward, applied_cleanly = await swe.run_evaluation(md, diff_text=diff_text, timeout_sec=...)
samples = await state.adapter.finish_session(
    session_id, base_sample=base_sample, reward=float(reward), extra_metadata=...,
)
return samples
```

这份骨架先保留“会话 → 执行环境 → 工作区 → Agent 执行 → 修改 → 评测 → 样本”的主线。具体调用再按本轮确认的问题展开，省略处继续保留为待回查的边界。

## 方法二：读代码时记录什么

2026-10-20，用户要求将以下内容作为“如何读”的第二条。四类记录分别用于恢复数据关系、定位当前追踪路径、追问设计原因和保留局部观察；原文继续保留，当前记录体系的对应方式另列在后面。

### 用户提供的记录方法原文

> 那么大厂程序员会记录吗 例如通过记录一个函数具体是在做什么 来了解后续会做什么 还是不太会？

<details>
<summary>粘贴时附带的界面文字</summary>

▸ Thought for 16s

A dual sandbox design was implemented to prevent test tampering, raising questions about the reward computation's location and the adapter's threading. Investigating the architecture, a data p...

</details>

他们一定会做记录，但记录的内容和方式，与很多人想象的“逐个函数做笔记”完全相反。

初学者最容易陷入的一个低效误区是：拿个笔记本，像翻译文言文一样，逐行记录“函数 A 做了什么，函数 B 做了什么”。
在大厂工程师看来，这种记录方式性价比极低——因为这只是把 Python 代码用自然语言重新抄了一遍，不仅耗时耗力，而且一旦代码重构，笔记立刻报废。

大厂的资深工程师在看代码时，通常只会记录以下 4 种极高信息密度的东西：

──────

#### 1. 记“数据形态的变化”（数据账本，而不是函数说明）

资深工程师最关心的不是函数名字，而是**“数据进这个函数之前长什么样，出来变成了什么样”**。

##### ❌ 低效记录（记函数做了什么）：

│
│ • prepare_workspace()：初始化沙盒环境并克隆仓库。
│ • harness.run()：启动 Claude Code 执行任务。
│ • git_diff()：获取修改后的 diff。
│ • run_evaluation()：执行测试用例。

##### 高效记录（数据状态跃迁线）：

资深工程师只在草稿纸或临时文档里写这一行“数据流水线”：

```text
           沙 盒 执 行                      测 试 沙 盒                     Adapter打 包
Task JSON ─────────→ Diff Patch (文 本 ) ─────────→ Reward (0.0/1.0) ────────────→ Sample (带  Loss Mask)
```

• 价值：只要盯紧这一行数据状态的流转，即使具体的函数名未来从 prepare_workspace 改名叫 init_repo，系统的本质逻辑依然一清二楚。

──────

#### 2. 记“临时面包屑”（防止自己深潜时迷路）

在跟踪深层调用时，人的大脑很容易在跳了 3 层函数之后突然忘记自己最初是从哪来的（“我刚才为什么要看这个函数来着？”）。

工程师会在编辑器旁边的草稿纸（Scratchpad）上写下极度随意的临时路径：

```text
[当前追踪目标：Agent 怎么拿到模型回复的？]
generate()
  └─> harness.run()
        └─> 发现它启动了 claude 命令行，把 API URL 指向了本地 Adapter
              └─> (跳到 adapter/anthropic.py) 正在看 handle_messages() ...
```

• 价值：一旦在最底层看明白了，顺着这个小面包屑一层层退回主函数，随手把这行草稿删掉，不留任何记忆负担。

──────

#### 3. 记“疑点与反常识决策”（The "Why" List）

他们记录最多的，往往是那些**“反直觉、不符合常规设计”的地方**：

│
│ • 疑点 1：为什么评测代码 swe.run_evaluation 不在刚才执行代码的同一个沙盒里跑，非要新建第二个沙盒？
│ → 结论：为了防 Agent 作弊篡改测试脚本（Reward Hacking）。
│ • 疑点 2：为什么 Adapter 里的 Web 框架用多线程（Threaded aiohttp）跑，而不是直接用当前进程的 asyncio？
│ → 结论：为了避免评测卡死时把网络监听事件循环阻塞掉。

这些关于**“设计意图（Why）”和“踩坑权衡（Trade-off）”**的记录，才是几个月后回顾时最有价值的财富。

──────

#### 4. 顶级程序员的高效小妙招：把“Git Diff”当笔记

很多经验丰富的程序员在阅读大项目时，甚至连笔记软件都懒得开，他们直接用 Git 本身做笔记：

1. 新建一个本地临时阅读分支：git checkout -b learn-code；
2. 在读代码时，直接在代码关键行上面写注释：

   ```python
   # NOTE: 核心分流点：如果是多轮交互，这里会通过 X-SMG-Routing-Key 锁定 GPU 显卡
   adapter.open_session(...)
   ```

3. 甚至随时插入 print(f"DEBUG: {data=}") 打桩打印；
4. 读完之后，在终端敲一行：

   ```bash
   git diff
   ```

   你刚才所有的理解、思考路径和关键函数，全部被 Git 以高亮的形式精准整理了出来。
5. 想要保存时，直接 git commit -m "docs: my architecture notes"；不想要时随时丢弃。

### 与当前记录体系及源码的对应

上述原文保留作者的表述，不将“所有工程师都会这样做”等措辞作为调查结论。应用时重点是记录数据、关系、疑问与证据，避免逐行复述代码。

- **函数记录继续保留。** 当前短期 memory 已包含场景、输入输出、用户原话和未知，不是只有“函数做什么”的标签。局部数据变化记在函数卡片；跨函数的数据交接放在步骤 README / scope，互相链接，不重复抄写。
- **临时路径与形成过程分开。** 导航草稿用于当前定位；实际形成的新认识、关键问题与修正仍按既有规则保存，不因草稿可以删除就清除学习历史。Git diff 是可选的临时记录方式，不替代正式函数记忆。
- **Sample 的来源不止 reward。** 上图是简化导航；当前 `finish_session` 汇合会话轨迹、基础 Sample、reward 等信息，不能理解为仅把一个分数转换为带 loss mask 的样本。
- **实际请求入口。** 当前 `AnthropicAdapter._register_routes` 把 `/v1/messages` 注册到 `BaseAdapter._run_turn`，不是原文示意中的 `handle_messages`。
- **设计原因要有依据。** 当前 `swe.run_evaluation` 的源码注释明确说明使用干净评测环境防止测试篡改；`run_app_in_thread` 可确认 Adapter 使用独立线程与事件循环，但“为了防止评测卡死”的具体动机仍需另找证据，先作为待验证解释保留。
- **路由示意要核对。** `X-SMG-Routing-Key` 当前在 `call_sglang_generate` 中随模型请求发送，不在 `open_session` 中设置；仅凭这一段代码不能断言它“锁定某张 GPU”，还需核对后端路由行为。

以上按固定版本 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 核对：入口见 `slime/agent/adapters/anthropic.py:48`，线程见 `slime/agent/aiohttp_threaded.py:46`，路由头见 `slime/agent/adapters/common.py:472`，评测见 `examples/coding_agent_rl/swe.py:239`。本次只保存阅读方法，没有在被阅读仓库创建分支、插入调试语句或提交代码。

### 从函数作用继续读懂实现：记录一次具体追踪

“函数负责什么”给出初始定位；继续阅读时，用一项具体问题串起源码位置、中间数据和实际动作。记录应使下次能恢复已经核对的解释，而不是只剩函数用途或重新逐行阅读。

公开工程实践可以提供参照：[Google 评审导航](https://google.github.io/eng-practices/review/reviewer/navigate.html)建议先建立整体认识、查看主要部分，再按合理顺序补充其他代码，必要时先读测试。[微软的代码变更理解研究](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/howdosoftwareengineersunderstandcodechanges_fse2012.pdf)调查了 180 位参与者，强调变更原因、正确性及对其他组件的影响等信息需求。这些材料面向代码评审与变更理解，不能直接当成所有大厂工程师统一使用某种笔记的证据；下面是借鉴它们、面向本仓库学习的记录建议。

**一次具体追踪只记录四项：**

| 项目 | 要留下什么 |
| --- | --- |
| 当前问题 | 这次要解释的一个具体行为；为什么继续看这里 |
| 代码证据 | 调用位置、实际执行体、关键中间值或状态变化；标明源码版本与静态/运行证据 |
| 当前解释 | 证据如何串成一个可复述的因果过程，包含适用条件 |
| 下一处未知 | 尚缺哪项证据，下一次应看什么；不把推测写成已确认结论 |

**示例：Adapter 地址怎样进入 CLI 的运行环境？**

来源为 Slime 提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。示例取正常配置路径，假设额外环境配置没有覆盖 `ANTHROPIC_BASE_URL`；这是静态源码追踪，没有运行沙箱或 CLI。

| 追踪位置 | 看到了什么 | 对解释有什么用 |
| --- | --- | --- |
| [BaseHarness.run](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L98) | 将入参 `adapter_url` 保存进 `ctx`，随后把 `ctx` 传给具体启动方法 | 确认地址的来源和第一次交接 |
| [ClaudeCodeHarness.launch_and_wait](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L62) | 将 `ctx.adapter_url` 放入 `env["ANTHROPIC_BASE_URL"]` | 确认地址怎样成为 CLI 使用的环境配置 |
| [额外环境配置分支](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L68) | 额外配置可以更新 `env` | 不能把初始字典值无条件当成最终值；本例需明确没有覆盖 |
| [run_agent](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L111) | 把 `env` 随命令交给 `exec_and_wait` | 确认环境配置传到了执行层 |

由此得到的解释是：在没有额外覆盖的路径上，地址作为 `run` 的输入，经 `ctx` 和 `env` 传到命令执行层。这里传递的是配置，HTTP 请求由启动后的 CLI 发出。

下一处未知可以写成：“`exec_and_wait` 怎样将环境配置交给沙箱中的进程？”若本轮只想解释地址的传递，可以先停；若继续研究启动实现，就以这个问题展开下一处，而不是重开所有前置函数。

这类追踪保存在实际 flow 或配套讲解中，函数记忆只提炼已弄清的实现路径和仍未解决的部分；跨函数关系仍在步骤层保留。用户理解与助手推导分别记录，后续运行观察可以验证或修正静态结论。

## 方法三：有了骨架后，怎样选择阅读顺序

用户进一步提出：已有七个步骤，为什么先讲 Harness.run？并要求把“先核心、后回查前置”的读法独立为推荐阅读顺序的 skill。

使用 [repo-reading-order](../.agents/skills/repo-reading-order/SKILL.md)：先根据当前问题选择能直接解释它的动作，再看清输入与输出，按需回查前置；每次回到已有骨架选择下一问。它与方法一配合：方法一提取骨架，方法三选择先深入哪一处。

关于 Harness 的完整原文与适用边界见[方法 reference](../.agents/skills/repo-reading-order/references/inside-out-method.md)，当前源码下的推荐例子见 [Coding Agent 阅读顺序](../.agents/skills/repo-reading-order/references/coding-agent-order.md)。启动问题可以先看 Harness，评分问题优先看评测；前置与收尾不按固定“价值等级”分类。推荐仍需接续本轮确认，不自动创建新的函数记忆。
