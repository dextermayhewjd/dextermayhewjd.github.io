# E2BSandbox.__aexit__

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/sandbox.py:302–307](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L302-L307)，由助手核对。
- 首次接触：Step 2，2026-10-21，最初在 `_grade_scaleswe` 的退出交接中定位，随后展开完整实现；本轮移为独立卡片。
- 最近认识更新：尚无用户对本函数行为的直接解释；已有 LLM 说明和验证从父卡归入本页，移动不代表新增理解。

- 本次继承自：[Step 2 的完整记录](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：本例 `_grade_scaleswe` 已完成评分，准备从 `async with E2BSandbox(image) as ev` 内返回。Python 等待本方法执行完退出处理，之后调用方才能接到评测结果。

2. **具体内容**：检查进入时保存的 SDK 对象 `self._sb`；存在时等待其 `kill()` 调用，尝试回收远端沙箱。捕获到回收异常时记录 warning，本方法自身返回 `None`。

3. **建议构建的心智模型**：

   > `__aexit__` 使用进入时保存的 SDK 对象，在离开上下文时尝试回收对应沙箱。
   >
   > 它处理环境退出，不接收或重新计算评分；退出处理完成后，父函数继续交回已有结果。

4. **调用代码**（`_grade_scaleswe`，仅保留当前退出语境）：

   ```python
   async with E2BSandbox(image) as ev:
       ...  # 已完成环境准备、补丁应用与评分
       return EvalResult(r, True)
   # 离开上下文时由 Python 调用并等待 __aexit__。
   ```

## 本场景的输入与输出

承接 [_grade_scaleswe](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md#environment-exit) 的教学成功例。父函数已形成 `EvalResult(1.0, True)`；这是退出时的背景结果，不是本方法的实参。未运行真实沙箱。

**输入：同一个环境操作对象，以及退出时的异常信息。**

| 输入 | 本例的值或状态 |
| --- | --- |
| `self` | 当前的 `ev`，即原来的 `E2BSandbox` 对象 |
| `self._sb` | `__aenter__` 保存的 SDK 对象，用于操作已创建的远端沙箱 |
| `self.sandbox_id` | 教学标识 `"demo-sandbox-001"`，用于回收失败时的日志 |
| `exc_type`、`exc`、`tb` | 正常返回时均为 `None`；本实现没有读取这三个参数 |

**输出与副作用：**

- 本方法直接返回 `None`。
- 通过 SDK 请求回收对应远端沙箱，并等待调用结束；本方法没有把本地 `_sb` 或 `sandbox_id` 清空。
- 正常退出后的外层结果仍为 `EvalResult(1.0, True)`，由 `_grade_scaleswe` 交回，不会被本方法返回的 `None` 替换。

**输入怎样得到上述结果（`sandbox.py:302–307`，完整方法）：**

```python
async def __aexit__(self, exc_type, exc, tb) -> None:
    try:
        if self._sb is not None:
            await self._sb.kill()
    except Exception as e:
        logger.warning("[agent.sandbox] kill %s failed: %s", self.sandbox_id[:8], e)
```

- **已有对象 → 回收调用**：`self._sb` 存在时，调用它的 `kill()`；若为 `None`，跳过回收调用。
- **`await` → 等待退出处理**：本方法等待 SDK 调用结束，调用方随后才接到评测结果；SDK 如何在服务端销毁环境暂不展开。
- **回收异常 → 日志**：被 `except Exception` 捕获的异常会记为 warning，原评分仍可返回。因此收到评分不证明远端一定已成功销毁。
- **返回 `None` → 保留外层控制流**：正常路径继续返回父函数已有结果；如果评测块原本抛出异常，本方法也不会将它压下或改成零分。异常与取消的更细边界见参考。

读完回到 [_grade_scaleswe 的退出交接](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md#environment-exit)：退出完成后，评测结果经 `run_evaluation` 返回给 `generate`。

## 我的直接表述（原话）

用户对记录归属提出纠正：

> 但是这个和sandbox相关的代码为什么不放在sanbodx的aexit里面呢？

这条表述针对卡片分工，尚不代表对本函数行为的理解确认。

## 尚不清楚

- SDK 的 `kill()` 如何与服务端通信、怎样确认远端环境已销毁，尚未展开或实测。
- 回收过程被取消时如何处理，以及其他部署后端的生命周期实现，未在本轮验证。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`，`sandbox.py:298–307`；退出语境 `swe.py:269–287`，返回交接 `swe.py:239–247` 与 `generate.py:215–219`。
- 原始讲解：[Step 2 的退出与返回讨论](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#evaluation-context-exit)；记录归属纠正：[从父卡移入本函数](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#aexit-record-ownership)。
- 已有验证：Python 3.12.3 下提取真实评测编排、结果类和本方法，使用替身核对正常返回、补丁失败提前返回、回收异常和评测异常四条路径；未调用真实沙箱、应用补丁或运行测试命令。本轮归档不重算首次接触或新增运行证据。
- [语言依据、双语引文与验证范围](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/references/sandbox-entry.md#async-with-exit)；[进入阶段的对象来源](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)。

</details>
