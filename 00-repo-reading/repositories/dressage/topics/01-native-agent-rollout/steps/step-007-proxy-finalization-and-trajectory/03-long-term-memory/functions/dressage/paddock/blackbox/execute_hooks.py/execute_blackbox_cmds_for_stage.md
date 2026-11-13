# execute_blackbox_cmds_for_stage

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 02-short-term-memory 记录](../../../../../../../step-005-agent-registration/02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[Step 005 scope · 第 2 项](../../../../../../../step-005-agent-registration/01-scope.md#reading-navigation) → **本函数** → 返回 generate，继续 Proxy 会话登记。

> 从已经整理好的计划中，取出当前阶段的命令，依次执行。

<details>
<summary>函数定位、心智模型与调用处</summary>

- 源码：[execute_hooks.py:77](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L77)。
- 首次单独展开：Step 005，2026-11-07。
- 最近认识更新：本轮为助手的源码说明，尚无用户对本函数的独立表述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 已完成 Agent 注册，调用本函数执行 before_agent。Agent 返回后也会以 after_agent 调用同一函数。
2. **具体内容**：检查阶段名，在 schedule 中取出命令，逐条 await 执行辅助函数。
3. **建议构建的心智模型**：

   > parse_blackbox_execute_cmds 整理计划，本函数按阶段兑现计划；配置了什么才执行什么。

4. **调用代码**，来自 generate:242：

   ```python
   await execute_blackbox_cmds_for_stage(
       paddock,
       state,
       metadata,
       schedule=execute_cmd_schedule,
       session_id=session_id,
       stage="before_agent",
   )
   ```

</details>

## 沿代码看本次执行

以下是完整函数，只添加说明。输入沿用本次任务已经取得的 paddock/state、会话 ID、metadata 和解析后的命令计划；当前 stage 为 before_agent。

当前位置需要区分：注册成功说明 BlackboxServer 已准备好运行所选 Agent 的配置，具体题目还要等后面的 call_agent(messages=...) 才提交。CLI 的安装由此前环境准备负责；这里执行的是已配置的前置命令。

```python
async def execute_blackbox_cmds_for_stage(
    paddock: Any,
    state: Any,
    metadata: dict[str, Any],
    *,
    schedule: BlackboxExecuteCmdSchedule,
    session_id: str,
    stage: str,
) -> None:
    # 当前支持 before_agent 和 after_agent；名字不合法则报错。
    if stage not in _ALLOWED_STAGE_SET:
        raise ValueError(f"unsupported execute_cmd stage: {stage}")

    # 本次只取 before_agent；没有命令就直接结束。
    for command in schedule.get(stage, ()):
        # 一条完成后再执行下一条，不在这里并行派发。
        await _execute_blackbox_cmd(
            paddock,
            state,
            metadata,
            session_id=session_id,
            command=command,
        )
    # 正常隐式返回 None；执行记录由下层追加到 metadata。
```

下层调用现有 `paddock.execute_cmd`，在本次沙箱内执行命令，并把输出/错误摘要追加到 `metadata["execute_cmds"]`。例如命令计划要求创建任务文件，此处才会真正执行；本函数不自行决定需要安装哪些依赖。

必须成功的命令失败时，下层抛出异常，后续流程不会继续到 Agent 执行；可选命令失败则保留记录并继续。这是已有辅助函数的行为，不是上面 for 循环自动具有的规则。

**本次返回位置：** generate:250，取得 `proxy_client.register_session_context`。当前函数返回 None，调用方不接收新的环境对象。

### 下一小段读哪些辅助函数

| 入口 | 当前建议深度 |
| --- | --- |
| [_execute_blackbox_cmd](_execute_blackbox_cmd.md) | 当前下钻：向已有沙箱发命令、记录结果、按 required 判断是否中止 |
| `_execute_cmd_result_summary`、`_execute_cmd_failed` | 随调用看用途即可：整理输出摘要，以及依据退出码和超时判断失败 |
| `_empty_schedule`、`_parse_command` | 属于此前解析计划阶段，不是本次执行阶段要顺序重读的函数 |
| 文本截断、异常摘要、JSON 转换辅助函数 | 先按格式整理工具理解，不继续下钻 |

用户已确认这一顺序，现为 `_execute_blackbox_cmd` 单独建卡。沿它调用的 paddock.execute_cmd 看清接口交接后，返回当前循环；其他解析和格式工具不继续展开。

<details>
<summary>原话、未知与源码依据</summary>

## 我的直接表述（原话）

> 好的 那么我们现在看完原来的部分吧看一下原来的这里的step 005吧

这是恢复本步的请求，不作为已理解本函数的证据。此前已经区分命令解析与执行，本轮尚无新的独立复述。

后续定位与疑问：

> 我们之前看的内容是这里的 paddock register agent对吗?
> 这里目前已经安装完了
> 也就是一个claude已经知道了目前需要做什么内容是我的理解
> 一系列setting啊什么的都做好了
>
> 那么现在需要做看的内容就是这里的execute black cmd for stage对吗?
> execute_blackbox_cmds_for_stage
> 现在是否需要看下面的这几个函数呢?

助手校准：配置准备与题目提交分开；register 不负责本次安装，也尚未调用 Claude 解题。用户已定位到前置命令阶段，但对下一处下钻的范围仍在确认。

## 尚不清楚

- 命令请求经过客户端/服务端后怎样启动具体进程，当前只按现有 execute_cmd 接口理解。
- 用户对 required 命令失败与可选失败的区别尚待反馈。

## 来源与验证

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- [_execute_blackbox_cmd 卡片](_execute_blackbox_cmd.md)保留本次下钻说明与固定源码，负责 execute_cmd 委派、执行记录与失败判断。
- [本步接续记录](../../../../../../../step-005-agent-registration/04-flow.md#resume-step005-registration-tail)。只做静态核对，没有执行沙箱命令。

</details>
