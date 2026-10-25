# _session_id

- 源码定位：[examples/coding_agent_rl/generate.py:438–443](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L438-L443)，由助手核对。
- 首次接触：Step 4，此前在输入背景中定位；2026-10-22 本轮展开并独立记录。
- 最近认识更新：2026-10-24，用户概括根据 base_sample 与 instance_id 取得编号，并表示大概清楚；具体字段与各分支仍按源码说明保留。

- 本轮源码校准：2026-10-24，函数 AST 与旧版相同；更新调用位置和编号规则的行号，原话与认识时间保留。[旧版完整卡片](../../../../../references/session-id-at-2f231865.md)供回查。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页输入输出整理，作为理解参考。

1. **使用场合**：`_generate` 已从 `md` 取得题目编号 `instance_id`，在调用 `open_session` 登记配置前，需要为本次 Agent 执行取得一个 `session_id`。

2. **具体内容**：优先返回样本已有的非空编号；没有旧编号时，若两个样本索引都不是 `None`，用题目编号与索引拼接；否则用题目编号与随机串拼接。返回字符串，本函数不修改 Sample，也不登记 Session 配置。

3. **建议构建的心智模型**：

   > `_session_id` 为这次执行取一个编号：能沿用就沿用，否则按索引或随机串生成。
   >
   > 返回的只是编号字符串；`_generate` 保存这个编号，再把它交给 `open_session` 登记配置。

4. **调用代码**（`generate.py:269–279`，省略登记的其他参数）：

   ```python
   session_id = base_sample.session_id = _session_id(base_sample, instance_id)
   adapter.open_session(session_id, ...)
   ```

## 本场景的输入与输出

沿用 [base_sample 参考中的源码测试例子](../../../../../references/base-sample.md)：题目编号为 `demo-1`，两个索引均为 `0`，原先没有执行编号。下面只展示本函数实际读取的字段，Sample 中的其他内容仍然存在。

**输入**：函数中的 `sample` 对应调用方的 `base_sample`；`instance_id` 是另一个实参。

```text
sample → base_sample（Sample 对象）
    session_id = None
    index = 0
    group_index = 0

instance_id = "demo-1"
```

**输出**：返回一个字符串。

```python
"cagent-demo-1-0-0"
```

- 其中 `demo-1` 来自题目编号，后面两个 `0` 分别来自 `sample.index` 与 `sample.group_index`。
- 本函数返回时尚未修改 `sample.session_id`；外面的赋值语句随后才将返回值写回 `base_sample.session_id`，并保存为局部变量 `session_id`。
- `metadata` 和 `prompt` 不参与本函数的拼接。题目编号已经在调用前从 `md["instance_id"]` 取出，再作为单独参数传入。

### 实际规则：依次选择一种返回方式（438–443）

```python
def _session_id(sample: Sample, instance_id: str) -> str:
    if sample.session_id:  # 优先沿用已有编号
        return sample.session_id
    if sample.index is not None and sample.group_index is not None:  # 两个索引都有值，0 也可用
        return f"cagent-{instance_id}-{sample.index}-{sample.group_index}"
    return f"cagent-{instance_id}-{secrets.token_hex(8)}"  # 缺少索引时补随机后缀
```

1. **已有非空编号**：直接返回，例如 `"saved-id"`；不再把它与题目编号或索引拼起来。
2. **没有旧编号，且两个索引齐全**：返回 `cagent-{instance_id}-{index}-{group_index}`，本例就是 `"cagent-demo-1-0-0"`。判断的是是否为 `None`，所以索引 `0` 可以使用。
3. **没有旧编号，且至少一个索引缺失**：返回题目编号加随机串，例如 `cagent-demo-1-<16位十六进制随机串>`。这里是形状示意；`secrets.token_hex(8)` 的具体结果不固定。

相同题目编号与索引会拼出相同字符串，本函数不检查 Adapter 中是否已登记该编号。返回后接到 [BaseAdapter.open_session](../../../slime/agent/adapters/common.py/BaseAdapter.open_session.md)，由那里处理配置登记和重复编号。

## 我的直接表述（原话）

> 好的那么我目前大概理解的是
> 这里的session id就是组合base sample 这里关于metadata 题目相关的原始信息
> 还有这里的prompt输入的问题内容
> index 样本索引group index是分组
> 还有已经有的sessionid
> 然后在这里通过session_id就创建一个这里的session_id
> 如果是创建的那么需要看一下这里的session_id的内容
> 也就是包含了instance id sample index还有这里的group index？
>
> 我可以简单这么理解吧
> 那么这里的内容是否适合放在session_id 这个函数记忆里面呢？

2026-10-24，用户回顾后表示：

> 简单来说就是根据base sample和instanceid 来给编号的对吗
> 好的 我大概清楚了
> 那么继续吧
> 下一步需要看什么呢?

这次已将两个输入与编号生成联系起来，随后进入会话登记；不据此补写逐项字段的理解。

## 尚不清楚

- 用户是否已区分“Sample 含有的全部字段”和“本函数实际读取的三个属性与一个独立参数”，仍待后续反馈。
- 旧编号优先、索引缺失时使用随机串，以及返回与调用方保存的区别，本轮已补充说明，尚未确认理解。
- 上游怎样分配样本索引与已有编号，继续保留为后续问题；本函数只消费这些值。

<details>
<summary>来源、验证与完整例子</summary>

- 当前固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。调用前取题目编号、保存返回值与登记配置见 [generate.py:260–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L260-L279)。以下测试样例与运行证据保留原 `2f231865` 版本归属，本轮只静态核对函数未变。
- 主例沿用 [CPU 测试的 Sample 构造](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L96-L105)；`session_id` 默认值见 [types.py:167](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/types.py#L167)。
- 2026-10-22 局部验证：用 AST 原样提取 `_session_id`，以带所需字段的 `SimpleNamespace` 替代完整 Sample。核对已有编号、索引为零、空旧编号、任一或全部索引缺失六种输入；检查返回值与随机串格式，并确认输入对象未修改。静态核对本函数只读取 `sample.session_id`、`sample.index`、`sample.group_index`。
- 没有运行完整 generate、初始化 Adapter、登记会话或启动模型与沙箱；局部验证不表示用户已理解全部规则。
- 形成过程：[Step 4 · 编号规则与实际使用的字段](../../../../../04-flow.md#session-id-function-memory)。概念背景继续查 [Sample](../../../../../references/base-sample.md) 和[题目编号](../../../../../references/instance-id.md)。

</details>
