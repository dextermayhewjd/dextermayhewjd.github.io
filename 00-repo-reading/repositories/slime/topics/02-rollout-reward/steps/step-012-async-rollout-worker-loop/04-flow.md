# 04 · Step 012 的理解形成过程

<a id="step012-start"></a>

## 2026-10-26 · 用户确认继续到后台持续调度

### 前一步模型与本步问题

用户已将组级函数概括为把一组工作分别交给 generate_and_rm，并表示大概理解分工。具体结果回填、评分与失败边界的未知继续保留。依据岗位复核，下一源码主线是持续调度，而评分扩展与验证作为配套实践。

用户确认：

> 好的那么请继续吧
> 开启下一个step吧

据此创建同一主题下的 Step 012，入口 AsyncRolloutWorker._loop。阅读聚焦在途组任务、完成结果积压、持续接纳和完成后补充；不新开 topic。

### 本轮核对发现的实现选择

本地与官方源码 HEAD 均为 18868a79b0b083a093798a94ed0f8cb4f71b9c14，本地工作区干净。_get_worker 在数据源带 reader_config 时创建 DistributedRollout，否则创建 AsyncRolloutWorker。Coding Agent 示例脚本第 130 行的默认 ROLLOUT_DATA_TRANSPORT 是 straw，因此不能把本地 _loop 当作该脚本默认配置的实际执行体。

本轮向用户说明该边界，并继续已确认的本地 _loop 阅读，用它建立持续调度的基础模型。此前把 fully-async 入口直接等同于本地 worker 的描述由此补正；分布式实现不在本步展开。

### 初始材料与阅读入口

scope 保留连续完整正常骨架；父卡分四段，每段均有源码与对应标记。先用①确认组级 Task 与 self.concurrency 的含义，从③接回前一步的组级调用，再看②回收和④发布/等待。_make_done_cb 只保留回调工厂接口，尚未创建独立卡片。

所有数据示例均为教学假设。尚无用户对 _loop 内部机制的反馈，未把初始源码说明转作个人认识。

### 继承与验证

Step 011 的 59 份 03 与 5 份 02 按路径合并为 60 份累计记录；同名完整 02 优先，3 份历史空白仍为空。原话、未知和来源保留，按新位置重算链接。组级函数与 GenerateState 调取到本步 02，新增 _loop 父卡。

完整骨架按去除异常包装和退出等待后的正常路径进行 AST 对照。文件与来源检查不表示运行真实 worker 或达到岗位实践要求；没有运行模型、Agent、远端服务或训练，也不处理 Hugo。


<a id="ray-worker-boundary"></a>

## 2026-10-26 · 分布式分支是否使用 Ray

用户追问：

> 也就是说这个分布式其实可以在ray上实现吗？
> 是这个意思吗？

最小核对 fully_async_distributed.py：DistributedRollout.__init__:532–558 筛选存活且有 CPU 资源的 Ray 节点，检查容量后用 ray.remote(_GenerationActor).options(...).remote(...) 创建 actor，并用 NodeAffinitySchedulingStrategy 绑定节点；每个 actor 申请一个 CPU。RolloutScheduler._run:115–135 使用远程 start/pause/next、ray.wait 和 ray.get 协调控制与结果。

actor 内部另有 asyncio 生成池，_produce:330–367 创建组任务，_generate_group:371–388 再调用已有 generate_and_rm_group。因而可以概括为“Ray 负责跨节点 actor 与远程交互，actor 内 asyncio 负责组任务并发”。分布式分支使用自己的 _GenerationActor._produce，并非直接复用本步 AsyncRolloutWorker._loop；两者都接到组级生成函数。

本轮只是回答实现选型与边界，未转入分布式方法的完整阅读或新建函数卡，也不表示已实际运行 Ray 集群。当前 Step 012 仍按已确认的本地 _loop 范围推进。


<a id="task-registration-and-polling"></a>

## 2026-10-26 · 从用户已说清的回收，接到登记与轮询

### 用户表述

> 好的那么我们现在还是应该看一下这里的这个asyncrolloutworker
> 好的那么请来一点点理清楚这里的的四个部分吧
> 首先是这里的task我差不多是理解的
> 然后是这里的并行
>
> 然后呢是什么？
>
> 回收这里的tasks？
> 我不是特别理解了
> 当前应该看看什么呢？
> 要不你带着我一点地iankanba
> 最开头的1我是能看懂的
> 第二各部分是
> 如果有任务已经完成了
> 那么就可以把这个active task剪掉了
>
> 然后之后是看一下这里的active的组如果小于的就从data buffer里面再拿一个sample是我的理解
> 然后再通过拿到group id的方式
> 再发送一个task
> 为什么最后有一个active tasks.add task？ 我有点没理解
>
> 以及最后一个状态状态部分我其实没有特别了解
> 这里的poll interval是做什么的呢？
> 我觉得需要看清楚？
>
> 请和我一步步过一下吧
>
> 主要针对我没有清楚叙述出来流程的部分

### 本轮带读重点

用户表示①能看懂，并描述完成 Task 可从 active_tasks 移除。先承认这段回收关系，再校准 get_samples(1) 的单位是一组、创建 Task 与给组编号的区别。

重点补充两条关系：create_task 安排执行而不会自动修改 active_tasks，add 才登记到本循环维护的集合；await sleep(poll_interval) 挂起调度协程，让其他 Task 和回调获得执行机会，再回到下一轮检查。采用“已有 TA，再创建并登记 TB，容量从 1 到 2”的同一个例子，不另开函数卡。

状态发布先说明作用：self.active 和 self.admission_paused 是给协调线程检查的快照，notify_all 通知等待者。poll_interval 在构造器第 103 行为 0.01 秒；异步等待不代表所有生成已结束，也不是生成超时。Condition 的完整协议仍留后续。

以上是源码解释与静态推演，尚待用户继续反馈。未运行真实 worker、队列服务、Agent 或训练；当前仍在 Step 012。


<a id="worker-class-and-input-source"></a>

## 2026-10-26 · 建立 worker 类卡，接清输入与状态字段的读取方

### 用户反馈

> 这里的done我的理解是 如果有一个人物完成了
> 那么就会进入sleep的状态 同时这里变成可以或者需要sleep的情况
>
> 这里机会让到这里的下面一个while loop
> 是我的理解
>
> 这里进入的条件我也可以理解
> 但是这里的data buffer 我觉得我需要清楚是哪里来的
> 这个是我觉得需要了解的数据结构
>
> 下面的内容比较好理解
> 其实就是根据我们之前读得generate and rm group来生成这里的task
>
> 所以这个其实也好理解
>
> 但是最后一个部分在做什么 我其实就不是特别理解
> 这里的四我需要额外的理解
>
> 我觉得主要会变成
> 当前这个asyncrollout worker 是否需要单独开一个class 的short term memory？
> 这样子能够加深对于这个class的理解 主要是为什么需要某些字段

### 当前校准

- done 是本次检查收集到的完成 Task 集合；非空时，回收后执行 sleep(0)，让出给事件循环。_loop 被重新调度后才继续下面的接纳 while，不是 sleep 直接调用或移交给该 while。
- 默认本地分支中，参数解析选择 RolloutDataSourceWithBuffer；RolloutManager 构造 self.data_source，经 call_rollout_fn 原样传给生成入口，在参数名 data_buffer 下到达 _get_worker，最后保存为 worker.data_buffer。同一个对象有自己的输入 buffer；完成结果队列 output_queue 属于另一端。
- 第④段发布的 active/admission_paused 有具体读取方 pause。paused 是请求，admission_paused 是循环发布的观察状态，active 是给等待方读取的数量快照；notify_all 让等待者重新检查暂停确认和 drain 条件。

按用户提出的字段理解需要建立[AsyncRolloutWorker 类卡](02-short-term-memory/classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md)，沿用已认可的 BaseAdapter 类卡结构，先列 13 个实例字段，再用源码接清输入来路及 pause/_loop 配合。_loop 卡保留执行变化并链接类卡，未将每个字段拆成新函数卡。

本轮只做必要前置回查和静态源码核对，未运行真实 worker 或队列；用户提出问题不记作已经掌握请求/确认或 Condition 协议。


<a id="worker-blackbox-boundary"></a>

## 2026-10-26 · 收窄类卡：依赖按接口使用，细节暂作黑箱

用户反馈：

> 我在想的问题是
> 这里asyncrolloutworker部分
> 这里吧sample什么放在这里2是合适的吗？
> 我只是感觉
> 在asyncrolloutworker部分这里的内容实在是太复杂或者晦涩难懂了
> 如果全部放在这里的话 我觉得会变成一个内容的灾难？
> 因为目前其实或许暂时不需要知道这么多
>
> 暂时把一部分留为黑箱 对于人来说比较好定位

此前类卡同时放入 13 个字段、输入数据源内部、跨多层来源链和 pause/Condition 协议，超出了当前跟随循环所需的前置。按用户明确反馈，类卡改为当前对象接口和最短来源；Sample 内部留在它自己的已有记录，数据源只保留 get_samples 的输入输出，第④段暂记作状态报告。

完整旧卡已移入[按需参考](references/worker-class-full-context-2026-10-26.md)，包含全部字段、来源、代码和原话。_loop 的完整执行骨架与逐段源码保留，暂停配合说明改为参考入口。黑箱表示暂缓内部机制，不代表相应部分已理解或可以删除历史。

本步继续围绕“拿一组、启动并登记、回收、必要时暂停接纳”的正常主线；没有增加 Sample 细节、线程原语或暂停协议的必读步骤。


<a id="next-completed-result-handoff"></a>

## 2026-10-26 · 下一处建议：完成结果怎样进入队列并被取走

用户反馈：

> 好的 我觉得 我差不多理解了
> 那么读完了这个step的话 我应该需要读什么部分呢/

用户对当前主线给出概括性理解反馈；数据源内部、暂停/Condition 协议与此前细节未知继续保留，不据此全部标为掌握。

沿当前本地 worker 的实际交接，下一候选是 AsyncRolloutWorker._make_done_cb:246–275，先读其返回的 _cb 的正常完成路径：done_task.result() → output_queue.put((gid, result))。它直接接上 _loop 中已读的 add_done_callback 注册点，回答“任务完成后结果由谁接住、放到哪里”。

随后短读同类的 get_completed_groups:147–161，确认结果从队列取出并交给 _generate_rollout_async:305–323 的收集逻辑。首次范围只串起正常结果，取消、中止重排与重试准备按下一问再展开，不把所有旁支变成前置。

建议下一步的记录重点：完成通知、返回值、带组编号入队、限量取走，以及它们各发生在哪一层。仍采用连续源码、少量标记与紧邻说明。推荐尚未作为新步骤的范围确认，未创建 Step 013、函数卡或完成总结。


<a id="jd-recheck-after-worker"></a>

## 2026-10-26 · 按混元 JD 重新核对剩余阅读范围

用户问：

> 请重新和对一下腾讯混元的岗位
> 然后考虑一下为了对齐这个岗位
> 我还需要看一下slime这里哪些代码呢？

本次重新获取腾讯官方职位接口，HTTP/API 均为 200，原始响应与当日已保存证据的 SHA256 一致；本地 Slime HEAD 与官方 main 均为 18868a79，源码工作区干净。详细职责映射和固定源码入口保存在[岗位对照](../../../../../../../slime_photo/code-reading/job-alignment.md#jd-after-step012-20261026)。

助手建议保留近期主线：完成回调/结果消费 → BatchBuilder 的样本转换 → train 的训练与权重闭环。随后明确补读默认 straw 路径的 Ray 调度与队列交接；结合一个扩展和一次故障穿插接口测试、Trace 与部署。训练控制骨架之后另作一次 advantage/loss 输入输出阅读，不展开全部算法与后端。

这次细化有两个边界：BatchBuilder 的奖励后处理不等于重新调用奖励模型；本地 AsyncRolloutWorker 的阅读不能替代分布式示例的实际路径。此前评分归属与插件加载模型继续复用，未把实践缺口改成重复阅读前置。

用户请求的是岗位复核与推荐，尚未确认开始完成回调或其他新范围；没有创建 Step 013、预写新函数卡或运行新增测试/部署。已有黑箱、未知与用户的概括性理解反馈保留。


<a id="jd-primary-focus-correction"></a>

## 2026-10-26 · 用户要求抓住岗位主要内容

用户重新贴出六条任职要求与四条加分项，并质疑：

> 感觉这里没有你说的那么多的内容？
>
> 你确定吗？
> 请找主要的内容来看吧

本轮以用户提供的文本分析，不声称再次获取官网。关键区别是任职要求使用“了解”及“至少一类”，上一轮把训练内部、分布式队列和恢复都提升为必读，混入了完成 Slime 全景的目标。助手承认范围偏大并修正为：复用已读 Agent 核心链路；近期完成任务结果交付，接着看 Trace 与接口验证；Kubernetes/容器单独通过具体部署排障准备。训练保留全景认识与自动化评估这一可选方向，具体 loss、权重同步和分布式实现按实际问题选读。

修正后的建议、对应条款与停止位置见[岗位对照](../../../../../../../slime_photo/code-reading/job-alignment.md#jd-primary-focus-20261026)。用户要求的是收窄推荐，不是确认开启这些步骤；未创建 Step 013 或新函数卡，已有未知和概括性理解反馈不变，未进行新测试或部署。


<a id="jd-scope-sufficiency-review"></a>

## 2026-10-26 · 区分近期新增阅读与完整准备范围

用户问：

> 确定只需要读明白这些内容就可以了吗？
> 请仔细考虑一下
> 不需要变多
> 但也不能变少

本轮复核用户贴出的任职要求和此前保存的完整官方职责，没有将“三项近期新增阅读”视为岗位的全部要求。助手保留结果交付 → Trace → 接口测试的近期顺序，并将其放回已有 Agent 主链、训练/评估背景和 Kubernetes 实践中。训练只需要在本轮准备中保留交接层认识，不恢复此前深入 loss、权重同步和分布式队列的长清单。

范围判断由函数数量改为可检验行为：能解释端到端链路，能落实一个小接口需求并测试，能定位一次运行问题，能实际完成部署与排障。一个项目可承载这些证据，不再新开多个平行课程。详细边界保存在[岗位范围复核](../../../../../../../slime_photo/code-reading/job-alignment.md#jd-minimum-sufficient-scope-20261026)。

本轮只形成范围建议，未将用户的追问记成理解确认；未创建下一步骤或函数卡，未开展新运行、训练或部署。下一源码候选仍是完成回调的正常结果交付。
