# Trial._scrub_jobs_dir（Harbor）

[本步 scope · 6a](../../../../../01-scope.md) · [返回 Trial.run](Trial.run.md) · [源码 :1233](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1233)

**当前问题：结果已经保存，最后怎样处理文件里可能出现的凭据？**

调用方：`Trial.run` 在 `_finalize` 之后的 finally 中执行 `self._scrub_jobs_dir()`；本函数不接收额外参数，使用 Trial 已有配置与路径，正常返回 None。

## ① 处理什么：文件留下，敏感值替换

它从 Agent、Verifier 的环境配置及明确指定的凭据中收集待替换值，再扫描 **self.paths.trial_dir，即当前 Trial 的目录**；不是删除整个 jobs 目录。文本内容经 scrub_file_text 处理，发生变化才写回。

静态示例，下面的值为虚构字符串：

```text
已识别的敏感值：demo-secret-abc
原文件：Authorization: Bearer demo-secret-abc
处理后：Authorization: Bearer [REDACTED]
```

文件和其他内容继续保留。没有收集到敏感值则直接返回；这是基于已收集值的替换，不保证自动识别文件中一切未知敏感信息。

<details>
<summary>按需看代码位置与跳过规则</summary>

源码：Trial._scrub_jobs_dir，trial.py:1233–1311。收集来源还包括已启用的 user agent、bridge 和 MCP 凭据；过滤类似布尔开关的值，避免把文本中的每个 1 都替换。

遍历普通文件，跳过符号链接；探测到二进制或无法按文本读取时跳过，不删除该文件。敏感值先按长度降序排列；JSON/JSONL 的纯数字敏感值限定在字符串中替换，避免破坏数字字段。辅助函数位于 utils/redaction.py:16，本轮不继续下钻。

</details>

## ② 核心动作：找敏感值 → 扫描文件 → 有变化才写回

教学裁剪：下面只保留扫描后的核心语句，敏感值收集、文件探测和异常分支已省略。

```python
ordered_secrets = sorted(secrets, key=len, reverse=True)
# 在 self.paths.trial_dir.rglob("*") 的循环内，筛选可处理文件之后：
text = path.read_text()
scrubbed = scrub_file_text(path, text, ordered_secrets)
if scrubbed != text:
    path.write_text(scrubbed)
```

敏感值按长度降序处理，避免先替换短片段而影响更长值的匹配。副作用是更新部分本地文本文件，不创建新的 TrialResult，也不删除结果目录。

## ③ 读完回哪里？

回到 Trial.run 第[6]段的内层 finally，继续 [Trial._close_logger_handler](Trial._close_logger_handler.md)。即使当前脱敏方法抛错，调用方也会尝试关闭日志处理器。


<details>
<summary>个人表述、未知与源码依据</summary>

- 首次单独建卡：2026-11-17，Step 016；前一轮已在 Trial.run 第[6]段讲解，本次移入独立卡，不表示新增掌握。
- 用户要求：“不应该单独再看一下这里的这个函数卡片吗 同时在这里的scope中写一下？”当前尚无对此方法内部机制的个人复述。
- 固定源码：Harbor v0.25.0，`fdba28fc411e47e8765420a1a063b4918fce3def`；仅静态核对，没有实际执行文件脱敏或日志关闭实验。
- 未展开：所有凭据识别规则、JSON/JSONL 处理细节；不把这套规则等同于对所有未知敏感内容的保证。
- [形成过程](../../../../../04-flow.md)。

</details>
