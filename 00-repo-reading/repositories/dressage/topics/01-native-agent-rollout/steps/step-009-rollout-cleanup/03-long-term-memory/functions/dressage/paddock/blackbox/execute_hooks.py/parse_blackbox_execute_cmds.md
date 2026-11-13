> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# parse_blackbox_execute_cmds

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../step-005-agent-registration/03-long-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[dressage/paddock/blackbox/execute_hooks.py:45](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L45)。
- 首次单独展开：Step 001，2026-11-06。
- 最近认识更新：Step 001，2026-11-06；用户确认返回的是计划而非执行，且包含运行前后两阶段；按请求扩充心智模型。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 的主 try 开头，读取 metadata.blackbox_execute_cmds。
2. **具体内容**：校验阶段和命令配置，按 before_agent、after_agent 整理成命令对象元组；未配置时返回两组空元组。
3. **建议构建的心智模型**：

   > 把已经配置好的命令整理成“Agent 运行前做什么、运行后做什么”的计划。
   >
   > 1. **先整理计划，还不执行。** parse_blackbox_execute_cmds 读取并检查配置好的命令，返回执行计划，留给后面的执行函数使用。
   > 2. **既有运行前，也有运行后。** before_agent 可以用于准备文件、安装依赖；after_agent 可以用于收集结果。“前后”指 Agent 执行任务前后；后续真正执行这些命令时，沙箱已经可用。解析计划本身不要求此刻已创建沙箱。
   > 3. **不会自动把步骤填满。** 配置了什么，它就整理什么；没有配置的阶段就是空的，不会自行判断还需要安装哪些依赖。

4. **调用代码**：

   ```python
   execute_cmd_schedule = parse_blackbox_execute_cmds(
       metadata.get("blackbox_execute_cmds")
   )
   ```

## 本场景的输入与输出

教学输入：

```python
value = {
    "before_agent": [
        {"name": "prepare", "cmd": "mkdir -p /tmp/task-output", "required": True, "timeout": 30}
    ],
    "after_agent": [],
}
```

返回结构：字典有 before_agent、after_agent 两个键。前者是包含一个 BlackboxExecuteCmd 的元组，后者是空元组。命令对象保存 stage、name、cmd、timeout、required、stdout_limit；本例 stdout_limit 缺省为 None。不是退出码、stdout 或运行结果。

完整解析函数：

```python
def parse_blackbox_execute_cmds(value: Any) -> BlackboxExecuteCmdSchedule:
    if value is None:
        return _empty_schedule()
    if not isinstance(value, dict):
        raise ValueError(
            "metadata.blackbox_execute_cmds must be a dict with before_agent "
            "and after_agent command lists"
        )

    unknown_stages = sorted(
        str(stage) for stage in value if stage not in _ALLOWED_STAGE_SET
    )
    if unknown_stages:
        raise ValueError(
            "metadata.blackbox_execute_cmds contains unsupported stage(s): "
            + ", ".join(unknown_stages)
        )

    schedule: BlackboxExecuteCmdSchedule = {}
    for stage in EXECUTE_CMD_STAGES:
        raw_commands = value.get(stage, [])
        if not isinstance(raw_commands, list):
            raise ValueError(
                f"metadata.blackbox_execute_cmds.{stage} must be a list"
            )
        schedule[stage] = tuple(
            _parse_command(stage, index, raw_command)
            for index, raw_command in enumerate(raw_commands)
        )
    return schedule

```

1. 未配置（None）时，_empty_schedule 返回两个阶段的空元组。
2. 校验外层是字典、键是支持的阶段；每个阶段必须是列表。
3. 逐条交给 _parse_command 校验并构造命令对象，保持列表顺序，转换为元组。
4. 返回计划。缺少某个阶段相当于该阶段无命令；非法配置会抛 ValueError，而非默默跳过。

_parse_command 本轮只需要知道：name、cmd、required 必填，timeout、stdout_limit 可选；required 必须是布尔值。具体命令执行留到执行层，不为该辅助函数另建卡。

返回 generate 后，计划会分别以 stage="before_agent" 和 stage="after_agent" 交给 execute_blackbox_cmds_for_stage。注意它使用 metadata.blackbox_execute_cmds，区别于 env_args 中交给沙箱后端的 sandbox_cmd。


## 我的直接表述（原话）

> 这里我可以简单理解为
> 这里这里的parse blackbox execute cmds
> 在做的内容是需要在blackbox execute运行起来之前先跑起来的内容是我的理解
>
> 类似于一系列command的操作
> 是我的理解
> 用来收集也好
> 安装也好
> 是我的理解
>
> 这里把这个运行前的步骤填写满了是我的理解

助手澄清：安装依赖、准备文件或收集结果可以是用户配置的命令用途，但该函数本身只读取并校验已有命令，整理成计划，不执行，也不自动补齐任务所需步骤。计划包含 before_agent 和 after_agent 两个阶段，参照点是 Agent 运行。正常路径下，before_agent 命令执行时环境已经取得、Agent 已注册；因此它不是在沙箱或 BlackboxServer 启动前执行。当时尚待用户确认；后续确认见下方原话。

本轮后续确认：

> 这里返回的是计划
> 并不是执行
> 是吧命令写好
> 有运行前后的内容

用户随后要求把“整理不执行、前后两个阶段、不自动补齐步骤”三点补入心智模型。

## 尚不清楚

- 后续执行与注册的内部机制，本轮仅定位交接，未继续下钻。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 基于本地源码静态核对，示例为教学构造；未启动 Agent、沙箱或训练。
- [本步过程](../../../../../../../step-001-task-identity-and-parameters/04-flow.md)。

</details>
