# SunabakoSandbox.__aexit__

- 源码定位：[examples/coding_agent_rl/sunabako_sandbox.py:84–103](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L84-L103)。
- 首次接触：Step 006，2026-10-24，从 `boot_agent_sandbox:164` 的退出调用进入。
- 最近认识更新：2026-10-24，用户串起先保存内容、再退出环境的顺序；保存条件、产物范围与保存失败后仍尝试回收，由助手校准。

[前一段：__aenter__](SunabakoSandbox.__aenter__.md) · [父函数的退出交接](../generate.py/boot_agent_sandbox.md#3-交给调用方使用退出时回收160164)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：调用方用完执行环境，`boot_agent_sandbox` 进入 `finally`；安装失败时也会调用本方法清理候选环境。
2. **具体内容**：已有 SDK 操作对象时，按配置保存产物，再请求回收；之后将一种已停止环境的 SDK 错误转换成 Slime 的异常。
3. **建议构建的心智模型**：

   > 用进入时保存的操作入口收尾：需要时先取回产物，再请求回收环境。

4. **调用代码**（父函数 `160–164`，省略追踪包装）：

   ```python
   try:
       yield sb
   finally:
       await sb.__aexit__(*sys.exc_info())
   ```

## 本场景的输入与输出

沿用同一个 `cand`，父函数通过 `sb = cand` 交给调用方。主例正常使用结束、未设置 `SUNABAKO_ARTIFACTS` 和 `SUNABAKO_DEFER_ROOTFS_DELETE`。

- **输入**：`self._sandbox` 已保存 SDK 操作对象；正常退出时 `exc_type`、`exc`、`tb` 都是 `None`。产物目录与延后清理选项从主机环境变量读取。
- **输出与作用**：正常完成返回 `None`，通过 SDK 请求回收环境；本地 `_sandbox`、`sandbox_id` 等字段仍保留。
- **本例实际路径**：跳过产物保存，等待 `kill(defer_cleanup=False)` 完成，再返回父函数。

### 1. 用已有操作入口保存产物并请求回收（84–93）

以下为源码前半段，仅添加注释：

```python
async def __aexit__(self, exc_type, exc, tb) -> None:
    if self._sandbox is None:
        return  # 没有保存 SDK 操作对象，直接结束
    try:
        if destination := os.environ.get("SUNABAKO_ARTIFACTS"):
            await self._save_artifacts(Path(destination) / self.sandbox_id)
    except Exception:
        logger.exception("[sunabako] could not save artifacts for %s", self.sandbox_id)
    finally:
        await self._sandbox.kill(defer_cleanup=os.environ.get("SUNABAKO_DEFER_ROOTFS_DELETE") == "1")
```

- **先取回，再回收**：设置 `SUNABAKO_ARTIFACTS` 时，在本机按沙箱编号保存指定的记录和日志文件；这里不保存整个执行环境的快照。未设置时直接进入回收。
- **保存失败仍尝试回收**：普通保存异常被记录；`finally` 中继续调用 `kill`。`kill` 自身抛出的异常会向外传播，不能把发出请求等同于已验证回收成功。
- **操作对象保留**：此处没有把 `_sandbox` 设回 `None`。对象还在，不意味着对应环境仍能使用。

<details>
<summary>产物内容与延后清理选项</summary>

`_save_artifacts` 保存创建清单、命令记录、可取得的状态及轨迹／安装／评测日志。输出目录位于运行 Slime 的主机；部分文件通过 SDK 从执行环境读取。`_commands` 的产生属于后续 `exec`，本轮只接清收尾时的用途。

`SUNABAKO_DEFER_ROOTFS_DELETE="1"` 时向 SDK 传入 `defer_cleanup=True`；具体延后删除的时机与实现由后端决定，本轮不推断其内部行为。

</details>

### 2. 回到父函数的退出交接

主例的 `exc` 是 `None`，后半段异常转换不触发。方法正常返回后，父函数结束本次沙箱使用期；外层 `_generate:301` 随后进入独立评测。

<details>
<summary>异常退出时的一种错误转换（94–103）</summary>

源码在 `kill` 正常完成后，继续检查传入的异常：

```python
if exc is not None:
    from sunabako import SandboxError

    if isinstance(exc, SandboxError):
        try:
            response = json.loads(str(exc))
        except ValueError:
            response = None
        if isinstance(response, dict) and response.get("error") == "sandbox must be running":
            raise SandboxTerminatedError(response["error"]) from exc
```

只有满足这一 SDK 类型与错误内容的异常才转换为 `SandboxTerminatedError`。其他原异常由外层继续传播，本方法不返回 `True` 来表示抑制异常。若 `_sandbox` 为 `None`，前面的直接返回也会跳过这一转换。

</details>

## 我的直接表述（原话）

2026-10-24，三个方法连读后的表述节选：

> 3.最后这里的sandbox部分在推出的时候是先把这里的内部的东西存储起来了之后在考虑推出这个environment
> 这是我的理解

完整原话与保存条件、产物范围、失败后仍尝试回收的澄清见[本轮反馈](../../../../../04-flow.md#sunabako-lifecycle-restatement)。用户已表达先保存再退出的顺序，尚未确认这些细分条件；此前[范围确认](../../../../../04-flow.md#sunabako-lifecycle-methods)保留。

## 尚不清楚

- SDK 的 `kill` 如何完成回收、延后删除怎样执行；取消和清理失败的完整行为。
- 实际部署中的产物内容与回收结果，本轮没有真实运行证据。

<details>
<summary>源码与验证范围</summary>

- 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；退出与异常转换按静态源码核对。
- 产物辅助实现见同文件 [105–124](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L105-L124)，只核对调用结果与保存位置。
- 本轮未执行 SDK 回收或读取真实沙箱产物；[连读过程](../../../../../04-flow.md#sunabako-lifecycle-methods)区分助手解释与用户反馈。

</details>
