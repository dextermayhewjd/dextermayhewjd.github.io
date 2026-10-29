# Step 016 · 理解形成过程

[本步范围](01-scope.md#reading-order) · [短期函数索引](02-short-term-memory/overview.md)

<a id="step016-start"></a>

## 范围确认：从生成接口转向结果如何被训练使用

前序讨论中，用户明确不需要继续讲解或测试 generate 的可等待要求。助手据既定路线推荐下一 Step 读 `BatchBuilder.convert`，把问题从“生成函数怎样接入、应该交回什么”转为“这些 Sample 怎样成为训练数据”。用户随后询问“这算是下一个step了吗？”，助手说明这是 Step 016 的候选范围，当时尚未创建。

本轮用户明确要求：

> 好的 那么继续吧 看一下这些结果到底是怎么整理成训练需要的数据的？

据此开始 Step 016，沿用主题 02，不再重复请求范围确认。创建 scope、convert 函数卡，调取已有 Sample 类卡；完整继承 Step 015 的 03 + 02，保留原话、来源、未知及前一步契约测试未运行的事实。取消 await 教学反例不代表全部接口测试通过。

<a id="first-field-assembly"></a>

## 首个观察点：按 Sample 组织，变成按字段组织

全局位置先接清：`RolloutManager._generate` 调用 `_get_rollout_data` 取得结果；后者在 567–568 行展开嵌套列表。默认正常路径中，385 行把 Sample 列表交给 `batch_builder.convert`，转换返回后再由 390 行的 `split_by_dp` 接续。不同配置的 rollout 执行方式保留区别，不把此前本地 worker 示例当作所有模式的统一实现。

第一次带读从 convert 的 278–288 行开始，先看一个可观察的结构变化：`samples[0].tokens` 放到 `train_data["tokens"][0]`，整数 `response_length` 汇入 `response_lengths` 列表。各字段按同一份 samples 的顺序对应。前置奖励处理和编号整理先给出用途，不沿文件顺序把所有前置机制都展开。

助手使用一个构造 Sample：token ID 为 `[101, 102, 201, 202]`，response_length 为 2，reward 为 0.75，status 为 COMPLETED，index 与 rollout_id 均为 7。使用默认转换、关闭奖励归一化，让第一轮只观察字段组织；这不是完整模型请求或典型训练配置的断言。

固定源码方法的隔离执行得到：tokens 为 `[[101, 102, 201, 202]]`，response_lengths 为 `[2]`，rewards 与 raw_reward 均为 `[0.75]`。完整方法还补出 loss_masks `[[1, 1]]`，并使原 Sample 的 loss_mask 从 None 变为 `[1, 1]`；后者记录为下一观察点的事实，不将它展开为用户已理解的结论。

首次解释强调：外层列表对应不同 Sample；内层 token 列表对应这一份 Sample 的序列。当前例子的总 token 数 4 与响应长度 2 分开看。下一处沿第二个阅读编号进入 292–304 行，说明 mask 与响应段的对齐。

## 证据与理解边界

- 静态证据绑定本地 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，工作区干净。本轮只查询到官方 main 为 `540ea919e45b8b929198abce008a103be9cfc779`，没有拉取或切换版本。
- 局部运行脚本抽取真实 Sample 类及固定源码方法执行；没有安装依赖、运行完整模块、Ray、模型或训练。输出与执行范围见 [结果 JSON](references/convert-example-output.json)。
- 本轮运行不补足 Step 015 未执行的插件契约测试，也不代表归一化、可选字段或训练分配已验证。
- 用户当前确认的是问题和阅读范围，尚未表达对 convert 实现的理解；函数卡如实保留这一状态。
- 本步的完整调用骨架与固定阅读编号保留在 scope，后续问题按同一张父函数卡逐段推进。不预生成完成总结，不处理 Hugo。

<a id="scope-step-links"></a>

## 整体位置图接上前序 Step

用户要求：

> 是否能够在这里的scope部分考虑一下更多的是把之前的几个步骤和内容串起来？
> 标注一下之前的 step多少处理了 整体位置中的哪些图 我觉得这样子会比较好？

原来的 3.1 把已有阅读压缩成“生成、评分、收集结果”，虽然能定位转换入口，却无法直接看出各步骤的归属。本轮核对 Step 010、011、012、013、015 的 scope，沿 Step 013 已认可的普通代码块图展开此前本地 worker 场景，在实际位置标注 Step 编号，并在图下补上可点击的回查入口。

关联保持三点：Step 012 是后台持续调度，Step 013 包含完成回调入队与上层主动领取，两侧通过同一个 output_queue 交接；Step 015 是回看 Step 010 中的生成接口，不新增运行阶段；Step 016 在本批结果回到 Manager 并展开为 Sample 列表后，处理训练数据转换。主题 01 作为具体 Agent 实现的回查入口，Trace Step 014 继续暂缓。

这是 scope 导航的补充，不代表新的源码阅读、个人掌握或运行验证。当前仍在第一观察点的字段组装；原有局部骨架、固定阅读编号、函数卡和 03 快照保持原状。

[修改后的整体位置](01-scope.md#overall-position) · [原 3.1 快照](references/scope-overall-position-before-step-links-2026-10-28.md)。

<a id="manager-generate-handoff"></a>

## 回看 Manager 主干，限定 begin 的阅读深度

用户要求：

> 好的 那么我们来看一下这里的rolloutmanager generate吧
> 是否需要看begin 还是你觉得这里有你觉得最好的链接和讲述方式？

本轮在同一 Step 内回看上层，先区分 public generate:317–333 与 _generate:335–390。前者登记本轮编号并在 328 行调用后者；当前数据交接集中在 _generate 的正常路径：取得 Sample 列表 → begin → convert → split_by_dp。具体 Agent generate 仍在前面的 rollout 执行链内部，不与 Manager 的批次编排混为同一职责。

begin 回查到当前 raw_ref=None 分支即可：50–53 行清空 batch_id 与 _plan，返回 None；_generate:383 的提前返回条件不成立，于是进入 385 的 convert。完整 begin 还会持久化、核对选择与转换计划，并在已有 ready 结果时返回分配结果。本轮纠正此前“检查可复用的转换”过于笼统的定位，保留该分支用途，不扩展 straw 和恢复专题。

父函数卡还标明同名 data 的变化：取回时是 Sample 列表，convert 后是字段字典，最终由 split_by_dp 返回每个 DP 分片对应的包装引用列表。末尾封装只据 497–530 行定位；没有执行 Manager、Ray 或新测试，之前的 convert 局部运行不作为整个调用链的运行证据。

scope 增加调用方回查入口，原有四个阅读编号保留；新卡只给 _generate，public generate 和 begin 的短片段作为其配套说明。用户尚未对该机制给出直接解释，未登记新的掌握状态。

[调用方回查入口](01-scope.md#manager-handoff) · [RolloutManager._generate 卡片](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager._generate.md)。

<a id="return-to-data-batch-builder"></a>

## 按用户纠正回到 data 目录的 BatchBuilder

用户先对阅读位置提出疑问：

> 好的 那么 我们来看一下看一下吧怎么就到ray的部分了 我服了 不是rollout manager吗

随后明确纠正本轮方向：

> 不用不用 就看batch builder那里吧 不应该是data那里吗？

据此直接回到 slime/data/batch_builder.py 中的 BatchBuilder.convert。此前为了说明上层交接展开了 RolloutManager 与 Ray 返回封装，使当前位置显得偏离原问题；Manager 确实定义在 slime/ray/rollout.py，但本步的数据转换核心仍在 data 目录。

scope 的第二部分恢复直接指向 convert，局部骨架先显示数据转换；Manager / begin 的已有说明移入折叠背景，原四个阅读编号保留。已有卡片和来源不删除，不继续展开 Ray、Manager 或 begin。当前仍围绕 Sample 到 train_data 的字段变化，尚无用户对转换机制的新表述；无新增运行。

<a id="convert-entry-memory-object"></a>

## convert、可选替换函数与短期卡片对象

用户问当前 scope 的核心骨架是否正确，并将 convert 与“convert samples to train data function”联系起来，询问是否为它建立 short-term memory。完整原话保存在 [convert 卡片](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md)。

助手核对当前骨架与 batch_builder.py:256–266：骨架按真实执行顺序展示自定义替换分支及默认转换主线，是教学裁剪而非完整源码。为减少归属歧义，补上 def convert(self, samples) 的方法边界。custom_convert_samples_to_train_data_func 在 42–46 行根据配置加载；若非 None，260–261 行立即返回其结果，否则继续默认实现。

当前已经存在 BatchBuilder.convert 的父函数卡，因此沿用它，补充入口分支和本轮原话；没有创建重复卡片，也不为未选定的自定义实现预建函数记忆。新的解释尚待用户反馈，未记录为掌握，无新增运行或范围扩展。

<a id="default-reward-to-fields"></a>

## 沿默认转换把已有奖励接到字段字典

用户要求：

> 好的 那么就按照按照这个来看一下这里到底是如何转换的吧

本轮继续在 data/batch_builder.py 的 convert 默认分支内阅读，不转向 Manager 或 Ray。先把 263 行 _post_process_rewards 的输入输出接清，再回到已有的 278–288 行字段组装。

沿用已有构造例子：Sample.reward=0.75，未配置自定义奖励后处理，reward_key=None、rewards_normalization=False。方法在 211 行提取已有分数，在 254 行返回 raw_rewards, raw_rewards，因此父函数中 raw_rewards 和 rewards 都为 [0.75]，本分支是同一列表的两个返回位置。前者随后写入 train_data["raw_reward"]，后者写入 train_data["rewards"]。此处使用已有评分；没有再调用 reward model，也不改写本例的 Sample.reward。

265–266 行负责检查奖励数量与样本数量一致；本例已有 rollout_id=7，准备为 rollout_ids=[7] 后进入 train_data 字典。缺号补齐、自定义后处理和完整归一化内部仍留作按需回查。本轮的奖励解释仅用于接清字段输入，不改动 scope 原有四个阅读编号。

输出数值复用本步已有的固定源码隔离运行结果，本轮补充静态路径解释，没有重跑实验或创建新函数卡。用户本轮表达的是继续阅读，尚未对上述机制给出直接反馈；下一处实质性变化仍是 loss_mask 的生成及对齐。

<a id="batch-config-and-reward-boundary"></a>

## 初步分清两条转换路径，再校准配置归属与职责

用户尝试概括“有自己的转换 function，否则调用 post process rewards，再根据后训练算法生成数据结构”，并询问 `_post_process_rewards` 是否需要单独看。完整原话保存于 [convert 父函数卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md)。

这一表述已区分自定义转换与默认路径，仍有两个需要校准的边界。第一，42–46 行根据 args.custom_convert_samples_to_train_data_path 为 BatchBuilder 加载函数，260–261 行一次传入整批 samples；这不是每份 Sample 像生成阶段的 generate_function_path 那样自行选择转换函数。第二，_post_process_rewards 返回两项奖励结果，算法与归一化配置影响其数值处理；后半段 convert 才组装完整 train_data 字典。

针对当前问题，助手推荐下一小段单独读同一文件中的 `_post_process_rewards:207–254`，仍留在 Step 016。建议先限定为“已有 reward 如何取出 → 自定义后处理／内置处理／原样返回怎样选择 → 两项结果如何回到 convert:263”，再按问题进入组内统计。它具有独立的分支机制，适合随后建立方法卡；父卡继续保留调用与返回交接。当前只记录推荐和边界校准，没有预建新的子函数卡、讲完归一化内部或把用户初步理解标为完整掌握，也没有新增运行。

<a id="post-process-algorithm-outputs"></a>

## 按算法、开关和返回值直接解释奖励后处理

用户进一步将 sample group 中的 index、reward 与 GRPO、GSPO、CISPO、REINFORCE++ 联系起来，要求直接翻译函数逻辑，并比较选择不同算法时返回的 rewards。完整原话见 [_post_process_rewards 方法卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder._post_process_rewards.md)。本轮据此正式单独展开该方法，仍在 Step 016。

助手按源码给出五个动作：自定义处理优先返回；提取已有分数；在支持的算法和归一化开关下按独立 rollout 去重并分组；去均值及条件标准化；按原 Sample 的顺序与数量映射回结果。以同组两次独立 rollout 的 [1, 3] 为例，分别得到原样 [1, 3]、去均值 [-1, 1]、标准化约 [-0.7071, 0.7071]。GRPO、GSPO、CISPO 在这里共用规则；源码第四种是精确的 reinforce_plus_plus_baseline，它只去均值。

补清 index 和 reward 的关系：group_index 用于组内比较，rollout_id 用于避免同一次 rollout 的多个片段重复参与统计，index 只在缺少 rollout_id 时回退使用。以归属 [10, 10, 20]、原始分数 [1, 1, 3] 为例，统计使用 [1, 3]，去均值后映射回 [-1, -1, 1]。最终只返回两个按 Sample 对齐的奖励列表，不返回 index 表。

静态核对了 tests/test_grouped_rewards.py 的既有案例，未运行 pytest。标准差约定查证 PyTorch 官方文档，数值以标准库算术核对，不称为 PyTorch 归一化分支运行；此前关闭归一化的局部运行证据仍保留原范围。子卡包含单 rollout 组为零、标识一致性及旧输入分组回退等边界。用户尚未对本轮校准给出反馈，未登记为完整掌握。

<a id="return-from-rewards-to-assembly"></a>

## 奖励后处理获大致理解反馈，返回父函数看字段拼装

用户明确要求“按照这个方式写入”，并表示“我差不多理解了”，随后提出回到上一步看后续拼装。完整原话保存于两张相关函数卡。记录奖励后处理的真实反馈，同时区分它与尚待反馈的字段拼装；不把继续阅读当作整个 Step 已完成。

本轮回到同一 Step 的 BatchBuilder.convert，而不是返回上一编号 Step。沿用子卡同组两次 rollout 的原始分数 [1, 3] 与去均值结果 [-1, 1]，补充两个不同长度的 token 列表、response_length、sample index 与 rollout_id。在[父函数卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#rewards-to-field-lists)对照 263–288 行说明：接住奖励并检查数量 → 准备 rollout_ids → 从 Sample 按字段收集列表。

核心关系是“同一列表下标对应同一份输入 Sample”。tokens 与 response_length 直接收集，rewards 与 raw_reward 分别使用已准备的两项奖励，truncated 根据状态生成 0/1 标记，sample_indices 与 rollout_ids 保留不同身份。这个阶段不再评分，不补齐 token 长度，不转 Tensor；展示的是 288 行的中间字典，后续仍要添加 mask 等字段。

下一观察点保持在 convert 内部的 loss_mask：缺失时怎样补、长度为何与 response_length 对齐。此次没有展开 mask 循环或进入 Ray、DP 分发。两份 Sample 的新对照为静态推导；没有重跑旧的 0.75 单样本实验、运行归一化测试或改变源码。固定源码 HEAD 与官方查询结果均未变化。

<a id="field-assembly-understood-next-mask"></a>

## 基础字段已能概括，定位 convert 的剩余重点

用户明确表示“好的我理解了”，将刚才的拼装概括为 token、长度、reward 等对应内容组成的简单字典，并询问这个函数还需要看哪些部分。完整原话补入 convert 父卡。助手确认该理解适用于 278–288 行基础字段组装，尚不能替代后半段的训练 mask 与条件数据处理。

本轮只定位后续阅读入口：优先 292–304，理解哪些响应 token 参与 loss、缺失 mask 与 remove_sample 如何处理；随后 316–321，理解为何先计算整个 rollout 的 mask 总和，再为所属 Sample 携带相同总数；最后简看 335–337 的 rollout_log_probs 和 443 行返回。323–329 的 raw_reward 元数据覆盖、SC/top-p、routing replay、多模态和 teacher_log_probs 等先保留条件用途，不逐个下钻。

下一小段建议仍在同一 Step、同一 convert 父卡内看 292–304。当前没有新建函数卡、展开后续完整机制或标记本步完成。本轮只读复核剩余源码，版本与工作区未变化，没有新增运行。

<a id="response-mask-brief-reading"></a>

## 将 response 的初步理解接到 mask，后续分支简读

用户同意简单看 loss_mask，认为它一般针对 response 构建，同时明确反馈下面的 if/else 太多。完整原话保存在 [convert 父卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#response-loss-mask)。本轮保留既有 Step 与四个阅读编号，在父卡内增加连续源码和小例子，不另拆函数卡。

助手核对 292–304 行后补清：mask 长度是 response_length 个 token，不是 response 字符串的字符数，也不是完整 tokens 的长度；已有合法 mask 保留，缺失时补全 1，长度不符触发断言，remove_sample 为 True 时改成全 0。处理后的 mask 既保存在 Sample 上，也按原顺序收进 train_data。清零在本段不会删除 Sample、tokens 或 reward。

承接两份响应长度 2、3 的构造样本，缺失 mask 且均不移除时得到 [[1,1],[1,1,1]]；把第二份标记移除的独立变体得到全零 mask。这些是静态推导，没有新增运行。之前的单样本运行只作为原范围内的证据保留。

后续只给用途概览：rollout_mask_sums 汇总同一 rollout 的有效响应 token 数；rollout_log_probs 携带已有生成信息；其他配置分支按需补字段或验证，再返回字典。具体归约、策略修正和复杂配置内部不在本轮展开。用户对 mask 与 response 的关联已有表述，具体规则的校准仍待反馈；没有把简读记为整个函数完成。

<a id="after-mask-next-function"></a>

## mask 简读之后，定位下一处真实函数交接

用户问：

> 这里是对于mask简单的解释 那么继续吧
> 我们还需要看什么会比较好呢？
> 这里解决完了之后应该看那些内容呢？ function什么的

本轮在 convert 父卡收拢生成信息与返回：335–337 行将已有 rollout_log_probs 放入字典，443 行返回 train_data。保留 rollout_mask_sums 与其他可选字段的用途定位，不把逐个深入所有 if 当作继续阅读的前置。用户本次请求是继续与选择入口，不能据此补写对每个 mask 规则的掌握。

下一函数推荐为同一文件的 BatchBuilder.split_by_dp:445，理由是调用方 RolloutManager._generate 在 385 行接回 convert 的字典，390 行马上把它交给 split_by_dp。首轮范围只看输入、DP rank 分配与返回引用，build_dp_schedule 的分配算法、Ray 传输和 straw 持久化先保留黑箱；不另开一整步学习并行调度。函数返回的是各 rank 的包装数据引用，不能把它说成仅返回普通字典或宣称由 convert 直接调用。

这段交接接清以后，仍按已确认计划以 train.py::train:13 为下一阶段核心，理解生成、训练、权重同步与评估的闭环。该阶段尚未开启，本轮没有创建新 Step 或 split_by_dp 方法卡，也没有运行训练或改动源码。

<a id="split-by-dp-first-pass"></a>

## 用户确认 split_by_dp，建立方法卡并简读字段分配

用户明确要求看 split_by_dp、确认 DP 是否指 Data Parallel，并要求短期记忆卡和简单带读。用户同时明确“我理解了刚才是把对应的训练字段都整理了”。完整原话见新建的 [split_by_dp 方法卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md)。此前只是推荐，本轮据此正式展开；仍在 Step 016，保留原四个阅读编号，追加第五项 DP 交接。

助手确认 DP 指数据并行，先选择 object-store 正常路径。输入承接 convert 的两份样本字典，完整 token 长度是 [3,4]，与响应长度 [2,3] 区分。build_dp_schedule 仅按接口理解为生成分配和小批次安排，不深入算法。

为展示实际字段选择，假设调度返回 partitions=[[0],[1]]。这两个数是输入列表位置，不是 sample index 或 rollout ID；各字段用同一组位置取出，所以 rank 0 保留第一份样本的配套数据，rank 1 保留第二份。raw_reward 和 total_lengths 保留全局数组用于指标，schedule 随各 rank 的数据携带。CPU 张量化的效果与返回 Box(ObjectRef) 的结构已核对，避免把输出误说成普通字典列表或即时训练。

本轮为构造示例与静态源码核对，假设的分配表不是 build_dp_schedule 的运行输出。没有执行 Ray、PyTorch 转换或训练，没有建立调度、传输辅助函数卡。方法卡已保存输入、输出形状、三段源码、少量必要分支和未知，用户对本方法机制的理解仍待反馈。

<a id="build-dp-schedule-reading-depth"></a>

## 是否需要继续看 build_dp_schedule：建议只展开调度主干

用户问：

> 我知道
> 那么这里是否需要简单理解一下这里关于build dp schedule部分的方法呢？
> 是否需要具体考虑一下呢？

助手核对 slime/utils/dp_schedule.py:82–209 后，建议读主干，以补上此前假设的 partitions 到底如何产生。split_by_dp 按方案选择并交付实际字段；build_dp_schedule 根据长度、rollout 归属和批次/并行配置生成索引方案，不处理真实 token 张量、发布引用或执行训练。

推荐按四个动作理解：按 rollout 组织训练步；每步把样本组成 micro-batch；检查或调整小批次数量，使各 rank 的安排满足对齐要求；再分给各 DP rank，构造返回索引。源码采用先组成小批次、再分配 rank 的顺序。相同 rollout 的片段留在同一训练步，不表示一定留在同一 rank。

建议短期记录只保留输入、这四个动作、四项返回值及回到 split_by_dp 后的用途。重点是 partitions 的全局样本位置与 micro_batch_indices 的 rank 内位置；具体装箱、FLOPs 估算、负载均衡算法以及 CP/VPP 细节仍作为黑箱。若继续具体阅读，可从 130–150 行的 rollout 到训练步开始。

本轮保存范围建议与主干概览，没有新建 build_dp_schedule 函数卡、开启新 Step 或执行调度实验。此前两 rank 的假设例子仍保留为静态示意，未改写成真实运行结果。

<a id="build-dp-schedule-concrete-handoff"></a>

## 用具体输入与输出接清 build_dp_schedule → split_by_dp

用户在上一轮范围建议后明确表示仍不理解，要求给出简单理解所需的内容。原话保存于新建的 [build_dp_schedule 函数卡](02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md)。因此本轮展开这个子调用，继续属于 Step 016 的第五个阅读入口，不再停留在建议或另开 Step。

助手沿用父卡的两份样本：完整长度 [3,4]、rollout_ids=[10,20]，补齐 dp_size=2、global_batch_size=2、micro_batch_size=1、关闭动态分批与负载均衡的具体配置。先按 rollout 组成一个训练步，再得到两个各含一份样本的小批次，最后各分给一个 rank。固定配置的实际返回为 partitions=[[0],[1]]、micro_batch_indices=[[[0]],[[0]]]、num_microbatches=[1]、global_batch_sizes=[2]。

本轮重点区分整批位置和 rank 内位置：rank 1 从整批位置 1 取样本，但取回后该样本在自己的列表中位于 0。父函数依据 partitions 选择配套字段，把本 rank 的 micro_batch_indices 与两个数量列表一起交付。调度函数本身只生成安排；父函数的字段选择与传输仍按源码静态说明。

运行证据是 [原始函数体隔离脚本](references/run-dp-schedule-example.py)及[输出](references/dp-schedule-example-output.json)：通过 AST 原样提取 build_dp_schedule 和 _pack_step_into_mbs，未改写两者实现；只执行固定大小、不启用负载均衡的路径。未执行完整模块导入、split_by_dp、Ray、张量化或训练，未测试其他调度分支。此前假设安排的历史叙述保留，本轮新增固定配置下相同结果的独立证据。

scope、父卡与函数索引已接入子卡，原有五个阅读编号与完整骨架保留。动态装箱、FLOPs 估算、负载均衡和 CP/VPP 机制继续留白；用户对本轮解释尚未反馈，不标记为已掌握或 Step 完成。

<a id="split-by-dp-concrete-data-first"></a>

## 调度例子仍未解决困惑，回到实际字段的分配前后

用户明确表示仍不理解，并询问是否有更容易理解的方式、已有 skill reference 是否能帮助。原话补入 split_by_dp 父卡。助手认为上一轮过早集中于四项调度结果，可能使函数目的与真实数据变化被遮住；这是对讲法的判断，不把它写成已确定的用户认知原因。

本轮查阅并复用两份已有方法：

- [BaseAdapter._translate 样例](../../../../../../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)：先给同一场景的真实字段与前后对应，再解释转换；这里复用展示方式，不复用协议转换业务。
- [先核心、后补前置](../../../../../../../.agents/skills/repo-reading-order/references/inside-out-method.md)：优先看直接回答当前问题的动作，再回查必要输入。本轮从 batch_builder.py:520 的实际字段选择读起，需要时回查 457 行的调度表来源。

同时参考了 [BaseAdapter._run_turn 的父函数阶段组织](../../../../../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md)：保留整个函数与子函数交接，不继续为局部取值增加新卡片。现有 scope 骨架、编号、完整输入和调度子卡都保留。

父卡新增同一两样本例子的 tokens / rewards 投影：输入为两条 token 序列与 [-1,1]；rank 0 的 value 取第一条序列与 -1，rank 1 取第二条与 1。这里只展示按字段选择后、张量化前的局部 value；完整函数仍附上安排并返回包装数据引用。该对照来自已有场景与静态源码核对，本轮没有重新运行调度、Ray 或训练。

目前先强调一份样本的 tokens 和 reward 配对进入同一 rank。micro-batch 与全局/本地下标的详细区别暂作为后续回查，不删除此前材料，也不将用户的再次求助记为已掌握。本轮只在同一 Step 内补展示入口和保存反馈，未建立新 Step 或新通用规则。

<a id="split-by-dp-purpose-and-batching"></a>

## 从长度相近的假设，回到 split_by_dp 的目的与两层决策

用户继续追问 split_by_dp 解决什么问题，提出“两个 sample 或 batch 内部 token 长度差不多才放进同一 batch”的理解，并要求从工程阅读与学习文档组织的角度建立核心模型。完整原话保存于父卡。本轮明确暴露的是对函数目的及分组依据的疑问，不能只继续展示索引或字段结果。

助手的校准是：全体样本的训练字段字典还需要变为各 DP rank 的样本分工、局部数据与小批次安排。split_by_dp 委托 build_dp_schedule 定计划，然后按计划取出字段、附上安排并返回数据引用。计划内部先决定哪些样本组成 micro-batch，再决定把这些小批次分给哪个 rank。静态路径按数量切分；动态且 balance_by_flops=False 时检查总 token 预算，并不要求样本长度相近。balance_data 另外控制是否按预计 FLOPs 尝试平衡 rank 的负载。

为解释长度规则，使用一个独立的静态推导例子，不替换卡片原有的两样本运行记录：四个样本 A、B、C、D 的长度依次是 [8,8,2,2]，各属不同 rollout，global_batch_size=4，dp_size=2，cp_size=vpp_size=1，microbatch_group_size_per_vp_stage=1，use_dynamic_batch_size=True、max_tokens_per_gpu=10、balance_by_flops=False、balance_data=False。

```text
一次全局训练步中的四份样本：A(8)、B(8)、C(2)、D(2)

按 token 总预算组成小批次：
  小批次 0：A(8) + C(2) = 10 tokens
  小批次 1：B(8) + D(2) = 10 tokens

把已经组成的小批次分给 DP rank：
  rank 0 ← 小批次 0
  rank 1 ← 小批次 1
```

first_fit_pack 按输入顺序把 A 放入第一个箱，B 放入第二个箱，C 填满第一个箱，D 填满第二个箱。两个小批次已经满足 dp_size=2 的对齐，无需再拆；关闭负载均衡时依次分给两个 rank。长、短样本在同一小批次中，说明这里的条件是总预算，而非相近长度。本例的总 token 数恰好相等，不代表所有调度结果都如此；没有在本轮运行这个动态例子或相关 pytest。

从工程角度只优先检查三个交接：453–463 行的长度和调度调用；498–523 行的字段选择及安排附加；527–530 行的引用返回。正确性的观察点是保留在完整训练步里的样本各分配一次、配套字段不串位、同一步各 rank 的小批次数满足共同安排；长度预算与 FLOPs 均衡属于具体配置下的资源策略。tests/test_dp_schedule.py:54–90 和 145–190 用于静态核对这些约束，不记为已运行测试。

文档组织建议继续沿用现有统一栏目：使用场合先讲全局数据为什么还需要各 rank 的分工；具体内容和心智模型保留“定计划 → 取字段 → 交付”三个动作；输入输出用同一完整例子逐段展示，每段紧邻真实源码；具体索引结构、配置分支与完整证据放后面按需回查。区分目的、分批策略和代码表达后再展开细节，避免每次解释都在开头叠加更多数组。BaseAdapter._run_turn 的分阶段父卡和 BaseAdapter._translate 的同场景前后对照继续作为已有参考，不新造一套记录格式。

本轮已校正两张卡片的目的与概念说明，保留原场景、原话、完整骨架和证据；整体大幅重排仍属于上述组织建议。用户对校准和组织方式尚未反馈，未将其登记为掌握，也未推进 Step。

<a id="split-by-dp-guided-rank-loop"></a>

## 2026-10-29 · 按实际主干带读，跟踪一次 rank 循环

用户再次要求带读 split_by_dp，并明确表示仍觉混乱，原话见父卡。本轮直接沿 object-store 路径讲解，继续使用此前两份样本的完整输入和已核对的分配表；不再讨论如何设计文档或另开调度专题。

讲解先定位 convert 返回的 data，再串起“统计长度、取得分配表 → 按 rank 取配套字段 → 附安排并返回引用”。本轮重点是 498–523 行中 rank、partition、value 的关系：第二轮 rank=1 表示接收方编号，partition=[1] 指向原 data 的第二份样本，value 是为这个接收方新建的字典。tokens 和 rewards 使用同一下标取出；列表推导保留外层样本列表，原输入样本不会被取走或删除。完整字段及全局统计字段的例外继续保留在父卡。

build_dp_schedule 的另外三项返回值先作为随数据交付的小批次安排保留，不在本轮展开内部组装；最终 result 保存各 rank 对应的包装引用，调用方之后把它们交给训练消费。没有在此处执行训练、传输实测或新增调度运行。用户尚未给出对这次带读的理解反馈，仍保留此前未知。

<a id="build-dp-schedule-parallel-config"></a>

## 2026-10-29 · 进入调度子函数前，补清四项训练约束

用户初步概括“先拿到总token，然后使用build dp schedule”，明确询问 dp_size、cp_size、vpp_size、mb_group 的含义，并提出需要函数短期记录。完整原话补入已有 build_dp_schedule 卡。本轮直接沿用这张卡，在输入输出栏增加准备阶段，不重复新建同名卡或另开 Step。

先校准 total_lengths：[3,4] 是两份样本各自的完整 token 长度，不是求和后的 7。接着区分数据并行副本数、上下文序列分工数、虚拟流水线模型片段数，以及每个虚拟阶段的微批组大小。mb_group 以小批次为单位，micro_batch_size 以样本为单位；不能把这两者都理解为一个 batch 中的样本数。

本轮只展开源码 112–125 的两项约束：动态路径的 max_per_bin=max_tokens_per_gpu*cp_size，及 align_to=dp_size*(mb_group if vpp_size>1 else 1)。前者是 token 预算，后者是总小批次数的整除基数；vpp_size 本身没有直接乘进去。dp_size=2、vpp_size=2、mb_group=2 时要求总小批次数是 4 的倍数，使每个 rank 的小批次数是 2 的倍数。该约束属于当前 Slime 实现，不将其推广为所有 Megatron 调度的通用要求。

配置来源只读定位：megatron_utils/actor.py:107–119 取得训练配置；train_actor.py:123–126 发送给 RolloutManager；rollout.py:572–573 写入 BatchBuilder。模块没有在这里创建并行进程、划分实际 CP 张量或执行流水线。概念定义对照 NVIDIA 官方并行指南、parallel_state 和 ModelParallelConfig 文档，来源已写进函数卡。

本轮继续使用原来的静态两样本主例，dp_size=2，其余三项为 1；先看普通 DP 约束即可。配置变化的小例子仅作算术说明，未运行 CP/VPP 或新增调度测试。tests/test_dp_schedule.py:227–249 仅核对其已有 VPP 对齐断言，没有执行该测试。后续仍沿同一子卡接回按 rollout 组织训练步、小批次组织、分配与返回；当前只记录新增疑问和助手说明，不将其记为已掌握。

<a id="build-dp-schedule-independent-card"></a>

## 2026-10-29 · 明确将 build_dp_schedule 单独作为函数短期记忆

用户明确要求单独创建 build_dp_schedule 的 short-term memory。该函数已有独立文件，本轮沿用它并明确卡片定位，避免生成两份同名记录；scope、短期索引与步骤 README 均可直接进入完整函数卡。

卡片保留输入与配置含义、调度主干、原两样本例子、四项返回值及回到 split_by_dp 的位置，也保留原话、未知和局部运行证据。本轮确认的是记录单位，不是新增阅读步骤或已掌握证明；未新增运行、改动源码或扩大调度算法范围。

<a id="parallelism-primer-and-microbatch-groups"></a>

## 2026-10-29 · 用样本与模型的具体分工补齐概念入门

用户尝试把 DP 理解为不同样本并行进入的消息数量、CP 理解为同一序列的 token 合作、VPP 理解为模型的虚拟片段，但明确表示 mb_group 尚不清楚，概念到实现的关系依然模糊。完整原话保存在 build_dp_schedule 卡片。前一轮定义表没有解决这次困惑，不据此登记为已经掌握四项配置。

本轮继续使用 repo-reading-short-term-memory 的职责分工：函数卡保留源码、输入输出、用户原话与未知；[概念入门](references/parallelism-primer.md)保存为理解当前函数所需的背景，并由 scope 的第五入口和卡片配置阶段直接链接。沿用已有的先补最小前置、同一例子展示数据变化的方法，不开启新 Step 或并行训练课程。

讲解先以 8 份独立 rollout 样本、micro_batch_size=2 得到 4 个小批次；dp_size=2 且关闭负载均衡时，副本 0 得 M0、M2，副本 1 得 M1、M3，校准 dp_size 数的是副本。随后放大一个副本，用 8 层模型、两个物理阶段引入 PP，再说明 VPP=2 表示每个物理阶段有两个虚拟片段；mb_group=2 表示同一虚拟阶段按两个小批次一组安排任务。前向示意省略等待、通信和反向传播，没有把局部任务顺序当作完整执行时间线。

CP 单独用一条长序列的分工解释，8 样本主例仍使用 cp_size=1。最终接回 Slime 的公式：动态路径的 CP 倍数影响 token 预算；dp_size 与启用 VPP 后的 mb_group 影响总小批次数的对齐。本函数按训练端给出的配置排数据，不在这里创建这些并行机制。

术语对照 NVIDIA 官方文档；具体分批、对齐与分配对照本地 18868a79 的 dp_schedule.py:55–209。新例子为静态推导，没有执行它的调度或多卡训练；此前两样本的局部运行证据单独保留。用户尚未反馈本轮讲法是否解决困惑，后续仍从同一函数卡接续。

<a id="parallelism-baseline-and-parameter-progression"></a>

## 2026-10-29 · 从同一个原始场景比较参数变化

用户认可上一轮例子，但要求考虑开头是否应从原始例子理解，并从认知与工程角度安排参数和具体内容。原话保存于 build_dp_schedule 卡片。本轮按“先有无并行拆分的比较基准，再逐步改变配置”理解这项要求；不把它写成用户已经明确选择了某组参数或已经掌握各机制。

助手判断，原说明直接进入 dp_size=2、PP=2 等配置，缺少改变前的完整场景，使读者还需要自己补出基准。因此保留已有 8 份样本的例子，在开头加入一个副本、一张 GPU、完整 8 层模型、每次处理 2 份样本的正常过程；先看到对象与运行方式，再为数量引入参数名。A–H、每份 4 个 token、模型层号和小批次标签保持稳定。

参数选择是为了使变化可见：8 份样本按 2 份组成 4 个小批次，分给两个副本后各得 2 个，又能说明 mb_group=2；8 层模型便于画出两个物理阶段各含两个虚拟片段。长度统一、关闭动态分批与负载均衡，使本轮专注于分工与数量单位。这是教学用的控制场景，不是集群性能建议。

递进为：原始基准 → 两个 DP 副本 → 副本内 PP → VPP 及其配套微批组；CP 从 DP 场景单独对照。每段展示相对于哪个场景的配置变化、数据或模型归属的变化。源代码存在配置联动：未启用 VPP 时 Slime 给调度器的 mb_group 为 1，启用后取训练模型配置；本例选 2，明确记录两个配置项一起变化，而不声称每次严格只改一行。PP 不是 build_dp_schedule 的直接输入；静态分批时仅改变 CP 不改变该函数的小批次或 DP 分配，这两个边界保留。

认知依据与设计判断分开：IES 的学习与教学指南支持连接具体与抽象表达、结合图示与文字；将这些原则落实为固定场景、改变前后对照和延后完整配置表，是助手针对当前问题的设计。没有为本例进行教学效果实验。通用 skill 不修改，背景讲解继续放 references，函数卡保存原话与链接，scope 的完整骨架和本步范围继续沿用。

本轮静态复核 Slime 18868a79 的 dp_schedule.py:112–125、168–209 与 actor.py:107–119，并核对官方微批组定义；未新增调度运行或多卡训练。用户认可上一轮示例不等于确认本轮改排已有效，当前仍停留在同一函数的概念准备。

<a id="batch-size-before-microbatch"></a>

## 2026-10-29 · 起点再校准：用户知道 batch size，尚不理解小批次

用户进一步指出，开头应连小批次概念都不包含，自己学习深度学习时只知道 batch size。完整原话保存在函数卡。这是明确的已知边界，不应因前面已经给过 micro-batch 解释就视为掌握。

上一轮虽增加了一个副本的原始场景，但开头仍把 8 份样本分成四组，每次算 2 份，实际预设了用户尚不理解的分次计算。修正后的入门第 0 节只展示 batch size=8、整批交给一张 GPU 上的完整模型、计算 loss 并进行一次参数更新。这里先假设整批能放入显存，不出现分组图或并行配置表。

第 1 节保留为后续展开：只有提出整批放不进显存、一次只能算 2 份时，才给四组数据图，并命名 micro-batch。为了保持一次更新共同使用这 8 份数据，说明需要累积梯度；归一化实现留待后续，不将其预设为已知，不宣称已验证数值等价。后面的 DP/PP/VPP/CP 图继续保留。

完整参数表相应修正：原始基准按源码表示为 micro_batch_size=8、dp_size=1、其余规模为 1，每个 rank 有 1 组；下一行才变为 micro_batch_size=2、每个 rank 有 4 组。表位于背景概念之后，不反向要求读者在第 0 节先掌握这些术语。Slime 的 global_batch_size 按 rollout 数计，本例各样本属于独立 rollout，因此与 8 份样本一致。

本轮只保存前置边界与修正讲法，更新当前入口；未新增 Step、未改 Slime 源码、未运行梯度累积或训练。用户对新起点及后续解释的反馈仍待补。

<a id="baseline-inline-in-function-card"></a>

## 2026-10-29 · 基础版本直接显示在函数卡，后续在同一处逐次构建

用户先反馈本地找不到具体内容。助手核实：基础例子已存在于 references/parallelism-primer.md，第 7 行起是 batch size=8 的原始场景，但 build_dp_schedule 卡片只在第 41 行放了跳转链接。文件存在不等于当前阅读位置已经直接显示内容，这也是前一轮保存方式需要调整之处。

用户进一步明确要求在当前 Markdown 直接显示最基础版本，并在这个基础上一点点构建。完整原话保存在函数卡。本轮把一整批 A–H 样本交给一个完整模型、计算 loss、反向传播并更新一次参数的示意直接写进“本场景的输入与输出”，默认显示。它是训练流程的教学基准，尚未调用 build_dp_schedule，也不被记成运行结果。

函数总览与已有配置、调度过程、两样本运行记录折叠保留；原话、未知与源码证据不删除。后续递进只在一个折叠表中定位：容量限制后才引入分次计算，多个副本后才引入 DP，再根据问题展开模型分布与序列协作。当前阅读停点仍是基础版本，不预填掌握状态。

scope、步骤 README、函数索引与唯一进度入口改为直达卡片的 batch-size-baseline 锚点。原 reference 继续提供扩展对照，基础阅读无需先离开函数卡。没有新增 Step、源码改动、训练运行或 Hugo 更新。

<a id="microbatch-to-dp-examples"></a>

## 2026-10-29 · 从单卡 micro-batch 到两个 DP 副本，标题标配置、段末看同一批数据

用户明确表示已理解 micro-batch 用于处理整批一次放不下的情况，继续询问 DP 是否相当于从一张 GPU 变为两张，并建议在标题标数量、每次改变后给出 examples。完整原话保存于 build_dp_schedule 卡；此前“小批次尚不理解”的当前状态随这次明确反馈更新，历史原话和形成过程保留。

本轮先校准分组对象：将一批 A–H 分成 [A,B] 等组，每份样本仍然完整；不能把这一步理解为单份样本被切成多个更小样本。显存限制是当前教学场景中引入 micro-batch 的动机，不把它写成唯一用途或任何显存不足都必须采用的办法。

DP 的回答限定在每张 GPU 放一份完整模型、只采用数据并行的例子中：DP=2 对应两张 GPU，各自承担一部分数据并通过梯度同步共同更新。DP 的计数对象是副本，一般不能等同于总设备数。图表达逻辑分工，具体梯度同步时机未展开。

三个可见标题现在分别标注 GPU=1/batch size=8，GPU=1/micro_batch_size=2，以及 GPU=2/DP=2/micro_batch_size=2。每段末尾保留同一批 A–H 的 Example，最终用表对照一次更新总共 8 份样本、单次每卡计算数量与每卡计算组数。标题只显示当前已引入的参数，未展开的并行配置不提前塞入标题；例子写在同一张卡中，不新建 examples 目录。

两个副本按当前 Slime 静态分批、关闭负载均衡的规则分得 M0/M2 与 M1/M3。源码依据为 18868a79 的 dp_schedule.py:145–209；模型副本和梯度同步语义对照 PyTorch DDP 官方教程。未执行新的调度示例或两卡训练。配置、源代码和旧两样本运行记录继续折叠保留；当前阅读在同一 Step 内推进到 DP，未自动展开 PP/VPP/CP。

<a id="dp-summary-at-section-end"></a>

## 2026-10-29 · 三组完整配置集中补到 DP 段落结尾

用户反馈在 DP 结尾没有看到助手列出的三个版本配置。核对发现，函数卡此前将完整配置分散写在三个标题里，DP 结尾只有数量表；原 reference 的 DP 段落也没有集中回顾。用户反馈的是展示位置缺失，不是需要重讲 DP。

本轮在函数卡与原 reference 的 DP 段末均加入 dp-stage-summary 锚点和三行完整配置，保留已有例子与表格。三种情况每次更新总共仍使用 8 份样本。未改源码、未新增运行或学习步骤，不把格式修正记成用户掌握。

<a id="opening-increment-list"></a>

## 2026-10-29 · 开头列表说明每一步新增内容，正文标题保留配置

用户澄清标题中保留配置很好，更重要的是在开头列出每一步加入了什么。先前把完整配置集中到 DP 结尾，仅解决了局部回顾，没有提供进入正文之前的递进总览。

本轮在函数卡和原参考页开头都加入可跳转列表：第 0 步建立整批单卡基准，第 1 步增加分次计算，第 2 步增加第二个完整模型副本；同一批 A–H 和一次更新使用 8 份样本作为固定条件。各节标题继续显示 GPU 数量与当前配置，正文例子和结尾回顾保留。这是展示方式的澄清与落实，不新增技术范围或掌握判断。

<a id="dp-replica-understood-remove-recap"></a>

## 2026-10-29 · 初步区分 DP 副本与 GPU，移除段末重复回顾

用户表示大致理解，提出一个数据并行副本不必完全放在一张 GPU 上，并要求去掉 DP 段末的回顾。助手确认其方向：DP 描述副本间的数据分工，副本内部是否跨卡由其他并行方式决定；此前每 GPU 一份完整副本只是教学示例的简化条件。保留“大致理解”的程度，不将其扩大为已掌握梯度同步或模型并行实现。

按要求在函数卡和参考页中移除段末三行配置回顾，开头增量列表、各节带配置的标题、Example 和数量表继续保留。原先添加回顾的历史记录不删除。当前仍在 Step 016，未开启新的阅读范围或运行训练。

<a id="pp-complete-layers-and-explicit-titles"></a>

## 2026-10-29 · 第 3 部分 PP：分配同一模型的完整层，标题明确写出概念

用户追问第 3 部分是否把模型按层分给物理阶段，尝试表述为单卡存储“某一个层的一部分”，并要求标题明确出现 batch、DP。完整原话保存在函数卡。本轮聚焦的区别是模型的一段层与一个层内部的切分，不把表述中的含混直接记录为已掌握。

助手按 PP 校准：同一个模型副本分成若干阶段，本例第一个阶段承载第 1–4 层，第二个阶段承载第 5–8 层；每段包含若干完整层。上一节两个 DP 副本及 M0/M2、M1/M3 的数据归属保持不变，新增 GPU 2/3 承担各副本的后半段，形成 DP=2、PP=2、每阶段一张卡的四卡示意。中间结果沿流水线传递，所有样本仍经过完整模型。

为避免再次只在 reference 中新增正文，函数卡直接增加第 3 部分及 Example，开头总览与标题显式使用 Batch、Micro-batch、DP、PP。参考页保留旧 pp-and-vpp 锚点，在 PP 说明后把 VPP 标为后续参考，不在本轮展开它的机制；已删除的 DP 段末重复回顾不恢复。

概念依据为 Megatron 官方并行指南；本地 Slime 仍为 18868a79。build_dp_schedule 只接收训练约束并安排数据，本节没有声称它实际切分模型或直接读取 PP 规模。四卡布局为教学示意，设备编号不来自实际作业，未运行分布式训练。用户对本轮校准尚未反馈，继续属于同一 Step 的概念准备。

<a id="vpp-fixed-model-and-device-layout"></a>

## 2026-10-29 · VPP：固定模型层数和 GPU 数，对照同一设备上的模型片段

用户提出“一个 GPU 可能有模型的多个片段”的理解，同时仍不确定普通 PP 是否只持有一层，要求明确 GPU、DP、PP 配置，考虑引入模型总层数。完整原话存于函数卡。本轮继续 Step 016 的 build_dp_schedule 概念准备，不开启新步骤或训练实现阅读。

助手的教学判断是引入模型总层数，并把它作为固定背景：在 PP 节先标出每个副本都有同样的 8 个 Transformer 层；进入 VPP 时保持 DP=2、PP=2、每阶段一张卡、共四卡及 A–H 的分组。标题继续显示设备与并行配置，旁边固定框说明完整背景，再用同一设备的前后两列显示层分布，最后跟踪 M0 的中间结果。这把“放在哪里”与“怎样流动”分开观察，不同时改变模型大小和硬件数量。

具体校准：普通 PP 的一个阶段已经可以持有多个完整层；VPP 让每个物理阶段持有多个模型片段。副本 0 的 GPU 0 从 [1–4] 改为 [1–2]、[5–6]，GPU 2 从 [5–8] 改为 [3–4]、[7–8]；副本 1 的 GPU 1/3 同理。每卡仍四层，每副本仍完整八层；四个虚拟片段由每副本的两个物理阶段承载。数据经过不同层本就是前向计算过程，VPP 的新增关系是片段的放置与交错调度。

认知层面的理由是保持比较对象与标识稳定，把参数名称紧邻其对应的数量，并排对齐同一设备，减少读者自行回找前例和换算的负担。这是针对当前困惑的教学选择，不宣称八层或四卡是经过实验验证的最优教学数字。概念设计沿用参考页已列的 IES 具体与抽象表达、图文结合原则。

工程依据：核对 NVIDIA Megatron Core 的 initialize_model_parallel 官方 VPP 层分布例子，并缩小到 PP=2、VPP=2、八层；本地 Slime 版本仍为 18868a79。actor.py:107–119 提供 VPP/微批组配置，dp_schedule.py:112–125 用它决定小批次数对齐。模型总层数是教学背景，不是 build_dp_schedule 的参数；启用 VPP 的完整配置还涉及 mb_group，保留配套取 2 的说明，不把模型布局对照冒充只改一项的完整启动实验。

已将第 4 部分直接加入函数卡，参考页同样显示配置和前后例子；开头增量列表、scope 的已有第五步入口、函数索引和唯一路线同步。旧段落、运行证据及 DP 段末回顾的删除决定保留。只核对静态层分布与文档链接，未执行 VPP、多卡训练或新的调度例子；用户对本次解释尚未反馈。

<a id="complete-config-in-headings"></a>

## 2026-10-29 · 标题保留完整场景配置，目录与正文一致

用户指出标题的设置又缺失，明确要求标题必须显示 DP、PP、batch 和 GPU 数量。核对发现此前标题按局部重点省略参数：早期标题缺 DP/PP，PP/VPP 标题又没有整批 batch size 和 micro_batch_size。正文中已有这些值，仍不满足用户要求的标题可直接对照。

本轮在函数卡与参考页的场景标题中统一保留 GPU、DP、PP、整批 batch size；从第 1 节起显示 micro_batch_size，PP/VPP 保留模型层数与 VPP，后续参考段再列自己的 mb_group 或 CP。第 0 节仍从整批计算开始，标题先列 DP=1、PP=1 作为配置定位，正文不提前展开这些机制。开头五项列表与正文标题逐字一致，已有固定锚点继续使用。

这一明确要求更新了此前“标题只显示当前新引入参数”的展示选择。例子仍为 A–H，总 batch size=8，各段设备配置与数据流均未改变；当前阅读仍在 VPP，未新增步骤或运行。此次仅修正文档展示，不作为用户新增技术理解。

<a id="heading-config-follows-concept"></a>

## 2026-10-29 · 对应概念出现时，才把参数加入标题括号

用户补充说明“只有在每一次怎加一个新的概念的时候才会出现对应的（）里的内容”，目的是让内容与 example 清晰对应。上一轮助手把完整配置提前列入所有标题，在 Batch 段就出现 DP=1、PP=1，违背了逐步引入概念的阅读方式。

本轮在函数卡和参考页中同步调整：第 0 节只有 GPU 与 batch size，第 1 节增加 micro_batch_size，第 2 节增加 DP，第 3 节增加模型层数与 PP，第 4 节才增加 VPP。已经引入的参数继续显示，数值按本节例子更新；开头列表与正文标题相同。原例子、固定锚点与技术内容保留。

这是对上一轮标题规则的进一步澄清，不是新增阅读范围或技术掌握。当前仍在 Step 016 的 VPP 概念准备，没有运行新实验。

<a id="vpp-device-versus-layer-reuse"></a>

## 2026-10-29 · VPP 再次使用设备，与复用同一层的区别

用户回顾已讲过 PP、对 VPP 有大概认识，随后把 VPP 解释为模型同时拥有不同层、由于 Transformer 而复用 MLP 或 model 层，并询问下一处阅读内容。完整原话保存在函数卡。这里保留用户自述的大概认识，同时记录仍需校准的“层复用”解释。

当前位置仍是 Step 016：Sample 整理成训练字段 → split_by_dp 按计划分配数据 → build_dp_schedule 生成计划。当前为了理解后者收到的训练配置，已经说明 Batch、Micro-batch、DP、PP、VPP 的模型布局；还没有展开多批次的完整流水线时间安排。

助手继续使用现有八层、四卡例子：GPU 0 先为 M0 执行第 1–2 层，在 GPU 2 完成第 3–4 层后，再接手第 5–6 层。两次出现的是同一设备；第 1–2 层与第 5–6 层仍是不同的层，VPP 不要求它们共享参数。层内部采用何种网络结构与层的设备分配是不同的问题，本轮不扩展 MLP/Attention 内部实现。对应澄清补入函数卡及参考页的 VPP 正文。

按 repo-reading-order 推荐下一处看 mb_group：同一物理阶段持有多个片段后，调度器按几个 micro-batch 为一组安排某个片段的工作。最小前置就是已有的 micro-batch 和 VPP 片段；看清后回到 build_dp_schedule 的配置读取与 align_to，而不进入完整训练调度器。入口为现有参考页的 microbatch-group 段及 dp_schedule.py:115、125；这是候选推荐，尚未开始新段带读或标记为已读。

技术依据：再次核对 NVIDIA Megatron 的 initialize_model_parallel 中 VPP 分层例子，以及 ModelParallelConfig.microbatch_group_size_per_vp_stage 的官方定义；本地 Slime 仍为 18868a79，工作区无修改。这里是布局及接口语义核对，未执行模型、调度器或多卡训练。用户对“设备再次执行另一段层”的校准尚待反馈。

<a id="vpp-statement-confirmed"></a>

## 2026-10-29 · 原样保存用户确认的 VPP 表述

用户明确要求将上一轮的这句话精准记录：

> VPP 这里是同一张 GPU 在不同时间执行模型中的不同层

已原样写入函数卡 VPP 正文与用户确认记录，并同步该项关系的确认状态；此前疑问及解释经过保留。此次只确认这句话，不推断完整交错调度已掌握，也不开始 mb_group 的带读。

<a id="microbatch-group-versus-other-counts"></a>

## 2026-10-29 · mb_group：区分样本数、模型片段数与调度组微批数

用户在确认 VPP 的一句话理解后，明确要求继续看 mb_group，重点询问它和其他部分有什么区别；原话存于函数卡。本轮从候选转为实际带读，仍属于 Step 016 的 build_dp_schedule 概念准备，不另开 Step 或单独函数卡。

助手沿用八层、四卡、DP=2、PP=2、VPP=2 和 A–H 的全部样本。只放大副本 0 的 M0=[A,B]、M2=[E,F]，以及 GPU 0 上的第 1–2 层、第 5–6 层两个片段。micro_batch_size=2 数每微批的样本；VPP=2 数每物理阶段的模型片段；mb_group=2 数每个调度组包含的微批。三个值相同不代表同一概念。

局部例子展示 GPU 0 先在片段 0 处理 M0、M2，在片段 1 处理同一组微批对应的中间结果。每次仍只处理一个微批，两个微批没有合并成四样本的一次计算。这里只列本卡前向项，省略 GPU 2 的第 3–4 层、通信等待和反向，保留数据依赖；不把局部列表当成完整训练时间线。VPP 例子本来已配套 mb_group=2，本轮展开含义，不假装此前未配置它。

官方定义核对 ModelParallelConfig.microbatch_group_size_per_vp_stage（文档 0.18.1）；前向列表核对 Megatron-LM core_v0.18.0 的 get_schedule_table。其局部微批 0/1 映射到当前副本的 M0/M2，两个片段对应 0/1，得到 (M0,0)、(M2,0)、(M0,1)、(M2,1)。这是静态核对，没有运行该函数、模型或训练。

接回本地 Slime 18868a79：actor.py:107–119 提供配置，dp_schedule.py:115 读取 mb_group，125 用 DP×mb_group 约束总微批数量，168–198 对齐并分配。本例四个微批分给两个副本后各两个，满足组大小为 2 的要求。静态路径不满足约束时会报错，完整数量处理保留在已有源码段。

第 5 段已直接加入函数卡，开头目录与参考页、scope 既有第五步入口和函数索引同步；此前确认的 VPP 原句及标题渐进规则保留。用户对 mb_group 的解释尚未反馈，CP 和完整交错调度没有开始带读。

<a id="microbatch-group-tradeoff"></a>

## 2026-10-29 · mb_group 调整交错安排，不能据此推断通信量减少

用户表示理解前一段，继续提出 mb_group 是否在通信与切换之间做权衡，并明确说明这个作用仍不清楚。记录为分组含义已有理解反馈、性能目的仍待校准；不将其改写为已掌握调度性能。

助手保留“调度粒度存在性能权衡”的方向，区分同一 GPU 切换到另一个已有模型片段，与微批的跨设备中间结果传输。沿用 M0、M2：GPU 0 的第 1–2 层处理各微批后，各自的结果仍需交给 GPU 2 的第 3–4 层。分组没有自动把两个结果合并成一次通信，也不改变既定模型边界。

在足够多微批且参数合法的比较中，组大小改变同一片段先执行多少前向项、何时转到其他片段，以及前向预热的长度。较大的组可能减少前向列表中的片段切换，但延后部分后续计算，并增加需要保留的中间结果；是否更快取决于实际计算、通信、重叠安排和显存条件。定性解释与测量结论分开，本轮没有做性能测试。

证据使用下载核对的 Megatron-LM core_v0.18.0 原始 schedules.py：get_schedule_table 在原始文件第 882 行，预热逻辑在 822–870，合法范围检查在 1068–1085，逐项前向后的通信在 1529–1582。此前链接误用了网页解析器行号 808，本轮校正为原始文件行号 882。当前例子每副本仅两个微批、PP=2，在该版本下只有 mb_group=2 合法，不虚构 1 对 2 或 2 对 4 的可运行比较；不宣称该上游版本就是本机已运行的训练后端。

解释追加在原函数卡第 5 段和参考页，保持标题配置、A–H 样本和用户确认的 VPP 原句。当前仍停在 mb_group，尚未展开 CP 或完整前后向调度。

<a id="context-parallel-from-dp"></a>

## 2026-10-29 · CP：保持样本归属，展开同一条序列内部的合作

用户表示“好的 我大概理解了 那么继续推进这里的cp部分吧”。前一段 mb_group 的讲解取得“大概理解”的反馈，当前明确进入 CP；仍为 Step 016 的 build_dp_schedule 配置准备，不另开步骤。

前一步模型是微批决定每次处理哪些样本，DP 分配不同样本，PP/VPP 分配层与模型片段，mb_group 组织微批的执行项。当前新增问题是单条序列很长时，如何分担其计算和中间结果存储。助手从第 2 段另作对照，固定 PP=1、VPP=1、mb_group=1、八层模型及 A–H，仅比较 CP=1 → 2：两个 DP 副本分别由一卡改为两卡，总卡数从 2 变为 4。它不是在上一段 PP=2、VPP=2 的配置上继续加卡。

放大 M0=[A,B]，每份仍用四个 token 表示。按本地 slice_with_cp 的普通路径，CP rank 0 取 A 的 a1、a4 与 B 的 b1、b4；rank 1 取其余位置。两卡在本例中各持有完整八层参数，通过 attention 信息交换协作处理原来的 A、B。样本身份、DP 归属和完整序列关系保留，分担对象是序列位置。GPU 编号仅用于延续教学布局。

静态源码依据为 Slime 18868a79 的 data.py::get_batch（allgather_cp=False）→ cp_utils.py::slice_with_cp；说明只展示序列切分，不含后续拼接、补齐或其他 CP 路径。NVIDIA 的 CP 官方说明用于核对序列维度分工、attention 协作和长上下文显存动机。未运行这些函数、attention 或多卡训练。

回到本步主线：build_dp_schedule 在 113 行读取 cp_size，118–120 行仅在动态分批时把它用于 max_tokens_per_gpu * cp_size。当前静态分批、关闭负载均衡的例子中，CP 变化不改变 M0–M3 的组成及 DP 分配；实际 token 切分由训练端执行。下一问是如何把已读配置重新对应到本函数的索引与数量计划，尚未自动展开新范围。

CP 第 6 段直接写入函数卡，开头目录、参考页、scope 第五入口、函数索引和唯一当前进度同步。用户对 CP 的理解尚待反馈；保留此前原话、未知与实际运行证据，03 长期快照不变。

<a id="cp-and-attention-scope"></a>

## 2026-10-29 · CP 的 token 分工贯穿模型，attention 处理跨位置依赖

用户在上一段序列切分示例之后，将 CP 理解为 attention 内部需要处理的内容，并提出底层应有能在不同 GPU 上并行的 attention 算法；完整原话保存在函数卡。当前位置仍是 Step 016 的 build_dp_schedule 配置准备，没有转入独立的 attention 算法阅读。

助手区分两层关系：CP 按 token 位置分配输入与中间表示，各卡的 MLP 等计算也处理自己的位置；attention 需要同一序列其他位置的信息，因此要有支持跨卡协作的实现。沿用 a1、a4 与 a2、a3 的分工，对照 MLP 本地处理与 a4 因果 attention 对远端 a2、a3 信息的需要。示意只比较这两类计算，省略残差等步骤，token 标签代表相应位置的中间表示。

核对依据为 NVIDIA CP 官方说明：沿序列维度切分输入与激活，逐 token 的 Linear/LayerNorm 保持本地计算方式，attention 配套交换所需信息。再次核对 Slime 18868a79 的 slice_with_cp:194–224 和 dp_schedule.py:113–120：前者实现切分，后者读取配置并计算动态 token 预算；两者不在这些语句中实现分布式 attention。没有执行模型或通信。

本轮在原函数卡第 6 段和参考页中补充这一关系，并更新已有进度及原话记录。用户对 CP 与 attention 的联系已有自己的表述，整体范围的校准仍待反馈；不将提出算法假设记为已经掌握其实现，也不另开 Step。

<a id="return-to-schedule-function"></a>

## 2026-10-29 · 回到函数逻辑，并停止函数卡与 reference 的全文重复维护

用户对前一段 CP 说明反馈“差不多理解了”，要求回到 build_dp_schedule 的逻辑，并询问为什么函数卡与 reference 内容一样。此前为了满足“基础例子直接可见”的要求，助手将完整入门复制进函数卡，随后不断同步两份文本；结果函数卡开头主要讲概念，真实函数逻辑反而放在折叠区。重复是助手整理方式造成的，不是源码中存在两套同名职责。

本轮局部整理将完整 Batch → Micro-batch → DP → PP → VPP → mb_group → CP 例子集中在 references/parallelism-primer.md，保留用户要求的渐进标题和配置。函数卡恢复认可的定位、LLM 四项、输入输出、原话、未知及来源栏目，正文先显示函数骨架与当前配置约束。旧版完整卡片保存为不再维护的历史快照，旧概念锚点仍指向对应参考入口；原两样本源码与运行结果折叠回查，全部原话继续保留。此次是当前记录的职责纠错，不修改通用 skill 或长期继承规则。

返回主线时沿用 A–H，使用此前 VPP / mb_group 例子的 DP=2、CP=1、VPP=2、mb_group=2，micro_batch_size=2、静态分批且关闭负载均衡。每份样本有独立 rollout ID；这次特例中 global_batch_size=8 同时对应八份样本。源码仍为 Slime 18868a79。

本轮通过 AST 提取 _pack_step_into_mbs 与 build_dp_schedule 的原始函数体，隔离执行这一组输入，得到 partitions=[[0,1,4,5],[2,3,6,7]]，两个 rank 的本地微批均为 [[0,1],[2,3]]，num_microbatches=[2]，global_batch_sizes=[8]。运行仅验证静态索引计划，不执行 VPP、CP、张量、Ray 或模型；证据单独保存在 dp-schedule-eight-samples-output.json，不把此前的静态推导改写为当时已经运行。

当前讲解聚焦①的 112–125 行：max_per_bin 是动态路径使用的 token 预算，当前为 None；align_to 是总微批数的倍数要求，当前为 2×2=4。稍后形成四个微批，每 rank 分两个，满足这一组约束。随后应接②的 rollout_id_to_samples，解释训练步如何选中样本位置；其余阶段先给导航，不据此标为全部理解。scope 仍保留既有五个阅读入口，没有另开 Step。

<a id="schedule-dataflow-clarification"></a>

## 2026-10-29 · 区分验证说明、源码语句和返回值，接清同一输入的中间过程

用户反馈 dp schedule 仍不够清楚，尤其质疑“固定版本原始函数体”附近的展示。原话保存在函数卡。这是当前表达仍未解决困惑的反馈，不登记为已理解。

助手分析：上一稿先给完整 SimpleNamespace 构造，随即显示四项结果数组，却只展开了①的配置约束；②–⑤的源码仍藏在另一组两样本例子里。因而同一组 A–H 如何走到这些数组没有直接连起来。“固定版本原始函数体”描述验证方式，放在结果之前也容易让人把展示值误认成源码本体。该分析由助手提出，不能当作用户已经确认的具体困惑。

本轮沿用原配置及已经取得的输出，不增加新的样本例子。将完整验证输入和执行范围移到来源折叠区，正文先用八个位置说明函数实际接收的长度和归属，再以五段源码及对应中间数据串联。③–⑤仍在②的训练步循环内部；节选时明确说明去掉一层缩进，并保留当前正常分支。返回语句单独显示，最终四元组明确标成返回值。

核心解释落在三次位置转换：step_mbs=[[0,1],[2,3],[4,5],[6,7]] 给微批定义样本；rank_mbs_idx=[[0,2],[1,3]] 分配微批编号；最后 rank 0 的 M2 把整批位置 4、5 写入 partitions，但在 rank 0 列表中接在位置 2、3。用两次循环的表格说明两个返回索引为何不同，数量列表再分别对应每 rank 微批数及全步 rollout 数。

本地源码仍为 18868a79，工作区无修改。中间数据来自对 112–209 行正常路径的静态展开；最终值对照上一轮八样本 JSON，不重新运行函数或训练。只修改当前卡片表达和入口，完整并行入门继续在 reference，历史原话、两样本记录和已有快照保留。新版是否清楚仍待用户反馈。

<a id="schedule-return-count-units"></a>

## 2026-10-29 · 返回值按 rank 还是训练步排列，数量究竟数什么

用户表示大概理解，并将 micro_batch_indices 描述为在已获得的 partitions 中使用本地 index 分批；同时将样本分给两路称为 PP，询问 num_microbatches 是微批大小还是微批数量，以及 global_batch_sizes 是否为一个 schedule 中 DP、PP 和微批组合后的 batch 总数。完整原话及返回元组保存在函数卡。

助手保留本地索引的语义理解，区分它与实际构造顺序：先组微批、分给 rank，最后同时写出两套索引。两路不同样本的分配属于 DP；PP 让同一份数据经过不同模型阶段，不能把阶段数再计为新增样本。

同一例子中，一个训练步全局八个 rollout，且每个对应一份样本。每个 DP rank 四份样本，拆为两个微批，每微批两份样本；micro_batch_size=2 数样本，num_microbatches=[2] 按训练步记录每 rank 微批数，global_batch_sizes=[8] 按训练步记录全局 rollout 数。前两份返回列表最外层按 rank，后两份按训练步。本次后两份列表长度一，说明只安排一个训练步；一次函数调用也可以包含多个完整训练步。

核对本地 Slime 18868a79 的 100–105 行、135–150 行、187–189 行及 198–209 行。2×2×2=8 只用于当前固定微批、每 rollout 一样本的例子，不推广为多片段 rollout 的计数恒等式。沿用原运行证据，无新增执行；用户对本轮计数及 DP/PP 校准尚待反馈，未开启新 Step。

<a id="schedule-role-and-parent-handoff"></a>

## 2026-10-29 · 概括计划职责，下一处回到实际数据交接

用户将 build_dp_schedule 概括为计算每个训练 GPU 应得的样本，并询问还缺什么、做完之后做什么；完整原话存入函数卡。这是对职责的初步概括，不将其当作此前所有计数问题已验证。

助手校准分配单位为 DP 副本：一个模型副本可能跨多张 GPU，本函数产出每个 DP rank 的样本及微批计划。它只接收长度与归属信息，实际训练字段仍由父函数处理。

按 repo-reading-order，从已读主线选择下一处短回顾：BatchBuilder.split_by_dp:498–523 按同一 partition 取 tokens、rewards、loss_masks，附上 rank 的 schedule 并准备张量；527–530 返回 Box 包装的数据引用。这些段落已有卡片，本轮只定位用途和交接，不再新建函数卡，也不把旧材料当成新的阅读完成记录。两样本父卡与八样本调度例子的场景差异继续保留。

正常的“计划 → 配套数据 → 返回引用”接通后，本步即可考虑收束；之后的既定候选为 train.py::train:51–99 的生成训练闭环：接收生成结果，交给训练，通知 training_completed，更新生成侧权重，再按周期评估。该候选只作后续方向，尚未建立下一 Step，不进入训练 loss、通信或传输内部。

本轮核对本地 Slime 18868a79 的父函数和 train 调用位置，未执行模型、训练或新的测试。当前函数的原始运行证据保持，用户对 DP 副本和物理 GPU 的区别及父函数交接仍需后续反馈。

<a id="split-by-dp-eight-sample-closing"></a>

## 2026-10-29 · 按用户要求，沿 A–H 完成父函数的数据交接说明

用户明确要求“好的 那么给出这里的收尾的内容吧”。本轮采用上一问已经推荐并获得继续授权的范围，回到现有 BatchBuilder.split_by_dp 卡，讲解计划返回后的字段选择、安排附加、张量准备和引用返回；不创建新 Step。

上一环节的计划保持 partitions=[[0,1,4,5],[2,3,6,7]]、每 rank 两个微批、全步八个 rollout。为让字段选择可见，给 A–H 补充长度为 4 的构造 token ID、长度为 2 的响应 mask 及奖励 1.0–8.0。它们是教学输入，不来自真实模型生成；完整字段与输出保存在 split-by-dp-eight-samples-fields.json。

核对本地 Slime 18868a79：读取真实 fields 清单，用 AST 取原 schedule 赋值、value 字段选择及两次字典更新语句执行，结果 rank 0 得 A、B、E、F，奖励 [1,2,5,6]；rank 1 得 C、D、G、H，奖励 [3,4,7,8]。两者都附有自己的 partition、本地微批索引及全局数量列表；raw_reward 和 total_lengths 保留全局数组。执行明确停在 tensorize_rollout_data_for_training 之前，未调用完整父函数、torch、Ray 或训练。

张量化和返回部分按源码解释：tensorize_rollout_data_for_training 原地将指定字段整理为 CPU Tensor，rewards 在该函数中保留列表；默认 object-store 路径将每份 rank 数据通过 ray.put 取得引用，Box 包装后组成两项列表返回。示意图只写 ObjectRef 类型，没有伪造运行取得的引用编号。

父函数卡默认入口改为本轮 A–H 收尾，原两样本说明与来源折叠保留；子卡返回链接、scope 第五步、索引及唯一路线同步。数据准备主线至此已有完整交接说明，用户是否理解仍待反馈。下一候选保持既定训练闭环，不提前创建或标记下一 Step，也不把本文当作训练已实际执行的证据。

<a id="split-by-dp-box-objectref"></a>

## 2026-10-29 · 第②段补源码引用，第③段区分列表、包装与实际数据

用户要求在第②段加入 split_by_dp 引用，并复述第③段会把准备后的数据放进 list，每项与 Box 有关，同时表示不知道 Ray 的含义，将其理解为一个节点所需的样本与数据。完整原话保存在父函数卡。

本轮在第②段标明 BatchBuilder.split_by_dp:498，以及附安排、类型整理的 522–523 行；说明这些是父函数内部阶段。第③段标明 527 行，将单行表达式等价展开为先 ray.put(value) 得 ObjectRef、再 Box(ref)、最后追加到 result。展开变量是教学标记，真实源码没有改动。

本地 Box:143–149 的构造函数只保存 _inner，inner 属性返回它。Ray 官方 put 接口说明用于核对对象存储和引用的含义；没有运行 Ray 或据文档推断本机版本。图示按 list → Box → ObjectRef → value 展示，value 含对应 DP rank 的样本、配套训练字段和微批安排。DP rank 与物理节点或 GPU 的映射保留训练部署边界。

用户对“列表收集准备后的数据”的方向已有表述；“Box 中调用 Ray”和“节点”对应的校准尚待反馈。没有开启新的 Ray 专题或新建 Box 卡片，没有新增执行。

<a id="ray-data-handoff-understood"></a>

## 2026-10-29 · 用户确认样本、配套字段和安排一起交付

用户表示“大概理解了”，并明确将这段职责概括为得到批次后把对应数据交给 Ray，包含样本、配套字段和对应安排。原话保存在 split_by_dp 卡片。此次记录的是数据交付这一层的确认，不是对 Ray 全部机制的确认。

助手将其具体化为：当前 rank 的 value 已包含样本字段与微批安排；ray.put 保存它并返回引用，后续训练侧通过引用取得数据。本轮只补充交付边界，没有新建函数卡、开启下一 Step 或执行代码。下一候选仍是既定训练闭环。

<a id="training-loop-next-scope"></a>

## 2026-10-29 · 数据交付之后的下一步范围建议

用户在确认数据交付职责后询问是否可以继续。当前 Step 016 已讲到样本字段、DP 分配计划与引用交付；用户“大概理解”的反馈保留，未展开的实现边界不因此记为掌握。

按既定路线，助手建议 Step 017 围绕 train.py::train 的一次训练循环：生成结果引用怎样传给 actor_model.async_train，完成后怎样通知 training_completed，再怎样更新生成侧权重并继续下一轮。eval 只定位在循环中的位置。首个局部入口为 51、67 行的引用接收与训练交接；采用 use_critic=False 的正常路径，资源卸载、checkpoint、loss、优化器和通信内部先不展开。

建议短期记忆先以 train 为父函数保存一轮的“输入引用 → 训练调用 → 完成通知 → 权重交接”，只在出现独立问题时下钻。这是具体范围建议；本轮只核对源码与规划，没有创建 Step 017、继承新长期快照或提前填入该函数的理解记录。等待用户就这一具体范围继续确认后建立下一步。

源码核对本地 Slime 18868a79：train.py:51、67、71、88–99，工作区无修改，没有新增运行。
