---
title: "S07.9 Integration：把 Skills 接回 Agent Loop"
weight: 90
summary: "学完独立机制后，回顾 S06，再用总图和伪代码说明目录、调用与正文交付如何进入原循环。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

前八节已经分别解释了 Skills 的内容、入口、交付和执行边界。现在回到 [独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map)，把 B、C、D、F 接入已有 Agent 系统。

**比较范围：** 下面沿用 S06 的教学骨架，加入基于公开行为设计的 Skills 接口。颜色比较的是本次教学设计中的机制变化，不是 Claude Code 内部源码的版本差异；本地 S07 脚本是另一个更小的机制示例。

本节的可运行的教学轨迹脚本、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-tools-trace-inline-py)。

## 1. 先回顾 S06 的整体结构

{{< architecture from="/projects/learn-claude-code/s06" src="images/subagent-flow.svg" mode="baseline" modified="history,model,tools" folded="task,child-history,child-loop,child-return,child-context,workspace" label="回顾 S06：保留原结构，标出上下文接口和将简记的已学子循环" caption="图 1：沿用 S06 的节点和连线。橙色标出本轮扩展的请求上下文与调用入口；灰色虚线提示已讲过的子 Agent 细节将在下一张用 S06 索引简记，功能概念没有被删除。" >}}

这里保留的是已学过的循环关系：模型提出行动、程序处理调用、结果回到历史。S06 的子循环内部已经讲过，本节不再把它完整铺开。

## 2. 把 Skills 的三个接口接回去

{{< architecture from="/projects/learn-claude-code/s07" src="images/skills-agent-integration.svg" legend="evolution" label="Skills 目录进入请求，用户或模型发起调用，正文回到当前上下文，原工具循环继续" caption="图 2：紫色分支对应独立总图的 B、C、D。目录扩展请求上下文，调用准备正文，交付让后续模型请求看到新指令；灰色虚线表示入口关联。旧工具维持小框简记，正文要求的实际操作仍由原工具循环执行。" >}}

| 接入点 | 来自独立机制图 | 对原循环的影响 |
|---|---|---|
| 请求模型时的可见信息 | B 技能目录 | 模型知道有哪些可用方法，不必先读全部正文 |
| 用户输入或模型调用的处理 | C 调用入口 | 两种入口确定同一个目标 Skill，经过各自适用的调用检查 |
| 后续模型请求所用的上下文 | D 正文交付 | 加入工作指令，模型可以据此继续行动 |
| 后续普通工具调用 | F 按需资源 | 需要时读取参考文件或运行脚本，结果继续进入当前执行上下文 |

这里的紫色箭头表达内容流，不能把它读成绕过工具权限、Hook 或 API 消息配对的捷径。模型发起的工具调用仍需收到匹配结果；用户直接点名则由命令入口处理，不需要伪造一次模型工具调用。

图 2 先展示默认 inline 路径。需要 `context: fork` 时，正文交付到子上下文，再按对应配置返回结果；目标与等待方式见 [S07.7]({{< relref "/projects/learn-claude-code/s07/07-subagents.md" >}})。这一选择不要求把所有 Skill 都改成 Subagent。

## 3. 用伪代码追踪同一份内容

下面是**本专题的教学设计**，不是官方内部函数。它只展开默认 inline 路径；消息角色、Skill 工具协议、去重以及临时权限的具体实现由运行环境决定。

先把正文准备写成一个有明确输入、输出的过程：

```python
def prepare_inline_skill(name, arguments, caller, session):
    skill = registry.resolve(name)
    check_invocation_policy(skill, caller, session)

    body = read_skill_body(skill)
    body = substitute_arguments(body, arguments)

    # 仅在正文包含动态命令时执行；命令也要经过适用的权限检查。
    body = prepare_optional_dynamic_context(body, session)
    return PreparedInstructions(skill=skill, content=body)
```

准备正文不等于执行正文中的自然语言步骤。例如“查看 git diff”这句普通指令，还要等模型接收到它后请求工具。动态命令的预处理路径则已在 S07.5 单独讨论。

用户点名时，调用入口已经确定：

```python
request = parse_user_input(user_input)

if request.is_direct_skill:
    instructions = prepare_inline_skill(
        request.skill_name, request.arguments, caller="user", session=session
    )
    session.deliver_direct_skill(request, instructions)
else:
    session.append_user_message(user_input)
```

模型自行选择时，调用发生在原来的工具处理阶段：

```python
while True:
    request_context = assemble_context(
        session=session,
        skill_descriptions=registry.visible_descriptions(session),
    )
    response = ask_llm(request_context, enabled_tools(session))
    session.append_assistant_message(response)

    calls = extract_tool_calls(response)
    if not calls:
        if continue_from_stop_hook(session):
            continue
        break

    results = []
    instruction_deliveries = []

    for call in calls:
        if is_skill_invocation(call):
            blocked = check_tool_call_with_pre_hooks(call, session)
            if blocked:
                results.append(tool_error_result(call.id, blocked))
                continue
            try:
                instructions = prepare_inline_skill(
                    call.skill_name, call.arguments,
                    caller="model", session=session,
                )
            except SkillInvocationError as error:
                result = tool_error_result(call.id, error)
                run_post_tool_hooks(call, result)
                results.append(result)
                continue
            # 本例返回匹配原调用的加载确认，正文单独交付一次。
            result = skill_loaded_ack(call.id, call.skill_name)
            run_post_tool_hooks(call, result)
            results.append(result)
            instruction_deliveries.append(instructions)
        else:
            results.append(execute_with_existing_hooks(call))

    # 先完成这一批调用的结果，再开始下一次模型请求。
    session.complete_tool_turn(results)
    session.deliver_skill_instructions(instruction_deliveries)
```

这里将“匹配调用结果”和“交付指令”分开命名，便于检查接口；本例的确认结果不含完整正文。如果某个平台直接在工具结果中承载正文，就不要再重复交付。消息封装不表示官方一定有两个同名步骤；权限与 Hook 的具体策略按 S07.6 接在应用边界上。调用失败返回错误并停止本次装载，不能按“正文已经交付”继续。

目录来自发现阶段的当前状态，并不意味着每次循环都重新扫描磁盘。调用后的正文会成为后续可见信息，普通参考文件和脚本仍按任务需要取用。[官方内容生命周期](https://code.claude.com/docs/en/skills#skill-content-lifecycle)

## 4. 本地教学代码怎样对应

当前本地 `s07_skill_loading/code.py`（`ce8f9f1`）提供了更具体、范围更小的实现：

| 教学设计中的职责 | 本地代码 |
|---|---|
| 发现并建立技能索引 | `SkillLoader.scan()` |
| 生成名称与描述目录 | `SkillLoader.catalog()`，加入 `build_system_prompt()` |
| 按名字取得完整内容 | `SkillLoader.load(name)` |
| 模型发起加载 | `load_skill` 工具与分发表 |
| 内容回到模型 | 原循环构造 `tool_result` 并追加消息 |

它没有实现本专题讨论的所有现代分支，例如用户命令路由、动态渲染、现代调用控制或 fork。也不能将其未注册 `task` 理解成 Skills 原理排斥子 Agent。

因此，我读教学代码时追踪“目录与全文如何分开交给模型”；读现代文档时再补充实际产品的入口、上下文和执行配置。两份材料回答的层次不同。

## 我现在怎样判断自己理解了

拿一个具体 Skill，能说清下面四件事：

1. 调用前模型知道哪些信息？
2. 这次由谁发起，正文交到哪个上下文？
3. 哪些指令由模型落实，哪些内容由应用预处理？
4. 工具结果、最终报告和后续上下文分别怎样继续？

**Skills 改变了模型能够按需获得的方法与指令；这些内容最终仍要通过一个执行上下文和它的 Agent Loop 发挥作用。**

[上一节：完整案例与评估]({{< relref "/projects/learn-claude-code/s07/08-evaluation.md" >}}) · [下一节：完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}})
