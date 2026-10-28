# AsyncRolloutWorker.get_completed_groups

- 源码定位：[fully_async_rollout.py:147–161](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147-L161)，由助手核对，固定版本 `18868a79`。
- 首次接触：Step 012 作为结果消费接口定位；2026-10-26 在 Step 013 确认独立阅读。
- 最近认识更新：2026-10-26，用户已表示理解前述领取说明，并尝试类比为“节流器”；本轮进一步区分按次领取上限、按时间限速与生成侧背压。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_generate_rollout_async 正在凑本次需要的组，向本地 worker 领取已经进入 output_queue 的结果。
2. **具体内容**：连续从队列移出回调写入的 (gid, group)，放入本次返回列表；达到 limit 或遇到空队列就返回。
3. **建议构建的心智模型**：

   > **按需取走已完成的组，遇空即返回。**
   >
   > 取走：从 output_queue 移除，放入返回列表。
   > 最多：limit 按组计数，剩余结果留在队列。
   > 遇空返回：不等待凑满；没有可取结果时返回 []。

4. **调用代码**（_generate_rollout_async:312，循环体此处省略）：

   ```python
   for _gid, group in worker.get_completed_groups(limit=target - len(collected)):
       ...
   ```

   `target - len(collected)` 是当前还缺的组数。只取需要的数量，把多余结果留给后续 rollout；这些组已经消耗输入并完成生成、评分，多取后丢弃会浪费已完成的工作。

   **“节流器”类比的边界**：这里限制的是每次调用最多领取几组，没有时间窗口、速率计数或等待间隔。生成侧的背压在 [_loop](AsyncRolloutWorker._loop.md)：output_queue 积压达到其阈值时，暂不接纳新组；领取移走结果后，后台下一轮才可能重新满足接纳条件。两者共同参与生产与消费的协调，各自控制的对象不同。

## 本场景的输入与输出

**教学构造，静态推导**：接上 [_make_done_cb](AsyncRolloutWorker._make_done_cb.md) 的例子，编号 7 和 8 的组都已入队；本次只剩一组名额，因此 limit=1。下表中的列表用于表示队列内容，真实字段是标准库 queue.Queue。

| 项目 | 内容 |
| --- | --- |
| 调用前队列 | [(7, result_group_7), (8, result_group_8)] |
| 本次参数 | limit=1 |
| 返回值 | [(7, result_group_7)] |
| 调用后队列 | [(8, result_group_8)] |

这里的 1 按组计数，result_group_7 里可以有多个 Sample。领取会从队列移除元素，不只是查看。返回列表仍保留 gid；样本结构保持原样。

在没有新结果入队的同一例子里，如果改为 limit=3，也只返回这两组；队列一开始就空则返回 []。**limit 是上限，不是必须等到的数量。**

### 连续源码：取到上限，或者没有可取结果

以下为原方法的执行体，仅省略签名注解与文档字符串，添加对应标记。

```python
def get_completed_groups(self, limit=None):
    completed = []
    while limit is None or len(completed) < limit:       # [1]
        try:
            completed.append(self.output_queue.get_nowait())  # [2]
        except queue.Empty:                            # [3]
            break
    return completed                                   # [4]
```

- **[1]** limit 限定本次最多取几组。None 表示没有这个数量上限，循环在碰到空队列时停止；这不是并发队列的一次固定快照。
- **[2]** 取出并移除一个元素，再追加到本次返回列表。领取顺序是入队顺序，不在这里按 gid 排序，也不保证等于任务创建顺序。
- **[3]** 没有立即可取的元素，就停止本次领取。队列一开始就空时返回 []；空队列不是生成失败。
- **[4]** 把已经取到的组记录交回调用方，不强求凑满 limit。该方法本身不是 async，也不等待后续生成。

**回到调用方**：_generate_rollout_async 解包得到 _gid 和 group，再判断过滤结果、决定是否放入 collected。队列已经取走与最终是否保留是两个时刻；过滤器本步只定位，不展开。

## 我的直接表述（原话）

2026-10-26，用户初步描述本方法，并询问需要注意的边界：

> 这里的内容也比较好理解吧
> 也就是获取一下以及完成的groups
> 这是我的理解
>
> 对于这个函数还有什么需要特别注意的地方吗？

[本轮核对与补充](../../../../../04-flow.md#step013-getter-purpose-and-boundaries)。

随后用户表示理解，并提出类比：

> 好的我理解了
> 也就是这一步其实也算一种节流器对吗？
> 我是这么理解的

类比的适用边界见[本轮澄清](../../../../../04-flow.md#step013-getter-throttling-analogy)。

回到调用方时，用户接续说明结果来路：

> 目前看到的这里有worker get completed groups
> 也就是在这里获取完成的groups
> 然后从之前翻入的worker outputuqueue里面得到记录？
> 这是我的理解？

[返回调用方与阅读深度](../../../../../04-flow.md#step013-return-to-caller-and-reading-depth)。

## 尚不清楚

- 用户已表示理解领取说明；“按次限量”和“按时间限速”的区别是本轮新增澄清，尚无针对这一修正的独立表述。
- 暂不深入：消费方丢弃一组后怎样继续补充，以及队列跨线程同步的内部实现。
- 后台何时因队列腾出空间而接纳新组，回到已有 [_loop 背景卡](AsyncRolloutWorker._loop.md)查看条件；本方法不主动启动新 Task。

<details>
<summary>来源、验证与完整例子</summary>

- [_make_done_cb:273](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L273)写入 (gid, result)，[get_completed_groups:147–161](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147-L161)移出，[_generate_rollout_async:312–321](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L312-L321)接住结果。
- [完整源码摘录](../../../../../references/source-excerpts.md)；[版本与验证边界](../../../../../references/source-evidence.json)。
- 标准库 queue.Queue.get_nowait 的最小语义见[参考](../../../../../references/python-callback-notes.md)。示例只做静态推导，未运行真实并发生成。
- [本轮短期卡补充](../../../../../04-flow.md#step013-getter-memory-update)：保留用户的用途理解，三项领取边界由助手据源码整理，尚未视为用户独立复述。
- [原始 Step 013 过程](../../../../../../step-013-completed-group-handoff/04-flow.md#step013-start)。

</details>
