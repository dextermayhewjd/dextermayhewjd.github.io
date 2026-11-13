# Step 012 · 理解形成过程

<a id="start-step012"></a>

## 2026-11-12：校准 Harbor 0.25 并开始本步

用户确认“好的 校准一下 然后看一下这里的这个step把”。沿已确认的一个任务例子区分 Task/Agent/Verifier 的范围继续，不转成全配置通读。

本轮通过本地发布标签核对：Job._init_trial_configs:448 的普通分支经 _build_standard_trial_configs:459 调用 JobPlan.build_trial_configs:140；Task 目录加载入口为 Task.__init__:51，Verifier.verify:198。保留旧 0.18 scope 完整快照，新版入口和安装方法源码定位逐项更新。

选择 examples/tasks/hello-world：instruction 要求创建 hello.txt 写入 Hello, world!，Dockerfile 工作目录为 /app，tests 检查文件存在及内容。这里只定位该样例，完整文件消费过程留到后续当前函数之后阅读。

当前只建立 JobPlan.build_trial_configs 一张函数卡，使用一题、一个 Agent、一次尝试说明返回 TrialConfig 列表。强调 models/trial/config.py 的 TaskConfig 是来源引用，models/task/config.py 的同名类才描述 task.toml；不把助手说明预填为用户理解。

按 Step 011 的 03 + 02 完整继承前序记录。Step 011 实际回查的 _run_partition 此前只更新了 Step 010 原卡，本轮先补齐 Step 011 的调取副本再继承，保留原话和来源，不倒改原有 03。未安装依赖、切换 checkout、运行 Job 或集群。


## 2026-11-12：恢复 3.1 的稳定整体主线

用户指出 Step 012 的 scope 与 Step 010/011 不同，随后明确主要问题在 3.1，3.2 的替换可以理解。确认此前将 3.1 改成 Job 创建阶段的局部链，弱化了整体定位。本轮只替换 3.1：复用 Step 011 的 Slime → Dressage → Job/Trial → 结果返回总图，增加 _CREATE_JOB 的当前回查位置，并标出 Agent 配置、任务 instruction 与评测规则的消费位置。3.2 与此前章节逐字保持，阅读范围、当前函数和全部记忆卡均不变。


## 2026-11-12：复核 Step 012–017 的整体顺序

用户要求评估后续流程。已核对六份 scope 与 0.25 的环境创建、取消/重试实现；建议保持编号顺序，收窄各步到一个具体接口问题，逐步穿插运行验证。013 需分清对象创建与 start，016 需区分外部取消与返回失败结果后的重试；014 商用模型代理改造不作为无条件必修，015 复用既有轨迹与转换认识，017 作为整合回归。详细评估保存在[既有阅读规划](../../../../references/integration-reading-plan.md#steps012-017-review-20261112)。本轮不重排 scope、不新增函数卡、不推进当前阅读状态。


## 2026-11-12：用实际调用顺序校正 012/013 的先后判断（待调整范围）

用户要求确认是否应先 013 后 012，并希望讲解尽量按调用顺序。重新核对 Harbor v0.25.0：Trial.create:469 起先 _load_task:474，然后构造 SingleStepTrial；Trial.__init__:210–212 先 _init_agent、_init_user_agent，再 _init_agent_environment。运行阶段 Trial.run → _prepare，先 _setup_agent_environment（经包装调用环境 start），之后健康检查/skills，再 _setup_agent；Agent 执行和 Verifier 在 _run 中继续。

因此不能把整个 Step 012/013 当作两个严格串行的调用块：012 当前同时包含输入配置、Agent 准备及后期评测，跨越了环境阶段。助手修正“012→013 总体合理”不等于当前每项都符合调用顺序的表述。建议保留既有编号与稳定 3.1，总体由 Trial.create/Trial.run 作为主干；012 先读任务与 Agent/评测配置及对象选择，到环境创建入口进入 013；环境启动后沿父函数继续 Agent setup/run 与评测，已读部分只提醒，不重讲。是否将后期执行项从 012 主读清单移为后续消费位置，需在明确该边界后再改 scope；本轮不改动函数卡或移动章节。


## 2026-11-12：落实 012–017 的调用顺序 scope 调整

用户要求考虑重构阅读顺序/各步 scope。按已核对的 Trial.create/__init__/run 交接，正式收窄 012 到任务与 Agent 对象和环境入口；013 接环境创建/启动，014 接 Agent 准备/执行与请求，015 接产物/实际评测/结果，016 单独回看取消或普通失败，017 整合验证。3.1 继续统一使用前两步的整体主线形状，3.2 标明实际调用、前置回查和返回点，修正环境工厂位置与取消并非自动重试两处流程问题。

旧 scope 全量归档；未改动已有函数卡或前序记忆，未给未来步骤创建学习卡与完成记录。项目/主题入口和既有阅读规划同步当前分工。源码定位来自 Harbor v0.25.0 与 Dressage 固定提交的静态核对，尚无实际运行适配证据。


## 2026-11-12：在各步 3.1 直接标出本步范围

用户要求每个 step 的 3.1 直接显示当前关注的函数或部分。本轮仅修改 012–017 的 3.1 图内旁注与图例：012 标配置/Task/Agent 对象来源，013 标环境创建/启动/适配，014 标 Agent.setup/run 与模型交互，015 标产物/评分/提交，016 标故障回看，017 标整条链的验收点；同时标后续步骤的交接位置。六图函数与分支结构保持一致，3.2 和各步范围/阅读状态没有变化；未提前创建函数卡。


## 2026-11-12：正式沿当前入口阅读尝试配置组成

用户在 scope 调整后要求开始 Step 012。本轮从已建的 JobPlan.build_trial_configs 卡恢复调用现场：回查 Step 010 的 _CREATE_JOB，Job 创建中经 _init_trial_configs/_build_standard_trial_configs 进入组装函数，而非 Step 011 执行结束后继续生成配置。用 hello-world、一份 Agent 配置和尝试次数说明 TrialConfig 列表，先只看 task/agent/environment/verifier 的组合与返回；未自动进入 Task 加载或建立其他卡片，也不要求重读全部参数。


## 2026-11-12：补当前函数从 Step 010 创建 Job 处进入的背景

用户忘记首个函数从哪里开始，要求调用/阅读背景。核对 Dressage rollout.py:101–111 的 _CREATE_JOB 默认绑定和 :704 的创建调用，以及 Harbor v0.25.0 Job.create:209 的构造、__init__:116 和 _init_trial_configs:457/_build_standard_trial_configs:460。函数卡增加直达 Step 010 创建段的链接和一张简短调用树，标明编排侧创建配置、早于 job.run；不要求重新深读全部包装，不自动推进到下一函数。


## 2026-11-12：把调用背景链接放到 Step 012 的阅读入口

用户指出只改函数卡仍不足，进入 Step 012 时就需要链接说明应看哪个调用位置。本轮在 scope 3.2 顶部增加从 Step 010 _run_partition「1. 创建 Job」的 _CREATE_JOB 行进入，再到直接调用者 Job._build_standard_trial_configs:459–462，最后进入本步函数卡 caller-context 的导航；同步第 1 项表格与 README 入口，3.1 保持不变。未增加新函数阅读或改动其他步骤的范围。


## 2026-11-12：补齐 _CREATE_JOB 到直接调用者之间的路径

用户指出从 _CREATE_JOB 突然跳到 Job._build_standard_trial_configs 不明白。上一轮入口链接只给起点和直接调用者，缺少函数变量绑定与 cls 构造这两个重要交接。本轮明确 _CREATE_JOB 默认绑定 _default_create_job → Job.create → cls(...) 触发 Job.__init__ → _init_trial_configs 普通分支 → _build_standard_trial_configs → JobPlan.build_trial_configs。补入 scope 的连续源码入口与现有函数卡调用图，不另开新步骤或预建包装函数卡。


<a id="job-create-context"></a>

## 2026-11-12：先建立 Job.create 的函数卡，按需继续初始化

用户希望按函数看创建 Job 后怎样继续，并询问是否需要分别建立短期记忆。当前卡点实为 Job.create 返回前的初始化过程。新增 Job.create 卡，保留普通路径的材料准备、cls(...) 构造和返回；Job.__init__ 只列下一处源码入口，两个薄转发 _init_trial_configs/_build_standard_trial_configs 不提前各建新卡。已有 JobPlan 卡保留。scope 补前置回查并修正 TrialConfig 列表与 Job 对象的返回归属；当前入口先到 Job.create，不新增后续未读卡。


## 2026-11-12：3.2 与 Job 创建的逐函数阅读顺序对齐

用户要求修改 scope 3.2。本轮只重写该局部导航：1 Job.create → 2 Job.__init__ → 3 已有 JobPlan.build_trial_configs → 4 返回 Job.create 与 _run_partition，再经已读运行链到 5 Trial.create → 6 Agent 对象创建 → 7 环境入口。图与表同号，子调用的返回点明确，保留 _CREATE_JOB 默认绑定的来源；3.1、既有函数卡和后续 scope 未修改。未实际进入的新函数只保留源码链接，不预建卡片。


## 2026-11-12：补回 classmethod 声明，区分类与实例创建

用户认为先创建 job 再调用 create，并反馈旧卡只有简略骨架，无法看出关系。检查旧卡确实省略 class Job 和 @classmethod，直接从 cls 开始。按本轮实际卡点重排 Job.create 卡：调用方右侧 await 先完成、默认函数导入类并调用 Job.create、类方法接收 cls、cls(...) 构造并初始化实例、return job 后外层接住同一对象。将深层调用树改为明确的下一处 cls(...) 入口，保留配置组装卡链接，不跨层提前讲完 __init__。旧卡完整归档，保留全部原话与未知，无实际运行。


## 2026-11-12：区分 cls 与实例，确认下一候选为 Job.__init__

用户用“拿到 class、通过 cls 构建”复述并询问下一张卡。助手校准 cls 是类，cls(...) 构造新实例且调用 __init__ 初始化；推荐从 Job.create:209 的 job = cls(...) 进入 Job.__init__:77，聚焦保存材料、生成尝试配置和后续字段准备，完成后返回 Job.create。当前没有 Job.__init__ 独立卡，不把推荐当作已经展开。


<a id="job-init-reading"></a>

## 2026-11-12：从 cls(...) 进入 Job.__init__ 并建立函数卡

用户明确要求构建 Job.__init__ 短期记忆。按 v0.25.0 job.py:77–145 保留调用现场，说明 self 为新实例、__init__ 返回 None 而构造表达式得到实例；主干按源码顺序写材料保存、尝试配置、目录/记录、待运行列表、队列与 Job 回调登记，备注直接贴代码。普通新 Job 以外的恢复/特殊分支留完整来源。父卡、scope、索引与唯一进度接到当前函数，不预建内部辅助卡或把本轮记录视为已掌握。


## 2026-11-12：初始化复述、类方法与实例共享边界

用户复述材料保存、目录日志、进度/待运行配置、执行对象与 hooks，并询问 cls 是否免实例调用、产生的实例是否共享。校准为 @classmethod 绑定类，不是 cls 的名字产生行为；这里 cls(...) 构造不同 Job 实例，但 self.config = config 保留传入对象引用。这里先在 TrialQueue 登记三个 Job 状态回调，再在后续具体 Trial 上挂接。

运行一个独立的 Python 教学缩减例，仅保留 classmethod、cls(config)、self.config = config：输出 same_instance: False，same_config: True。此为语言语义实验，不是实际 Harbor 构造或运行；真实框架还涉及目录/环境等外部资源，不能由对象不同推断全部资源隔离。说明补入两张现有卡，不新增课程或函数卡。


## 2026-11-12：确认类方法关系，接回尝试配置生成

用户确认 @classmethod 与 cls 创建实例的关系，并询问下一处。推荐从 Job.__init__:116 的 _init_trial_configs 进入；当前普通路径在 :457 调 _build_standard_trial_configs，再由 :460 调已有 JobPlan.build_trial_configs。先交代这两个转交位置，不从 __init__ 直接跳过它们，不自动增加包装函数卡或推进未读状态。


## 2026-11-12：沿 Job 初始化正式进入尝试配置组装

用户确认继续前述函数并要求短期记忆。本轮复用已有 JobPlan.build_trial_configs 卡，避免重复建卡；把入口接到刚读过的 Job.__init__，保留两个短转交方法、静态方法签名、任务/Agent/次数的组合以及列表返回到 self._trial_configs 的位置。移除当前默认跳到题目目录的下一步表述，先返回初始化主线。用户原话、未知与版本来源保留；未运行构造或实际任务。


<a id="correct-init-trial-configs-entry"></a>

## 2026-11-12：纠正当前函数为 Job._init_trial_configs

用户明确指出要读的是 init trial config，质疑为什么助手反复指向 JobPlan.build_trial_configs。助手此前擅自把较短的分支函数当作可略过的中转，造成当前阅读对象错位。本轮按实际目标补 Job._init_trial_configs 独立卡，完整保留三分支与赋值，普通分支下的薄委派只作下一层入口。已有 JobPlan 卡保留为下游，不删除历史或假定用户读懂。父卡、scope、索引和唯一进度一并纠正到直接调用的函数。


## 2026-11-12：为 TrialConfig 增加同一场景的具体输入与输出

用户要求修改静态例子，直观看到 TrialConfig 的样子。本轮只替换 JobPlan.build_trial_configs 卡的原一句例子：用 hello-world、一份 Claude Code AgentConfig、Docker 后端、启用评测、一次尝试和确定性示意 Job ID 构造输入，展示返回列表第一项的 JSON 字段节选。明确真实返回为 TrialConfig 对象，随机名称由模型自动生成且示例用占位，尚无执行产物或奖励。核对了 JobConfig 和各嵌套模型字段、默认值与命名验证器；没有安装环境、运行模型或实际构造 Harbor 对象。其余阅读结构和进度不变。


## 2026-11-12：配置例子之后先返回创建主线

用户表示大概知道 config 的样子并询问下一部分。保留该局部理解，推荐先接清已有返回：JobPlan 的列表 → _init_trial_configs 保存到 self._trial_configs → Job.__init__ 完成剩余记录与队列 → Job.create 返回 Job。随后经已读 _run_partition/plugin/job.run/队列，下一处真正的新函数为 Trial.create:469，问题是配置怎样变成具体 Trial、题目从哪里读入。本轮不预建 Trial.create 卡或提前展开加载器。


<a id="trial-create-reading"></a>

## 2026-11-12：从一份 TrialConfig 进入 Trial.create，明确本地读源码

用户确认查看 Trial 怎样根据 config 生成，随后询问本地 Harbor 是否为 0.25、是否无需联网。核对本地 /home/fredkeira/projects/harbor：HEAD 500af913，发布标签剥离提交 fdba28fc，HEAD 领先 123 提交，工作区干净；两者 pyproject 均写 0.25.0，因此用本地 git show 发布标签继续，不切换 checkout、不联网。

本轮建立 Trial.create 卡，从队列的调用现场接入，沿 source_trial=None、user_agent=None 和 hello-world 单步任务说明：解析 skills、_load_task 返回 Task 与材料记录、按 task.has_steps 选择具体实现、构造并返回 Trial，再由队列挂 hooks 和运行。完整源码保留在来源区，未提前建立加载器或构造器卡；未实际下载、安装或运行任何任务。


## 2026-11-12：Trial 类型选择与 bridge 的阅读边界

用户复述按 Harbor 工作步骤选择 multi/single，并询问 create_bridge。核对本地 v0.25.0 Task.has_steps:235 返回 bool(self.config.steps)，TaskConfig:877 的 steps 列表及校验不要求至少两项；因此非空显式步骤与 Agent 的对话/工具调用轮数要区分。当前 config.user_agent=None，_create_bridge:526–529 直接返回；用于额外 user_agent 交互的机制留白，不新增子卡。将条件旁注和最小职责补回 Trial.create。


## 2026-11-12：Bridge 连接谁、为什么当前 user_agent 为 None

用户追问 bridge 是否连接其他 Agent 以及 user_agent 为 None 的原因。核对本地发布版 BaseBridge 的类说明、UserAgentConfig 与 TrialConfig 字段、_init_user_agent 和 _run_agent_phase：user_agent 是可选模拟用户，与主 Agent 通过协议交互。当前示例只配置主 Agent，JobConfig 默认 None 被 JobPlan 传给 TrialConfig，所以 _create_bridge 直接返回。仅补定义与默认值来源，不展开 ACP 或桥接生命周期，不新增函数卡。


## 2026-11-12：下一张卡推荐 Trial._load_task

用户询问下一个函数应写什么。沿 Trial.create:474 的真实委派推荐 Trial._load_task:532–550，卡片围绕 config.task 来源 → TaskClient 取得目录 → Task(...) 对象 → 返回 Task 与 TaskDownloadResult 两项，接回父函数的配置检查和 Trial 类型选择。保持 hello-world 例子；不展开所有下载来源或桥接机制。仅核对本地发布标签，尚未创建本函数卡或运行任务。


## 2026-11-12：补 Job.create 返回之后到 Trial.create 的运行时交接

用户表示从之前的 Job.create 到现在 Trial.create 未连上。核对 _run_partition:704、760–762、Job.run 到 _run_trials_with_queue 及队列执行体，明确创建 Job 返回后先回调用方，再经 job.run 安排 Task，Task 内才 Trial.create。本轮在 Trial.create 卡加入这一调用现场和两个既有父卡链接，scope 第 5 项直接链接该来路；不新建额外函数卡或继续下钻 _load_task。


## 2026-11-12：在 3.2 加入真正可点击的跨步返回与进入位置

用户要求在 scope 指明回哪里、从哪行继续，避免仅在函数卡内解释。只修改 Step 012 的 3.2：将第 4 项至第 5 项之间的已读过渡标为 4A _run_partition 的 job.run 调用、4B Job.run 的队列等待、4C Task 内 Trial.create 调用；表格直接链接 Step 010/011 卡片锚点与 queue.py:201。图表同号且标为回看，不增加必读函数。3.1 保持不变，README 补快捷入口；当前仍是 Trial.create。


## 2026-11-12：3.2 的链接文字直接说明回看内容与返回点

用户要求在超链接文字中写明需要重新看哪个函数的哪部分，而不是只给函数名或“本步函数卡”。本轮保留原有编号、调用顺序和当前入口，只改 3.2 阅读表：链接标明“回看/进入/返回 + 函数/步骤 + 具体语句或段落”，返回列同样可点击；4A–4C 的跨步定位无需自行补链。Job.create 加入 return 段的精确锚点，不改变正文。用户所举“第八步”未被当作新增步骤，未重编号或扩大范围。


## 2026-11-12：3.2 阅读跳转只使用本地函数卡

用户明确 3.2 应只保留卡片跳转，不直接连接网络源码。本轮限定修改 Step 012 的 3.2：默认创建委派改链 Job.create 调用代码，移除队列调用位置的 GitHub 链接，_load_task/Trial.__init__/_init_agent 等未建卡位置保留名称与待建状态；已有卡片提供来路和返回点。任务配置前置改链已有例子，Step 013 交接只保留文字。源码出处仍在函数卡内部，未批量删除既有证据，也不为补齐链接预建未读卡片。3.1 和阅读顺序保持，Job.create 只加精确锚点。


<a id="complete-creation-chain-navigation"></a>

## 2026-11-12：补齐创建链的每个卡片入口和阅读上下文

用户反馈每张卡应说明上一处位置，自己能跟到 create/init/_init_trial_configs，但 _build_standard_trial_configs 与 JobPlan 仍从 scope 消失。检查确认两者仅藏在图或某行说明中，没有完整独立入口。按用户指定的实际调用链，补建此前已查看的短委派 _build_standard_trial_configs 卡；五张相邻卡统一就近来路、已有数据、下钻和返回说明。

只重写 3.2：创建链列成 1–5，明确 5→4→3→2 的逐层返回，6 为 create 交付对象，原 4A–4C 回看改成 7–9，后续 Trial/Agent/Environment 为 10–12。所有阅读跳转只链接本地卡片，未建卡位置不伪造链接。3.1 及后续范围不变，当前源代码阅读位置仍保留 Trial.create；这是导航与记录补齐，不表示新增掌握或已经开始后续函数。


## 2026-11-12：按用户要求回看 Job.run

用户明确要求查看 Job.run 代码。本轮从 03 完整调取前序函数卡到本步 02，保留原话、认识日期和未知，补上与已读 __init__ 字段的连接；通过本地 git show v0.25.0 再核对主干。当前只看 JobResult 初始化、await 队列执行、合并/统计/返回，不自动重读队列和 Trial。scope 将回看位置设为第 8 项，Trial.create 记录保留为随后接续。未启动任务或改动 03 快照。


## 2026-11-12：将聊天中的 Job.run 简写直接作为卡片主干

用户认可连续代码加短注释的呈现，追问为何函数卡不能这样写。本轮将本步调取的 Job.run 主体改为一段带方法签名、try/finally 的正常路径裁剪，删除重复的分段解释，明确省略范围；参数、记录细节留按需区，原话、未知和来源保留，完整旧卡归档。保留所有原锚点，scope 的队列跳转文字改为主干中的 [2]。Step 011 原卡及本步 03 均未改写，未执行源码。


## 2026-11-12：撤回刚才的 Job.run 简写

用户表示“算了还是回复吧”，按当前语境恢复刚才简写前的 Job.run 卡片；从完整快照恢复并重算相对链接，scope 的对应跳转文字一并还原。其他函数卡、阅读顺序和前序快照未改动；保留本次调整与撤回经过。
