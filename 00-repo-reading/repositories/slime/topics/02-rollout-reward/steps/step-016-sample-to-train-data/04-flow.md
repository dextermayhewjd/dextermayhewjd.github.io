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
