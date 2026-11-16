# BaseEnvironment.run_healthcheck

- 源码定位：[src/harbor/environments/base.py:1560–1612](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1560)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 013，2026-11-13；此前已在聊天中展示配置选择部分，本轮补入函数卡。
- 最近认识更新：尚无针对检查机制的个人复述；已展示与待续读位置分别保留。

[Trial._prepare：环境启动之后](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-healthcheck-call) → **当前 run_healthcheck** → 到命令调用时进入 [exec](../../02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.exec.md) → 返回本函数检查结果 → 返回 _prepare。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：环境启动调用已正常返回，Trial 在继续 skills 与 Agent 准备前，按配置检查环境。
2. **具体内容**：从检查配置取得 shell 命令 `hc.command`，通过环境的 exec 执行，以退出码判断是否通过；通过就返回，否则按配置等待或抛错。BaseEnvironment 已提供这段通用编排。
3. **建议构建的心智模型**：

   > 任务作者定义“怎样检查环境已可用”，Harbor 执行这条命令并查看退出码。通过后，Trial 才继续准备 Agent；没有检查配置则跳过。

4. **调用代码**（Trial._prepare:647–648，节选；前面的启动已经读过）：

   ```python
   # 环境启动已正常返回；下面两行位于 _prepare 的 try 内。
   await self.agent_environment.run_healthcheck()  # 当前进入；没有显式传配置。
   await self._upload_injected_skills()           # 正常返回后继续这里。
   ```

## 本场景的输入与输出

已有对象是 `self.agent_environment`。调用表达式写在 Trial 中，当前方法定义在 BaseEnvironment 中；进入方法后，`self` 指环境对象。

| 输入 | 本次从哪里来 |
| --- | --- |
| self | Trial 持有且已调用 start 的环境对象 |
| healthcheck: HealthcheckConfig 或 None | 调用方未传，使用默认值 None |
| self.task_env_config.healthcheck | 环境对象持有的任务环境配置，作为本次检查配置的来源 |

<a id="healthcheck-config"></a>

### 1. 取得检查配置 · 前面已展示

源码 1576–1580 行，只增加注释：

```python
hc = (
    healthcheck if healthcheck is not None else self.task_env_config.healthcheck
)  # 有显式参数就用它，否则取环境中的任务配置。
if hc is None:
    return  # 没有配置检查，直接返回 _prepare。
```

本次没有显式传入 healthcheck，所以 `hc` 取自 `self.task_env_config.healthcheck`。这一段只选配置；有配置才继续向下执行检查。

<a id="healthcheck-command"></a>

### 2. hc.command 到底执行什么 · 当前重点

它是任务配置里的 **shell 命令字符串**。检查什么由任务作者决定，run_healthcheck 负责执行和判定退出码。

用仓库自带的 `examples/tasks/hello-healthcheck` 具体化这次调用。下面摘取该示例的两个配置字段；这是静态阅读示例，不表示当前已启动这个任务。

```toml
[environment.healthcheck]
command = "curl -sf http://localhost:8080/"
timeout_sec = 5
```

这个示例的启动脚本在等待 3 秒后启动 HTTP 服务。检查命令会在**目标环境里**访问该服务：`localhost:8080` 指执行命令所在环境的本地地址。`-s` 隐藏进度和错误提示但仍可输出响应正文，`-f` 让 HTTP 错误响应产生失败退出码。

```python
# 原函数中的调用；本例 hc.command 是上面的 curl 字符串，超时为 5 秒。
result = await self.exec(hc.command, timeout_sec=int(hc.timeout_sec))
```

命令成功退出，`result.return_code == 0`，本轮检查通过。服务尚未监听等情况会使 curl 非零退出，再交给下面的失败处理。**这里判断的是退出码，不要求 stdout 包含某段文字。** 更换任务后，hc.command 可以是其他检查命令，不能把这个 curl 当成 Harbor 固定内置的检查。

<a id="healthcheck-next"></a>
<a id="healthcheck-loop"></a>

### 3. 循环怎样使用这次结果

主干节选：暂时省略计时、日志和失败处理，不是可独立运行的替代实现；完整循环在下方折叠保留。

```python
while True:
    result = await self.exec(hc.command, timeout_sec=int(hc.timeout_sec))
    if result.return_code == 0:
        return  # 通过，退出整个函数，回到 Trial._prepare。
    # 非零退出：按配置等待重试，或达到失败次数阈值后抛错。
```

当前先接清 **检查命令 → 环境执行 → 退出码 → 返回或重试**。等待策略只需知道：宽限期内失败不计数，之后失败达到阈值就抛错；具体秒数与计数过程按需展开。

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

| 按需进入的子函数卡 | 读完回到哪里 |
| --- | --- |
| [BaseEnvironment.exec（含 ExecResult）](../../02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.exec.md) | 回到本循环的 `result.return_code == 0`，接着看返回或失败分支；具体后端仍暂缓 |

**输出与返回位置**：正常返回类型是 None。没有检查配置或检查通过时，回到 [Trial._prepare](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-healthcheck-call)，继续 `_upload_injected_skills()`；失败次数达到配置阈值会抛出 HealthcheckError。这里不返回另一个环境对象，也不直接返回 ExecResult 给 Trial。

## 我的直接表述（原话）

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

## 尚不清楚

- 配置选择已经展示，用户尚未反馈具体理解。
- 当前通过 hello-healthcheck 静态示例解释命令来源、执行位置与退出码；用户是否接清仍待反馈。
- 完整循环保留作按需回查；宽限期和计数细节暂不作为当前主读重点。
- 目标环境的 exec 如何真正执行命令，按当前范围暂缓具体后端实现。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 Harbor 的 `git show v0.25.0:src/harbor/environments/base.py` 核对本方法；方法签名为 `async def run_healthcheck(self, healthcheck: HealthcheckConfig | None = None) -> None`。
- 调用方为 [Trial._prepare:641–658](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L641)。调用代码是局部节选，完整 try/finally 由父函数卡保留。
- 命令类型与约定：[HealthcheckConfig.command:358](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/config.py#L358)，shell 命令，退出码 0 表示健康。
- 示例配置：[hello-healthcheck/task.toml:27](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-healthcheck/task.toml#L27)；服务启动：[environment/entrypoint.sh](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-healthcheck/environment/entrypoint.sh)。只借用示例解释检查目标，没有展开或选定 Docker 后端实现。
- 本轮补齐配置选择之后的循环主体，日志省略但业务分支保留；材料完整性不代表用户已读完或掌握。未实际执行健康检查，也未取得运行结果。
- [Step 013：补齐 Trial 到健康检查卡的入口](../../04-flow.md#healthcheck-card-linked-from-trial-20261113)。

</details>
