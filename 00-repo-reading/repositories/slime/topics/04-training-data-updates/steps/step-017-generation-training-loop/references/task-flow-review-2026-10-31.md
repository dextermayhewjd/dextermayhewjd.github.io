# Step 017 task flow 审阅：参照以前的总结补清交接

> **完整参考稿已写出：[一轮数据怎样完成训练，并交回生成侧](task-flow-reference.md)。** 用户已要求按第 5 节的方向写成完整 reference；本页继续保存比较和方案形成过程。

> 结论：当前四部分的职责划分合适，第 2 节还需要补清“输入怎样变化、谁在等待、返回哪里”。本页保存对照与局部候选，正式 [05-task-flow](../05-task-flow.md) 本轮保持原文。

> **最新建议见 [第 5 节](#recommended-two-level-flow)**：保留主骨架，以短小的局部调用图、面包屑和注释解释交接。第 2、4 节保留方案形成过程；不再推荐把跨函数代码直接拼成一个深缩进的 Python 块。

[本步 scope](../01-scope.md) · [函数记录](../02-short-term-memory/overview.md) · [本轮问题与记录](../04-flow.md#task-flow-reference-review-20261031)

## 1. 参照哪几份旧稿，具体借鉴什么

以下使用当前目录中的 Step 编号；skill 中历史命名的 Step 003、Step 007，分别对应当前 Step 004、Step 008。

| 已有 task flow | 值得沿用的做法 | 当前 Step 017 的差距 |
| --- | --- | --- |
| [Step 004：轨迹与奖励交成训练样本](../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/05-task-flow.md)，第 2、3 节 | 调用节点旁同时写接收的字段、结果变化、返回父函数的位置；结果表说明字段来源和去向 | 当前树主要列函数名，数据引用与结果引用的转换、训练后参数留在哪里，要离开树去查表 |
| [Step 008：启动 CLI 并等待结果](../../../../01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md)，第 2 节 | 入口的直接动作放在第一层，子调用缩进；退出码沿各层返回的方向可跟随，并区分两种等待 | 当前树虽有调用层级，但没有就近显示 async_train 交回引用、train 外层等待与 update_weights 内部等待的区别 |
| [Step 013：完成的组交给上层](../../../../02-rollout-reward/steps/step-013-completed-group-handoff/05-task-flow.md)，第 2、4 节 | 分开后台和消费侧，标明通过什么交接、由什么事件触发继续；边界表说明何时需要回查 | 当前已说明 _loop 独立运行，这点应保留；还需说明 pause 等待的后台确认，以及恢复后只是重新允许接任务 |

当前稿值得保留的内容：正常路径与可选分支的边界、四部分结构、函数卡片导航、训练与发布的区别、未运行真实训练的说明。

建议重点调整四处：

1. **第 2 节以“调用 + 就近注释 + 返回位置”为主。** 让表格补充定位，减少读者在树和表之间拼接同一信息。
2. **启动背景与本轮主体分开。** 启动时推送已有权重只需短提醒；本轮主体继续沿数据、训练、登记、同步与评估。
3. **暂停、同步、恢复放在同一段内，但保留各自完成条件。** 完成登记不停止 rollout；暂停确认不保证在途任务结束；权重同步正常返回后才判断恢复。
4. **第 4 节收回技术边界。** 保留本步停止点和具体未知；后续岗位取舍用链接引用已有复核，不在 task flow 重述 A/B/C 的讨论过程。

## 2. 第 2 节的局部候选：调用旁直接说明交接

### 2.1 先定位启动背景和本轮输入

循环前的 train.py:16–25 建立训练组、发布载入的权重，再用 training_ready 通知启动准备完成；它还承接恢复场景中暂时冻结的后台。这里只提醒位置，不展开初始化。

本轮从 train.py:51 接住 Step 016 的 `list[Box]` 开始，Box 中保存按 DP 分片的数据引用。下面沿 use_critic=False、直接权重同步、已有可用生成引擎的正常路径展开；暂停机制使用已读的本地 AsyncRolloutWorker 作说明。有批次登记的完成通知是单独标明的条件分支。

### 2.2 跟随主循环，并在原位置展开必要的子调用

这是**阅读用的调用层级伪代码**：缩进表示调用归属，包括远程调用；同行注释说明作用，独立注释说明返回后的状态。它不是可直接运行的 Python。参数及外围 checkpoint、资源处理作了裁剪；后台 _loop 不列为 pause 的子调用。

```python
train(...)  # 指挥官：把一轮数据、训练和生成侧更新接起来
    for rollout_id in ...:  # train.py:47，本轮编号
        rollout_data_ref = ray.get(rollout_manager.generate.remote(...))  # 51：接住数据引用列表

        ray.get(actor_model.async_train(rollout_id, rollout_data_ref))  # 67：① 提交，并在外层等待
            # RayTrainGroup.async_train 内部：每个训练 worker 收到整份 rollout_data_ref
            actor.train.remote(...)  # 按 worker 提交；每次返回一个训练结果 ObjectRef
            # async_train 交回引用列表 → train 的 ray.get 等所有训练调用正常完成
        # 回到 train:71：训练侧已有新参数；生成侧尚未因这次训练自动更新

        ray.get(rollout_manager.training_completed.remote(rollout_id))  # 71：② 告知数据侧本批训练结束
            self.batch_builder.training_completed(rollout_id)  # RolloutManager 转交给 BatchBuilder
                if self.batch_id is not None:  # BatchBuilder 内部；主例无登记则直接返回
                    # 有登记时先核对 rollout_id 是否匹配
                    ray.get(self.controller.finish_batch.remote(self.batch_id))  # 登记消费、移除未完成批次引用
        # 逐层返回 train；经过本图折叠的 checkpoint / 资源处理，再到 88 行

        was_paused = ray.get(rollout_manager.pause_rollout_admission.remote())  # 88：③a 暂停新接纳
            worker.pause(drain=False)  # Manager 找到已登记的后台；正常运行时等暂停确认
            # 返回暂停前状态 → was_paused；无后台时返回 True
        # 回到 train:89：新接纳已暂停；已有在途任务仍可能运行

        actor_model.update_weights()  # 89：③b 将训练后的参数发布给生成侧
            # RayTrainGroup.update_weights 内部：提交各训练 worker 的发布工作
            ray.get([actor.update_weights.remote() for actor in self._actor_handlers])  # 等待在本方法内部
                self.weight_updater.update_weights()  # 各 Megatron worker 委派具体发布；传输机制留在卡片
            # 正常返回 None → train:92；本主例的生成引擎已接收新参数

        if rollout_id + 1 < args.num_rollout:  # 92：还有下一轮才请求恢复
            ray.get(rollout_manager.resume_rollout_admission.remote(was_paused))  # 93：③c 按旧状态恢复
                if not was_paused:  # RolloutManager 内部；不打开原先已暂停的后台
                    self.data_source.consumers["fully_async"].resume()  # 重新允许接纳；不是等待新数据生成完

        if should_run_periodic_action(...):  # 98：满足本次评估条件
            ray.get(rollout_manager.eval.remote(rollout_id))  # 99：④ 等本次评估处理完成
                result = call_rollout_fn(..., evaluation=True)  # RolloutManager.eval：取得评估输出
                data = result.data  # 取评估数据；本图折叠共享服务收尾
                save_debug_rollout_data(...)  # 按配置保存调试数据
                log_eval_rollout_data(..., data, result.metrics)  # 记录评估结果
            # 正常返回 None → 当前循环体结束
        # 进入下一轮 rollout_id；没有下一轮则离开 train
```

**这整段完成什么**：把本轮数据变成训练侧的新参数，再把这些参数交给生成侧，使后续生成可以使用本轮训练结果。数据消费登记负责结束本批的使用记录；暂停与恢复负责围住权重同步时的新任务接纳；评估在条件满足时使用同步后的引擎并记录结果。

与 Step 013 相同，后台需要单独说明：在本地 worker 的正常运行场景，pause 写入 paused=True 后等待；已在运行的 _loop 观察这个标志、停止新增任务，并写入 admission_paused、notify_all。pause 被唤醒后复查确认状态，才把原状态交回主循环。drain=False 不等待所有在途任务结束，具体安装权重时的协调由 updater 负责，本步没有展开。

对应卡片：[① 训练提交](../02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md) · [② 完成登记](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md) · [③a 暂停](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md) · [③b 权重发布](../02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md) · [③c 恢复](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.resume_rollout_admission.md) · [④ 评估](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.eval.md)。

## 3. 其他部分只需怎样调整

- 第 1 节保留入口与配置边界，明确本地 worker 是暂停机制的已读主例；不把它描述为所有后端唯一实现。
- 第 3 节沿用当前结果表，补充“由谁接住或使用”一列：结果引用由 train 的 ray.get 使用，新参数先留在训练 worker、再发布给生成引擎，was_paused 交给恢复判断；eval 的 data/metrics 留在评估处理内，正常返回 None。
- 第 4 节沿用“职责层阅读已收束、实现未知仍保留”的判断。后续实践只链接[已有岗位复核](../../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md#jd-recheck-20261031)，不增加新必读函数。

本轮交付的是审阅和具体候选，不把新排版视为已采用，也不据此新增学习完成或实际运行状态。

<a id="breadcrumb-comment-option"></a>

## 4. 补充方案：面包屑定位，Python 注释解释，段末返回主线

用户进一步询问以前是否有“面包屑 + 绿色注释”的方式。最接近的已采用组合是本步 [training_completed 正式卡片](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model)：开头的面包屑定位当前函数，2.3 按层次展开 Python 伪代码，以 # 写注释。旧 [Step 006 task flow](../../../../01-coding-agent-rl/steps/step-006-agent-sandbox/05-task-flow.md) 第 3 节也用 Python 代码块和旁注说明调用方的使用期与返回回收位置。

这两份材料分别提供了已经使用过的表达方法；检索到的旧 task flow 尚未把整条主流程统一排成下面的组合。本节是把它们应用到当前 task flow 的局部候选。

### 4.1 主线只保留一次，各分支用面包屑接回

主线仍为：接住数据 → ①训练并等待 → ②完成登记 → ③暂停、同步与恢复 → ④按条件评估。每次展开只注明当前走到哪个分支、下面是谁，再用一小段带注释的代码展示交接。已有第 2 节的大代码块可按这四个分支分段，不必在每段重画整轮流程。

### 4.2 示例：展开主线中的②完成登记

**当前路径**：[train](../02-short-term-memory/functions/train.py/train.md#training-completion) → **② 完成登记** → [RolloutManager](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model) → BatchBuilder → RolloutQueueController。

下面沿用分层阅读伪代码；缩进表示调用归属，不是可直接运行的 Python。注释中的 2.1–2.3 表示②内部的层次。Python 代码块使 # 后的文字按注释高亮，具体颜色取决于阅读器主题。

```python
# ② 完成登记：进入这里时，本轮训练已经结束
ray.get(rollout_manager.training_completed.remote(rollout_id))  # 主循环等待登记处理完成
    # 2.1 RolloutManager：把通知转交给数据组织侧
    self.batch_builder.training_completed(rollout_id)
        # 2.2 BatchBuilder：以下 self 指 BatchBuilder
        if self.batch_id is not None:  # 主例无登记批次时直接结束
            if rollout_id != self.rollout_id:
                raise ValueError(...)  # 有登记时，先核对是不是同一轮
            ray.get(self.controller.finish_batch.remote(self.batch_id))  # 等待指定批次收尾
                # 2.3 Controller：更新消费进度、移除本批未完成登记并保存状态
# 逐层返回 train.py:71；经过保存与资源处理后，主线到 ③a 暂停接纳（88 行）
```

**这一段完成什么**：把“本批已经训练完”的事实交给数据管理侧，完成适用的消费登记，再把控制权交回主循环。下一段暂停新任务接纳是另一项动作。

这种排法中，面包屑回答“现在在哪里”，同行注释回答“这一行在交接什么”，末行回答“完成后回哪里”。展开③时仍须把后台 _loop 标成独立运行的协作者，不因展示缩进而变成 pause 的直接子调用。

<a id="recommended-two-level-flow"></a>

## 5. 从认知负担与工程准确性重新判断：主骨架与局部交接分开

**当前更推荐的组织：完整主骨架 + 带面包屑的局部交接 + 结果去向。** 面包屑、绿色注释保留，但不把它们本身当成最优形式。判断目标是用户隔天回来能找回一轮流程、准确解释相邻动作为什么能交接；这是一项针对当前材料的设计判断，尚无用户使用效果或学习实验验证。

### 5.1 对前一版具体调整什么

| 观察角度 | 前一版仍有的问题 | 建议调整 |
| --- | --- | --- |
| 找回整体 | 多层展开挤在主骨架中，读局部时容易失去这一轮做到哪里的参照 | 主骨架连续保留，只呈现 train 的主要直接动作；①②③④与局部节标题一致 |
| 同时理解代码和解释 | 长注释、表格和深层实现争夺注意，颜色只改善识别，不能决定哪些内容需要记住 | 注释优先写用途、状态变化或等待条件；每段末尾一句说明结果及下一站 |
| 正确识别运行关系 | 连续的 Python 缩进跨越多个函数和进程，self 的身份还会改变 | 跨函数关系用明确的调用图，写对象全名、普通调用或 Ray 调用；源码片段各自注明所属函数 |
| 保持记忆职责 | 若每个节点重抄完整实现，task flow 会变成第二份函数卡合集 | task flow 保留组件间的交接，内部算法、条件变量与存储细节链接已有卡片 |

### 5.2 保留四部分，只改变第 2 部分的阅读层次

1. **位置与前提**：接住 Step 016 的数据引用，注明本次正常分支和结束位置；启动准备只短提醒。
2. **主骨架与局部交接**：2.1 连续显示 train 的裁剪骨架，Python 的缩进只表示真实控制结构。随后 2.2 训练、2.3 完成登记、2.4 暂停/同步/恢复、2.5 评估逐段说明交接；每节有短面包屑和返回位置。第 2 节始终可见关键调用归属，不能仅用表格代替。
3. **结果与去向**：一次性对照数据引用、任务结果引用、训练侧新参数、生成侧参数、was_paused 和评估记录，注明谁持有、谁使用；不再重复抄一遍调用代码。
4. **收束边界**：本轮已经连接的关系、仍留白的内部机制及回查入口。岗位复核和历史取舍继续引用既有记录。

层次按当前问题展开，不要求每个函数固定拆成三层。读者只想恢复整轮关系时，看主骨架和结果即可；某个交接不清楚，再进入对应局部节。

### 5.3 以完成登记为例：明确是调用图，避免伪装成一个函数

**面包屑**：[Step 017](../01-scope.md) → train 的一轮循环 → **② 完成登记**。

**进入条件**：主循环已经等到本轮训练正常完成；现在交入 rollout_id。

下方是调用图，借用 Python 代码块高亮 # 注释，不是 Python 程序。对象名保持明确，树线表示调用归属。

```python
train.py:71  # 驱动进程等待这次完成通知处理结束
└─ RolloutManager.training_completed(rollout_id)  # Ray 调用；接收本轮编号
   └─ BatchBuilder.training_completed(rollout_id)  # 普通调用；检查是否有登记批次
      └─ [有批次且轮次匹配] RolloutQueueController.finish_batch(batch_id)  # Ray 调用；等待消费登记完成
```

**结果与返回**：无登记批次时直接结束；有登记且匹配时，更新消费进度、移除本批未完成登记并保存状态。调用逐层返回，驱动结束 71 行的等待，经保存与资源处理后进入 88 行的暂停接纳。轮次不匹配报错的规则保留在[函数卡](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model)。

这里让读者同时看到调用归属、编号交接、等待与结果；不需要再次展开 Controller 的锁、回执、保存和 GC 实现。注释只在承担新信息时出现，不为每个名字机械添加中文翻译。

### 5.4 暂停与同步采用适合各自关系的局部表达

- **暂停接纳**：保留主循环 → Manager → worker.pause 的调用链；后台 _loop 另列为已经在运行的协作者，用 paused 请求与 admission_paused 确认连接两侧。不能沿同一棵调用树继续画成 pause → _loop。
- **训练与同步**：明确 async_train 把结果引用交回驱动，由外层 ray.get 等；update_weights 在组方法内部等待各 worker 发布完成。训练侧新参数和生成侧接收参数是不同时间点。
- **恢复与评估**：保留是否还有下一轮、was_paused 与周期评估条件，简单节点直接写作用和返回即可；无须为了版式把它们扩成同等篇幅。

采用后应以实际回顾检验：能否仅沿主骨架说明一轮；能否在对应局部节找出谁持有结果、谁等待、什么条件让主线继续。若仍需反复跳转，就针对该交接调整，而不继续增加通用栏目。

本节是最新推荐，尚未替换正式 task flow，也没有改写此前已采用的函数卡或通用 skill。

<details>
<summary>对照与源码依据</summary>

- 依据 [task-flow skill](../../../../../../../../.agents/skills/repo-reading-task-flow/SKILL.md) 及第 1 节三份现有总结；借鉴其交接表达，不复制旧例的分支数量或运行关系。
- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本轮核对当前 checkout `540ea919e45b8b929198abce008a103be9cfc779`；上述 train、actor_group、rollout、batch_builder、fully_async_rollout 和 Megatron actor 六个文件与固定提交没有差异。
- [主循环 47–99](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/train.py#L47-L99)；[训练提交及发布 148–190](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/actor_group.py#L148-L190)。
- [管理器暂停与恢复 151–158](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L151-L158)；[评估及完成通知 392–431](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L392-L431)；[BatchBuilder 条件转交 144–148](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L144-L148)。
- [本地暂停与恢复 114–126](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L114-L126)；[_loop 的接纳与确认 202–228](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L202-L228)。
- 本次是静态源码与文档比较，没有新增真实 Ray、worker、训练、权重同步或评估运行；既有替身实验的范围继续见原 task flow 和函数记录。

</details>
