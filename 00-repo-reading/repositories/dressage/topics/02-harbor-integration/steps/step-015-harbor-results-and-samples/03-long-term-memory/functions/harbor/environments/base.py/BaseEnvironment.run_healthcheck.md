# BaseEnvironment.run_healthcheck

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/environments/base.py/BaseEnvironment.run_healthcheck.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.run_healthcheck.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码：[base.py:1560–1612](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1560)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 013，2026-11-13；此前已在聊天中展示配置选择部分。
- 最近认识更新：2026-11-13，用户已将 HTTP 示例理解为验证 sandbox 是否准备好；该认识限于本例，重试细节未确认掌握。

[Trial._prepare 的调用处](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-healthcheck-call) → **run_healthcheck** → [exec](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.exec.md) → 回到本函数判断退出码。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：环境启动后、Agent 准备前。
2. **具体内容**：执行配置中的检查命令，以退出码决定通过或重试。
3. **建议构建的心智模型**：

   > 任务提供检查方法，Harbor 等待检查通过，再继续准备 Agent。

4. **调用代码**（Trial._prepare:647–648）：

   ```python
   await self.agent_environment.run_healthcheck()  # 不传参数，使用环境中的检查配置。
   await self._upload_injected_skills()           # 检查正常返回后，从这里继续。
   ```

## 本场景的输入与输出

教学裁剪：省略日志、计时和失败处理的具体语句，完整循环保留在下方；此片段用于阅读，不能直接替换实现。注释采用仓库 `hello-healthcheck` 的真实配置作为静态示例，未实际运行。

<a id="healthcheck-config"></a>
<a id="healthcheck-command"></a>
<a id="healthcheck-next"></a>
<a id="healthcheck-loop"></a>

```python
async def run_healthcheck(
    self, healthcheck: HealthcheckConfig | None = None
) -> None:
    # self 是 Trial 持有的环境；本次未传 healthcheck，取任务环境配置。
    hc = (
        healthcheck if healthcheck is not None else self.task_env_config.healthcheck
    )
    if hc is None:
        return  # 没配置就跳过，回到 Trial._prepare。

    while True:
        # 本例 command="curl -sf http://localhost:8080/"，timeout_sec=5：
        # 在目标环境内检查本地 HTTP 服务；其他任务可配置不同命令。
        result = await self.exec(hc.command, timeout_sec=int(hc.timeout_sec))
        if result.return_code == 0:
            return  # 以退出码判定通过，不看 stdout 文本；正常返回 None。

        # 失败处理（具体语句见下方）：等待后重试；宽限期内不计失败，
        # 之后计数达到阈值就抛 HealthcheckError，退出本函数。
```

需要下钻时看 [exec / ExecResult](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.exec.md)，随后回到 `result.return_code`；本函数正常返回后，接回上面的 `_upload_injected_skills()`。

<details>
<summary>完整循环：计时、宽限期、重试与异常边界（源码 1584–1612，省略日志）</summary>

```python
start_time = time.monotonic()
start_period_end = start_time + hc.start_period_sec  # 启动宽限期的结束时刻。
consecutive_failures = 0

while True:
    now = time.monotonic()
    in_start_period = now < start_period_end

    # 每轮真正执行一次检查命令，取得本轮结果。
    result = await self.exec(hc.command, timeout_sec=int(hc.timeout_sec))

    if result.return_code == 0:
        return  # 通过：退出整个 run_healthcheck，回到 _prepare。

    if in_start_period:
        # 宽限期内失败不计数，等一会儿再检查。
        await asyncio.sleep(hc.start_interval_sec)
    else:
        consecutive_failures += 1
        if consecutive_failures >= hc.retries:
            raise HealthcheckError(
                f"Healthcheck failed after {hc.retries} consecutive "
                f"retries: {hc.command}"
            )  # 失败次数达到阈值：抛错，退出本函数。
        await asyncio.sleep(hc.interval_sec)  # 尚可重试，等待后进入下一轮。
```

先沿循环认清三个动作：**执行命令 → 判断结果 → 通过则返回，失败则决定等待还是抛错**。`while True` 让未退出的情况继续下一轮；`return` 结束整个函数，`raise` 则沿异常路径退出。宽限期内也立即检查、也能立即成功返回，不是先等待整个宽限期结束。

`in_start_period` 在每轮执行命令前计算。`timeout_sec` 限制本次检查命令；`start_period_sec` 用于决定失败是否计数，两者不是同一个限制。如果 exec 本身抛出异常，此处没有捕获，会向调用方传播。

</details>

## 我的直接表述（原话）

本轮理解（节选）：

> 好的也就是说简单的来看需要看一下这个网址是否可达
> 用于验证这个sandbox是否准备好了
> ok

本例确实用环境内 HTTP 服务的响应判断就绪；其他任务可通过不同命令定义检查条件。


<details>
<summary>阅读顺序、函数完整性与精简要求</summary>

用户确认应先沿调用方阅读：

> 我需要的是你一点点带着我读
> 例如这里的这个应该是先看这里的这个run healthcheck对吧

随后要求把入口放回 Trial 卡片：

> 那么应该在这个trial这里这里列出一下这个agent environment run haelthcheck这个函数的short term memory对吧

用户随后指出函数卡漏掉主体：

> 这里难道不是有一个run_healthcheck
> 吗
> 以及这里的这个的short term memory的函数卡片
> 怎么没有和函数对应上呢?
> 这里难道不应该是需要看一下这里的这个while true的部分吗?

用户进一步明确阅读重点：

> 以及需要给出这个exec hc command到底在执行什么?
> 其余的一些不是特别重要的部分倒无所谓?
> 作为一个资深的程序员和认知学专家你会如何修改这里的这个short term memory呢?

这些是对阅读顺序、记录位置和解释重点的要求，尚未作为对检查算法的个人理解。

用户要求进一步精简：

> 是不是还是不够凝练?
> 你看一下是否还有比较合适的方式构建这里的函数卡片呢?

</details>

## 尚不清楚

- 用户已说明本例的检查用途；配置选择与退出码机制尚无单独复述。
- 宽限期与计数细节按需回查；目标环境 exec 的具体后端实现暂缓。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 Harbor 的 `git show v0.25.0:src/harbor/environments/base.py` 核对本方法；方法签名为 `async def run_healthcheck(self, healthcheck: HealthcheckConfig | None = None) -> None`。
- 调用方为 [Trial._prepare:641–658](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L641)。调用代码是局部节选，完整 try/finally 由父函数卡保留。
- 命令类型与约定：[HealthcheckConfig.command:358](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/config.py#L358)，shell 命令，退出码 0 表示健康。
- 示例配置：[hello-healthcheck/task.toml:27](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-healthcheck/task.toml#L27)；服务启动：[environment/entrypoint.sh](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-healthcheck/environment/entrypoint.sh)。只借用示例解释检查目标，没有展开或选定 Docker 后端实现。
- 本轮补齐配置选择之后的循环主体，日志省略但业务分支保留；材料完整性不代表用户已读完或掌握。未实际执行健康检查，也未取得运行结果。
- [Step 013：补齐 Trial 到健康检查卡的入口](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#healthcheck-card-linked-from-trial-20261113)。

- 示例补充：hello-healthcheck 的启动脚本等待 3 秒后启动 HTTP 服务。curl 的 `-s` 隐藏进度和错误提示但保留响应正文，`-f` 使 HTTP 错误响应产生失败退出码。本函数不检查响应正文。
- [精简前完整卡片](../../../../../../step-013-harbor-kubernetes-environment/references/history/2026-11-13-run-healthcheck-before-condensing.md)保留此前的字段表、示例与展开说明。

</details>
