# BaseEnvironment.stop

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/environments/base.py/BaseEnvironment.stop.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.stop.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码定位：[src/harbor/environments/base.py:1112–1113](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1112)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独记录：Step 013，2026-11-13，用户确认本轮接口建卡范围。
- 最近认识更新：尚无针对本接口的个人复述；以下为 LLM 静态核对，建卡不代表已掌握。

[Trial._finalize：收尾](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline) → _stop_agent_environment → **stop 接口** · [scope 3C](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md#reading-sequence)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：执行或收尾阶段需要停止 Agent 环境；当前从已读 Trial._finalize 回查 _stop_agent_environment 的委派。
2. **具体内容**：接收 delete，约定停止环境并可选删除；基类没有资源操作代码，也没有标注返回类型。
3. **建议构建的心智模型**：

   > 调用方决定何时停止和是否要求删除，具体后端把请求落实到其环境资源。

4. **调用代码**：Trial._stop_agent_environment:2043–2047，正常路径真实节选；已有标记检查及异常处理暂略。

   ```python
   await asyncio.shield(
       self.agent_environment.stop(delete=self.config.environment.delete)
   )
   self._is_agent_environment_stopped = True  # 正常路径：委派完成后登记。
   ```

## 本场景的输入与输出

这里已经离开准备阶段；沿收尾调用回查接口。shield 是上层等待包装，不是 stop 抽象接口本身的资源实现，本轮不展开取消机制。

### 接口与输入

下面为固定版本的完整抽象方法声明。实际调用选定后端对象的方法；不会先由这段声明转发到后端。

```python
@abstractmethod
async def stop(self, delete: bool):
    """Stops the environment and optionally deletes it."""
```

| 输入 | 当前调用现场与接口要求 |
| --- | --- |
| self | 本次 Trial 使用的具体环境对象 |
| delete: bool | 来自 self.config.environment.delete；控制停止时是否同时要求删除环境 |

### 输出与返回位置

副作用合同：停止环境，按 delete 请求可选删除。接口未标注返回类型，调用方只等待并更新自己的标记，不接收 TrialResult。delete=False 的保留/重用细节由后端决定；未验证任何资源已经释放。

本例返回 _stop_agent_environment，再回到 _finalize 补结束时间、写结果和发 END。环境也可能已在执行阶段停止，已有标记时 helper 会跳过；无需重新阅读整个 Trial.run。

## 我的直接表述（原话）

尚无针对本接口的职责或机制的直接复述。本轮已确认建立这些接口卡片；确认原话统一保存在 [Step 013 形成过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)，不将授权建卡记成个人技术结论。

## 尚不清楚

- 目标 Agent Sandbox 后端停止/删除的资源范围、完成条件与重复调用行为。
- 取消和失败时真实资源是否释放，留到实施验证；不能单凭 stopped 标记判断。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 `/home/fredkeira/projects/harbor` 的 `git show v0.25.0:src/harbor/environments/base.py`，通过 AST 核对方法签名、文档和行号；未混用当前 main。
- [_finalize 的调用和后续结果处理](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L660)：仅核对本页调用现场。
- [_stop_agent_environment 的标记、shield 和异常边界](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L2039)：仅核对本页调用现场。
- 接口与调用代码均为静态源码材料；调用节选已标注所在分支，变量值未通过真实运行取得。没有选定或执行任何具体后端，也没有启动沙箱、安装 Agent 或操作集群。
- [Step 013 本次建卡与边界](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)。

</details>
