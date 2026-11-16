# Trial._start_agent_environment

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码：[src/harbor/trial/trial.py · Trial._start_agent_environment](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 013，2026-11-13，用户确认从上层启动包装进入。
- 最近认识更新：2026-11-13，用户将其概括为完成后端沙箱构建；助手校准为通过后端 start 委派并等待准备，具体构建与启动在后端实现，内部仍未展开。

[调用方 _setup_agent_environment](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) → **Trial._start_agent_environment** → 已有环境对象的 start · [scope](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：上层已经发出环境启动事件、记录开始时间，现在要等待已有环境对象启动。
2. **具体内容**：将 force_build 传给环境 start，用已计算的超时值等待；遇到 asyncio.TimeoutError 时转换为 EnvironmentStartTimeoutError 并向上传递。
3. **建议构建的心智模型**：

   > 调用选定后端的 start，并在框架这一层统一限制启动等待时间、报告环境启动超时。

4. **调用代码**（上层的等待位置）：

   ```python
   try:
       await self._start_agent_environment()  # 当前进入这里。
   finally:
       self.result.environment_setup.finished_at = self._now()
   ```

## 本场景的输入与输出

### 带着什么进入？

完整来路为 Trial.run → _prepare → _setup_agent_environment → 当前函数。self.agent_environment 是初始化阶段已创建的同一个环境对象，当前调用它的 start；不用重新创建对象。上层已准备了环境启动的事件通知和计时记录。

本轮继续沿用 Docker 场景。为了直观看参数，下面假设 force_build=False、已计算的启动超时为 600 秒；这是静态输入示意，没有真实启动。

```text
self.agent_environment                   已选定后端的 Environment 对象
self.config.environment.force_build      False（示例设置）
self._environment_build_timeout_sec       600（示例设置）
```

超时值由前面的初始化准备，本函数直接使用；force_build 对具体后端构建行为的影响由其 start 实现决定，这里只看原样传参。

### 完整代码：调用 start → 等待 → 转换超时异常

保留原方法的全部语句，仅加旁注：

```python
async def _start_agent_environment(self) -> None:
    try:
        await asyncio.wait_for(
            self.agent_environment.start(        # [1] 调用已有环境对象的启动接口。
                force_build=self.config.environment.force_build
            ),
            timeout=self._environment_build_timeout_sec,  # [2] 使用已准备好的超时值。
        )
    except asyncio.TimeoutError as exc:
        raise EnvironmentStartTimeoutError(      # [3] 转成“环境启动超时”，向上报告。
            f"Environment start timed out after {self._environment_build_timeout_sec} seconds"
        ) from exc
```

- **启动的实际入口**：是 self.agent_environment.start(...)。wait_for 驱动并等待它；具体如何构建、创建和启动环境，由该对象对应的后端实现负责。
- **时间边界**：timeout 使用已有字段值；该值不是在本函数里重新计算的。本层只转换超时异常，没有执行资源清理；远端资源的处理需沿具体后端与上层清理路径核对。
- **错误交接**：捕获 asyncio.TimeoutError，抛出包含超时值的 EnvironmentStartTimeoutError；from exc 保留原始异常关系。其他未匹配的异常继续向上传播。

### 完成后交回什么？

| 情况 | 当前函数的结果 | 返回上层后 |
| --- | --- | --- |
| 环境 start 正常完成 | 返回 None | 上层 finally 写结束时间，随后 _prepare 继续 run_healthcheck |
| 捕获到 asyncio.TimeoutError | 抛出 EnvironmentStartTimeoutError | 上层 finally 仍写结束时间，异常继续向上传递 |
| 其他异常 | 当前方法不处理，继续传播 | 交给上层生命周期处理 |

本函数不返回新的环境对象，也不在这里安装 Agent。正常路径留下的是同一环境对象的启动副作用；后续健康检查仍是独立一步。当前阅读只到 start 接口，尚未展开具体 Docker/K8s 后端，也没有实际调用环境。

## 我的直接表述（原话）

用户确认继续：

> 好的 那么来看一下这个start agent environment吧

用户此前对上层委派关系的表述保存在[父函数卡](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md)。当前尚无对本函数内部的独立解释；上方说明由助手依据源码整理。

用户随后概括用途并询问接续：

> 简单来说就是通过这里这个函数来完成后端沙箱的构建是我的理解 那么是否适合看一下个部分了呢？

助手校准：从上层用途看，它发起并等待后端沙箱准备；本函数直接实现的是启动调用与超时处理，具体镜像构建、容器创建和启动属于后端 start。此前曾建议沿 Docker 示例看具体 start；用户随后明确目标为 K8s，已撤回该必读建议，后续按本步的 K8s 接入边界推进。

用户纠正后续后端的选择：

> 部队吧
> 我知道这里是这个start agent environment就是让这个对应的agent environment 本身开始构建
> 那么如果我知道我最后是通过k8s的话
> 那么这里的这个那么当前在这个scope中还需要看这个docker吗？

以目标后端决定继续阅读的位置：K8s 路线无需先通读 Docker 的启动实现。当前函数是后端无关的启动调用；后续先明确 Harbor BaseEnvironment 的接口，再核对目标 K8s/Agent Sandbox 的实际适配与调用。Docker 类的定位只保留为此前示例证据。

## 尚不清楚

- K8s / Agent Sandbox 路线具体通过哪个 Harbor Environment 适配类接入，需按实际配置与实现核对；不将已有 UpstreamK8sSandbox 名称视为已接通证据。
- force_build 在具体后端如何影响构建策略。
- 启动超时或其他失败后，后端资源是否已创建、如何被清理，需沿相关失败路径核对。

<details>
<summary>来源与验证边界</summary>

- [官方固定版本 trial.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)：核对当前函数、上层计时包装、_prepare 中的健康检查位置。当前按固定版本符号定位，不使用网页重排行号代替原文件行号。
- 600 秒与 force_build=False 为帮助阅读的静态设置；不是运行结果，也没有测试实际超时、取消、Docker 或 Kubernetes 资源状态。
- 本次下一入口定位：[环境工厂注册](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/factory.py)的 Docker 类型对应 DockerEnvironment；[具体 start](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/docker/docker.py)位于 docker/docker.py。本轮只核对类型与入口，未新建该函数卡。
- [本轮过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#start-agent-environment-entry-20261113)。

</details>
