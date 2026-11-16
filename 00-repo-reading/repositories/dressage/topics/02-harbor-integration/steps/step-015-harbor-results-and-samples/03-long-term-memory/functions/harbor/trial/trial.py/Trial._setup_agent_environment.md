# Trial._setup_agent_environment

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码：[src/harbor/trial/trial.py · Trial._setup_agent_environment](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 013，2026-11-13。
- 最近认识更新：2026-11-13，用户已表述 _prepare 调用本方法、本方法再委派 _start_agent_environment；当前追问实际 start 的时机。

[调用方 Trial._prepare](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) → **Trial._setup_agent_environment** → _start_agent_environment（下层启动入口，尚未展开） · [scope](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：环境对象已经创建，Trial 已进入 run 的准备阶段，需要启动运行环境并记录这段过程。
2. **具体内容**：发出 ENVIRONMENT_START 事件，建立环境准备的计时记录，等待下层启动；进入 try 后，无论启动正常返回还是抛出异常，退出时都记录结束时间。
3. **建议构建的心智模型**：

   > 给环境启动过程加上事件通知和计时，真正的启动工作交给 _start_agent_environment。

4. **调用代码**（Trial._prepare 中的相邻位置）：

   ```python
   await self._setup_agent_environment()          # 当前进入这里。
   try:
       await self.agent_environment.run_healthcheck()  # 正常返回后继续这里。
       await self._upload_injected_skills()
       # 后面的 Agent 准备暂略。
   finally:
       self._write_stream_handle()
   ```

## 本场景的输入与输出

### 从对象创建走到运行准备

沿用前面的 hello-world / Docker 静态场景。上一个函数已经设置 self.agent_environment，但尚未执行环境 start。构造流程完成后，队列调用 trial.run()，后者先 _init_result()，再进入 _prepare()，由它调用当前方法。

```text
已有的输入状态：
self.agent_environment  ← 构造时创建好的 Environment 对象
self.result             ← Trial.run 已初始化的本次结果对象
self._hooks             ← 已登记的生命周期回调
```

这里的 self.result 与构造器中 _result=None 的时刻不同：现在已经进入运行阶段，有对象可供写入准备过程的计时信息。

### 完整方法：通知 → 计时并等待 → 记录结束

下面保留原方法的全部语句，只增加旁注；不是独立运行示例。

```python
async def _setup_agent_environment(self) -> None:
    await self._emit(TrialEvent.ENVIRONMENT_START)  # [1] 通知已登记的回调：开始环境准备。
    self.result.environment_setup = TimingInfo(started_at=self._now())  # [2] 记录开始时间。
    try:
        await self._start_agent_environment()     # [3] 委派并等待启动，本层不实现具体后端。
    finally:
        self.result.environment_setup.finished_at = self._now()  # [4] 记录这次启动尝试结束的时间。
```

- **事件通知**：_emit 按当前事件调用已登记的回调；这里先知道通知位置，不重复展开 hooks 的存储与触发机制。
- **结果记录**：environment_setup 保存 TimingInfo；它记录这段准备过程，不重新创建整个 TrialResult。
- **等待启动**：await 的下层入口是 _start_agent_environment。具体的环境 start 调用与超时包装已在[下层函数卡](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md)接续。
- **结束时间**：finally 记录启动尝试何时结束。即使下层启动报错，这里也会写结束时间，然后异常继续向上传播；有 finished_at 不等于启动成功。若前面的事件通知就抛错，则尚未进入这段计时与 try/finally。

### 留下什么，返回哪里？

以下只是正常完成路径的字段示意，t0/t1 没有真实运行数值：

```text
self.result.environment_setup: TimingInfo
├─ started_at: t0
└─ finished_at: t1

正常返回：None
执行影响：已等待下层启动完成；self.agent_environment 仍是同一个环境对象
```

正常返回 _prepare 后，下一行才做 run_healthcheck，随后上传配置的 skills 并准备 Agent。健康检查与 Agent.setup 不在当前方法内。启动异常则不会沿这条正常路径继续，具体失败记录与清理由上层已有生命周期处理。

**继续下钻时：**从上面 await self._start_agent_environment() 进入[当前子函数卡](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md)，返回本层 finally 写结束时间，再回 _prepare 的健康检查。

## 我的直接表述（原话）

用户确认本轮入口：

> 好的 那么我们来看一下这里的这个setup agent environment吧

用户随后表述调用关系并追问：

> 好的 我差不多理解了
> 这里是这个在preapare之列先运行这个setup agent environment
> 这里价单给出委派的这个start agnet environment
> 是我理解的
> 然后就是等具体这个agent environment start 是什么时候开始的了？
>
> 看一下我们下一个需要哦看的函数把

用户已说清 _prepare → _setup_agent_environment → _start_agent_environment 的委派关系。下一处推荐从当前 await 进入 _start_agent_environment，看它怎样通过 wait_for 驱动并等待已有环境对象的 start，以及怎样处理超时。推荐不等于已阅读其实现；事件和计时的用途仍保留助手说明。


## 尚不清楚

- _start_agent_environment 的调用、参数与超时已单独建卡；具体后端 start 和清理行为仍未展开。
- ENVIRONMENT_START 的各个回调在本次运行中做什么，本轮只认通知位置。
- Docker 或其他后端怎样实际启动、判定可用与处理失败，后续按选定分支阅读。

<details>
<summary>来源与验证边界</summary>

- [官方固定版本 trial.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)：本轮核对 Trial.run、_prepare、_setup_agent_environment 和其下层入口的调用位置。使用 v0.25.0，网页重排行号不替代原文件行号。
- 本例沿用已读的 hello-world / Docker 场景，只说明调用与字段变化；没有调用真实 start、创建 Docker/Pod、安装 Agent 或运行模型。t0/t1 为示意时间。
- [Step 013 本轮过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#setup-agent-environment-entry-20261113)。

</details>
