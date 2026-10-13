---
title: "S07.6.5 执行前先验证计划"
weight: 50
summary: "把准备执行的计划保存为中间数据，先与真实输入核对，再进行实际操作。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

本节对应 [Plan-validate-execute](https://agentskills.io/skill-creation/best-practices#plan-validate-execute)，重点是把一部分错误提前到执行之前发现。

## 问题

填写一份 PDF 表单时，Agent 根据用户要求准备填入 `signature_date`，但表单实际字段叫 `signature_date_signed`。

如果直接执行，错误会在填表过程中暴露；批量操作还可能已经处理了一部分文件。

仅仅“先写一份计划”也不能解决字段不匹配。计划需要与实际输入核对。

## 解决方案

为流程增加两个明确的中间产物：

| 文件 | 表示什么 | 谁提供依据 |
|---|---|---|
| `form_fields.json` | 表单真实存在的字段、类型和必填信息 | 从输入 PDF 中提取 |
| `field_values.json` | 准备向哪些字段写入什么值 | 根据用户要求生成的计划 |

验证器比较这两份数据，检查字段是否存在、类型是否兼容、必填项是否遗漏。验证失败就修改计划，再次验证；通过后才进入填表步骤。

## 最小示例

下面保留官网流程中的命令、参数顺序与文件名，补成中文 `SKILL.md` 教学示例。官网该段没有附带这些脚本的完整实现，本仓库也未实现这组 PDF 工具；这里用于解释流程关系，不能直接当作可运行练习包。

````markdown
---
name: fill-pdf-form
description: 根据用户提供的值填写 PDF 表单，填写前检查字段映射是否符合实际表单。
---

1. 提取实际字段：
   ```bash
   python scripts/analyze_form.py input.pdf
   ```
   将结果保存为 `form_fields.json`，其中包含字段名、类型与必填信息。

2. 根据用户要求生成 `field_values.json`，记录准备写入的字段与值。

3. 验证填写计划：
   ```bash
   python scripts/validate_fields.py form_fields.json field_values.json
   ```

4. 验证失败时，根据具体错误修改 `field_values.json`，再次运行验证。

5. 验证通过后填写表单：
   ```bash
   python scripts/fill_form.py input.pdf field_values.json output.pdf
   ```
````

这里的关键动作是第 3 步。它提供了可检查的依据，而不只是让 Agent 再想一遍“计划是否合理”。

## 怎样检查

为验证器准备三个用例：字段不存在、字段值类型不匹配、必填字段遗漏。观察它是否给出具体原因，以及这些错误是否在实际填表之前被发现。

还要准备一份有效计划，检查它能否通过验证并进入执行。这些是待实现工具的检查要求，本页没有将其写成已经完成的 PDF 测试。

与上一节的区别是检查时机：上一节根据工作结果发现问题并修正；这里先对准备执行的数据做检查。真实任务中可以同时保留执行后的验证。

若业务要求验证失败时绝不执行，应把这一判断接入调用程序；仅写在 Skill 中仍需要 Agent 遵循。

[上一节：验证循环]({{< relref "04-validation-loops.md" >}}) · [下一节：可复用脚本]({{< relref "06-scripts.md" >}})
