# DressageHarborPlugin.on_job_end

- 归属：Dressage，源码 [plugin.py:420](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:420)。
- 首次接触：2026-11-16，Step 015；已记录当前疑问；不标记掌握。
- [本步 scope](../../../../../../01-scope.md)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层 `_run_partition` 等待 `job.run()` 返回 JobResult 后，显式调用本函数。它不是单次 Trial 的 END 回调 `_on_end`。
2. **具体内容**：从 JobResult 提取最终 Trial 身份；有 Store 且未推迟选择时，委托写结果清单；最后调用 `aclose()` 收尾。
3. **建议构建的心智模型**：

   > 整个 Job 已返回，这里处理 Job 级收尾。当前 rollout 配置把最终结果选用留给外层，因此这里先关闭插件资源，再返回外层继续检查结果。

4. **调用代码**（rollout.py:760–762）：

   ```python
   await plugin.on_job_start(job)
   result = await job.run()
   await plugin.on_job_end(result)
   ```

## 本场景的输入与输出

**先记住用途：整个 Job 已结束，通知插件“可以处理最终结果登记，并收尾你持有的运行资源了”。** 它不是再生成结果的函数。

- **传入**：Harbor 返回的 `JobResult`，里面有各个 Trial 的结果与身份。
- **完成的事情**：按配置决定是否委托登记最终结果，然后调用 `aclose()` 收尾。
- **返回**：正常返回 `None`；调用者继续使用原来的 JobResult 和之前保存的 bundle。

### 把这一个函数连起来看

教学裁剪：保留真实取值、分支和 finally，只省略清单调用的路由统计参数。省略号处不是完整可运行调用。

```python
# ① 从 Job 的结果中整理“最终有哪些 Trial 身份”。
final_keys = {
    (str(getattr(result, "trial_name")), str(getattr(result, "id")))
    for result in (getattr(job_result, "trial_results", None) or [])
}
try:
    # ② 如果由本层负责最终登记，就把这些身份交给 Store。
    if self._artifact_store is not None and not self._defer_final_selection:
        await self._artifact_store.write_job_manifest(
            job_result,
            final_keys=sorted(final_keys),
            ...
        )
finally:
    # ③ 最后收尾插件运行资源。
    await self.aclose()
```

**① 拿身份，是为了后面的结果登记。** 例如结果里有 `trial_name="task-A"`、`id="attempt-2"`，就得到 `("task-A", "attempt-2")`。它能对应到 Store 中此前保存的那次尝试的 bundle。这里不重新提取 token、不重新评分，也不按最高分挑尝试。

**② 登记，是告诉 Store“最终采用哪些尝试”。** `write_job_manifest` 根据这些身份更新结果选用状态并形成 Job 级清单；具体文件写入暂不展开。但当前 rollout 把这个动作推迟给外层，所以这段不执行。

**③ 收尾，是释放运行时占用。** `aclose()` 委托清理逻辑处理尚在收尾的任务、尝试路由、Job 凭据、Gateway 租约及插件自己持有的 Proxy 客户端。这里调用清理，不等于删除已保存的结果。等待限时、后台清理等细节本轮不展开。

### 当前路径实际走了什么？

`_run_partition` 创建插件时传入了 `defer_final_selection=True`（[rollout.py:729](/home/hongshi/projects/Dressage/dressage/integrations/harbor/rollout.py:729)）：

```text
① 提取 final_keys
      ↓
② 跳过 write_job_manifest     ← final_keys 在本函数这条路径中没有继续使用
      ↓
③ await self.aclose()         ← 当前路径的主要实际工作
      ↓
返回 None，回到 _run_partition
```

**为什么推迟？** 外层还要取得 bundle、转换 Sample，并检查整组结果是否满足要求。完成这些后，才汇总成功组的 `selected_keys`，调用 Store 登记最终结果（rollout.py:853–873）。所以不能把 Job 返回的 Trial 名单直接当成最终可采用的训练结果名单。

| 使用方式 | 在 on_job_end 中做什么 |
| --- | --- |
| 有 Store，`defer_final_selection=False` | 按 JobResult 的身份委托登记，再收尾 |
| **当前 rollout：`defer_final_selection=True`** | **先收尾；最终登记交给返回后的外层流程** |

读到这里即可返回 `_run_partition`。本轮需要保留的是：**Job 的执行结束了，插件资源可以收尾；结果的检查与选用还可以继续。**

## 我的直接表述（原话）

用户当前的疑问：

> 这里的这个on job end 是在做什么呢？
> 简单从这里的这个result中拿到对应的内容？
> 然后呢？
> 这个short term memory是不是不是特别清楚和清晰呢？

用户已注意到从 result 取值，尚未表示理解后续登记与资源收尾的用途。

后续反馈：

> 好的 我清楚了 虽然我感觉这里的函数应该是耦合了

用户表示当前说明已清楚，同时提出职责耦合的设计感受；尚未进一步讨论是否需要拆分实现。

## 尚不清楚

- 外层如何将最终 Trial 身份对应到 bundle，以及哪些组检查影响选用，尚待沿 `_run_partition` 接续。
- `aclose` 的内部清理与超时处理本轮不展开。

<details>
<summary>来源、验证与修正</summary>

- 固定版本：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；plugin.py:420–441，rollout.py:729、760–762、853–873。
- 助手此前将 on_job_end 概括为“选择最终尝试”，不够准确：它可以委托写清单，但当前 rollout 明确推迟到外层。已按实际调用配置修正。
- 代码为静态核对，未运行 Job 或清理操作。教学节选中的省略号不代表完整可运行调用。
- [本步讨论过程](../../../../../../04-flow.md)。

</details>
