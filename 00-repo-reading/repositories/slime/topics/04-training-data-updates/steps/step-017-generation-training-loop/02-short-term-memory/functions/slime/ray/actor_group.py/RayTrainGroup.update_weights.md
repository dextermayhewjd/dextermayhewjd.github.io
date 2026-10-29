# RayTrainGroup.update_weights

- 源码定位：[slime/ray/actor_group.py:178](/home/hongshi/projects/slime/slime/ray/actor_group.py:178)，固定版本 `18868a79`；调用方为 [train.py:89](/home/hongshi/projects/slime/train.py:89)。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-29，用户已将更新与 rollout 使用新参数联系起来，进一步追问两侧是否都停止，还是训练已结束而只需同步。当前补清训练计算结束、暂停新接纳、同步和恢复的时序，理解待反馈。
- 导航：[scope 的③](../../../../../01-scope.md#weight-handoff) → **本卡：提交权重更新并等待** → [返回 train 的暂停/恢复组合](../../../train.py/train.md#weight-handoff)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：一轮训练与完成通知已经结束，调用方先暂停后台 rollout 的新任务接纳，再让生成侧使用训练更新后的权重。假定训练和生成服务可用，本轮只看非全量磁盘更新的分支。

2. **具体内容**：遍历训练 worker 句柄，提交每个 worker 的 update_weights.remote，并在本方法内部通过 ray.get 等待。实际权重连接、发送与服务端处理由下层执行，本轮只识别交接。

3. **建议构建的心智模型**：

   > 训练已改动训练侧参数；这个入口组织把相应权重提供给生成侧，并等各 worker 的更新调用结束。
   >
   > 先完成训练计算，再同步已有新权重。暂停与恢复接纳由外层 train 编排，本方法负责中间的权重同步；训练进程仍参与这次同步。

4. **调用代码**（train.py:89）：

   ```python
   actor_model.update_weights()
   ```

## 本场景的输入与输出

本次没有显式业务参数；self 是已经创建的 RayTrainGroup，内部持有 `_actor_handlers` 和权重更新配置。当前训练 worker 已持有本轮训练后的模型，生成侧服务已经就绪；选择非全量磁盘更新分支，不把 object-store 数据传输与权重传输方式混为一个配置。

**输出**：正常返回 None；在本方法返回前，ray.get 已经等待这些 worker 的更新调用结束。具体权重传输不在此处展开。

<a id="training-finished-before-sync"></a>

### 到这里时，训练侧和生成侧各在做什么

沿当前 train.py 正常路径，67 行已等待本轮训练结束，训练 worker 已有本轮的新权重。随后 88 行暂停新的 rollout 接纳，89 行把新权重同步到已有生成引擎。这里需要分开看两侧：

| 一侧 | 更新权重期间的状态 |
| --- | --- |
| 训练侧 | 本轮训练计算已结束，新参数已经算好；训练 worker 参与权重同步，主循环等待同步返回，尚未进入下一轮训练 |
| rollout 侧 | 后台调度暂停接纳新的生成任务；已有生成引擎接收训练侧的新权重。当前没有据此断言所有在途请求都已结束 |

因此，“训练已经完成，现在同步给生成侧”是当前时序；训练进程仍在执行同步工作，不能把它概括成两侧进程都停掉了。

```text
本轮训练计算完成，新权重已在训练侧
    → 暂停新的 rollout 任务接纳
    → 训练 worker 向生成侧同步权重，主循环等待
    → 有下一轮且原先未暂停时，恢复接纳
```

pause_rollout_admission 使用 drain=False，只由这一调用不能推断全部在途生成已经结束或取消。生成引擎在实际安装权重时如何协调在途请求属于下层同步机制，本轮继续留白；不以“暂停新接纳”替代该机制的解释。

### 当前精读骨架（178–182）

真实源码节选，只保留本轮分支；后面的全量磁盘保存和重载分支暂时折叠。

```python
def update_weights(self) -> None:
    if not self._full_disk_weight_update_enabled():
        ray.get([actor.update_weights.remote() for actor in self._actor_handlers])
        return
```

1. 遍历的是已有训练 worker 句柄；各 worker 的更新调用产生结果引用。
2. 本方法内部的 ray.get 等待这些调用结束，随后返回 None。
3. 下层 [MegatronTrainRayActor.update_weights:629](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:629) 取得可更新的生成引擎，并最终委派 weight_updater.update_weights；这里只定位，不追通信实现。

和刚读过的 async_train 对照：async_train 先交回引用列表，由 train 的外层等待；这里 update_weights 把等待包在自身内部，所以调用方直接调用它。

### 读完回到哪里

回到 [train 父卡](../../../train.py/train.md#weight-handoff)：88 行暂停新接纳，89 行完成更新；有下一轮时，92–93 行按原暂停状态决定是否恢复。不是无条件打开原本已暂停的 producer。

**下一观察点：更新完后，什么时候恢复生成？** 进入 [train.py:92–93](/home/hongshi/projects/slime/train.py:92)，必要时只回查 [RolloutManager.resume_rollout_admission:156–158](/home/hongshi/projects/slime/slime/ray/rollout.py:156)。下一次只需弄清两个条件：是否还有下一轮、暂停前是否已经暂停。暂停与恢复先保留在父卡的 [恢复接纳入口](../../../train.py/train.md#resume-after-weight-sync)，不新建完整调度专题。

## 我的直接表述（原话）

用户指出真实执行顺序，并询问精读重点：

> 然后下一步不是这里的paused吗？
> 虽然应该也很好理解
> 就是原有的rollout部分不再接受新的请求应该是这个意思对吧
> actor model 更新权重我们先看这一步吗？

其中暂停新接纳的理解由用户提出；具体暂停粒度、was_paused 的含义及权重更新内部等待由助手补充，尚待反馈。

用户对当前动作的初步理解：

> 我的简单理解就是 现在所有的actor都开始更新当前的权重我可以这么理解吗？

其中“所有 actor”按源码限定为当前训练组 self._actor_handlers 中的训练 worker。这里的更新是发布/同步已有的训练后权重，让生成侧使用新参数；参数的训练更新已在前一阶段完成。列表推导式提交每个 worker 的更新调用，外层 ray.get 等它们结束。该校准不等于用户已确认全部同步细节。

用户对训练结束与同步时序的追问：

> 好的 那么继续吧
> 这里是在当前已经有的rollout侧用上了这些新的参数
> 是训练侧和rollout侧都停下来吗？
> 还是训练侧已经更新完整了权重
> 现在只需要actor这里同步权重就可以了？

助手按 train.py 的实际先后关系回应：本轮训练计算先完成，随后进入同步；训练进程参与同步而不启动下一轮训练，rollout 暂停新接纳。具体在途生成如何处理没有据此推断或标记为理解。

用户要求保存上述解释并考虑下一步：

> 记得把这里的内容写清楚放在这个函数卡片里面吧
> 然后考虑下一步

本次将两侧状态整理为对照表，并明确下一观察点是恢复条件。保存说明和提出下一入口不表示用户已确认全部时序或恢复机制。

## 尚不清楚

- 用户对更新调用与内部等待的理解尚待反馈。
- weight_updater 的权重传输、引擎同步和在途生成收束方式未展开。
- 全量磁盘更新分支仅识别边界，未精读。
- 没有运行真实权重更新、生成或训练。

<details>
<summary>来源、验证与完整例子</summary>

- [本轮进入第三段的讨论](../../../../../04-flow.md#pause-before-weight-update)。
- [两侧状态与下一入口的整理](../../../../../04-flow.md#weight-sync-state-card-and-next)：保存请求、状态对照与恢复条件的候选入口。
- 固定源码：train.py:88–93；actor_group.py:178–190、241–246；rollout.py:151–158；MegatronTrainRayActor.update_weights:629–678。
- _full_disk_weight_update_enabled 检查 role=actor、update_weight_mode=full、update_weight_transport=disk 三者。本例选择其返回 False 的路径；不深入传输。
- 仅静态核对，没有新运行。哈希与阅读范围见 [源码证据](../../../../../references/source-evidence.json)。

</details>
