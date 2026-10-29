# test_custom_generate_function_path_supports_user_override

- 源码定位：[tests/plugin_contracts/test_plugin_generate_contracts.py:148](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)，核对版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- 首次接触：Step 015 前期作为第三步候选定位；2026-10-28 用户明确要求阅读本文件，本轮开始展开这个测试。
- 最近认识更新：2026-10-28，用户已初步区分生成函数的签名检查与返回 Sample 的字段检查，并询问通过 contract 是否就算合格样本；当前正在校准“通过本测试”和“满足完整下游要求”的边界，不计为已运行或全部掌握。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：检查一个通过函数路径接入的自定义 generate，能否被框架调用并交回具备基本字段的单个 Sample。本轮使用文件自带的默认测试实现。

2. **具体内容**：取得生成函数路径，检查此测试要求的参数名称，再经真实 generate_and_rm 执行，最后断言返回对象及几项字段。运行状态由 fixture 换成轻量替身，生成结果由小函数写死。

3. **建议构建的心智模型**：

   > 准备一个结果可预期的生成函数，让框架通过配置找到并调用它，再检查交回的数据。测试执行的是接入链路；固定 token、文本和分数用于观察这条链路。

4. **调用代码**：以下为测试体的调用骨架，省略参数；完整实参见下方源码。

   ```python
   result = asyncio.run(generate_and_rm(...))
   assert_sample_contract(result)
   ```

## 本场景的输入与输出

**场景前提**：没有设置 `SLIME_CONTRACT_CUSTOM_GENERATE_FUNCTION_PATH`，因此选择自带的 `REFERENCE_CUSTOM_GENERATE_PATH`；`group_rm=False`、`evaluation=False`，没有额外结果改写 hook。pytest 在执行测试体前，通过 `patch_generate_state` 将模块里的 GenerateState 替换为 FakeGenerateState。

**输入**：路径指向 `plugin_contracts.test_plugin_generate_contracts.custom_generate`；框架接收 `Sample(index=0, prompt="prompt")`、由 make_args 构造的最小配置及 `sampling_params={"temperature": 0.3}`。fixture 是测试准备入口，不是传给生成函数的业务参数。

**输出**：测试函数自身成功时隐式返回 None；要观察的是中间变量 result，它在当前默认路径中接住单个 Sample。以下是根据源码得到的预期，不是本轮真实运行输出。

| 字段 | 输入 Sample | 预期 result |
| --- | --- | --- |
| index / prompt | 0 / "prompt" | 0 / "prompt" |
| tokens | [] | [11, 12, 13] |
| response | "" | "generated" |
| response_length | 0 | 3 |
| reward | None | 0.25 |
| status | PENDING | COMPLETED |

返回值中的字段先看 [Sample 类卡](../../../../classes/slime/utils/types.py/Sample.md#step015-field-view)。本轮没有启动真实 Agent、模型或训练。

<a id="minimal-generate"></a>

### ① 用一个最小生成函数准备可预期结果（74–80）

```python
async def custom_generate(args, sample: Sample, sampling_params: dict):
    sample.tokens = [11, 12, 13]
    sample.response = "generated"
    sample.response_length = len(sample.tokens)
    sample.reward = 0.25
    sample.status = Sample.Status.COMPLETED
    return sample
```

- 它接住三个位置参数，原地填充传入的 Sample，并返回同一个对象。args 和 sampling_params 在这个替身中没有实际用于生成。
- 数值和文本是写死的测试数据，目的是让调用结果可预期。这里没有 tokenizer 或模型调用，不能据此推断这三个 token 会解码为 "generated"，也不能把 `response_length = len(tokens)` 推广为所有真实训练样本的规则。
- 它没有声明 evaluation，框架实际调用它时只传三个位置参数。它已经提供 reward，因此在这条单 Sample 路径中不会触发缺失奖励的补分。

### ② 经由框架执行这个函数（148–162）

下面是本轮选读测试的真实函数体：

```python
def test_custom_generate_function_path_supports_user_override(patch_generate_state):
    custom_generate_path = get_contract_path(
        "CUSTOM_GENERATE_FUNCTION_PATH",
        REFERENCE_CUSTOM_GENERATE_PATH,
    )
    assert_custom_generate_signature_matches_expected(load_function(custom_generate_path))
    result = asyncio.run(
        generate_and_rm(
            make_args(custom_generate_function_path=custom_generate_path),
            Sample(index=0, prompt="prompt"),
            sampling_params={"temperature": 0.3},
            evaluation=False,
        )
    )
    assert_sample_contract(result)
```

按测试体的执行顺序看三处交接：

1. **路径与签名**：get_contract_path 读取对应环境变量，没有配置时使用默认路径；load_function 取出函数对象。随后的断言要求前三个形参名称正好是 args、sample、sampling_params。
2. **执行与接收**：asyncio.run 执行 generate_and_rm 返回的协程；框架选择配置里的生成函数、等待它完成，并接着处理结果。最终返回值进入 result。这样一条测试包含了框架调用生成实现的过程。
3. **检查结果**：assert_sample_contract 检查 result，而不是再次执行生成。断言不成立会让测试失败。

```text
测试函数
  ├─ 取得路径 → load_function → 检查签名
  ├─ asyncio.run(generate_and_rm(...))
  │    └─ 框架调用 custom_generate → 接回 Sample → 返回
  └─ assert_sample_contract(result)
```

回到框架内部时，复用 [generate_and_rm 的调用约定](../../../slime/rollout/sglang_rollout.py/generate_and_rm.md#step015-call-contract)。FakeGenerateState、make_args、install_stubs 先作为测试准备：提供轻量状态、最小参数和部分依赖替身；本轮不展开其完整实现。

### ③ 断言究竟覆盖什么（93–103）

返回值断言的真实代码：

```python
def assert_sample_contract(sample: Sample) -> None:
    assert isinstance(sample, Sample)
    assert isinstance(sample.tokens, list)
    assert isinstance(sample.response, str)
    assert isinstance(sample.response_length, int)
    assert sample.reward is not None
```

它检查“单个 Sample、token 列表、响应文本、整数长度、奖励存在”。它没有断言 status、具体 token/分数、token 元素类型或长度对齐，也没有验证实际模型生成和训练是否正确。上方数据表的具体值是由默认生成替身赋值推导出来的，不是这些断言逐项验证的结果。

**“合格”在这里应限定为通过当前辅助函数的基本检查。** 例如其他检查项均满足时，即便 tokens 是空列表、response_length 是 100，这个辅助函数也没有长度关系断言去拒绝它。因此满足这五项不能保证数据内容合理或可以直接用于训练。通过整个测试还需要签名断言通过，并且中间的 generate_and_rm 调用正常结束。

末尾检查的对象是框架处理后的 result，不是直接检查生成函数内部的某个局部变量；其中 reward 也可能已经由框架按当前路径补齐。这里要求的是最终结果的 reward 非 None，不能推导为所有生成插件必须亲自评分。

签名断言比较的是前三个形参的名称和顺序，未单独检查参数总数、参数种类或是否以 async def 声明；中间的真实调用会进一步暴露调用或等待错误。实际框架按位置传这三个参数。已读 Coding Agent 使用 base_sample 且返回列表，不能直接用这个测试的名称和单对象断言去定义所有合法接入形式。需要时应让测试场景和断言匹配实际实现。

本轮先读这一个正常路径测试。同文件中默认生成、每样本路径优先、group_rm 列表返回的测试只作后续定位；一个错误／失败情形的实际验证仍未完成。

## 我的直接表述（原话）

本轮对两类检查的理解与追问：

> 而且这里是否应该只是检查了 assert custom generate signature matches expected？
> 也就是这里的sample 具体是需要满足什么内容？
> 这里也就只是说来而这个custom 的generate 只是要求满足这个是否满足这里的三个参数标准
> 最后的这个assert sample contract 的内容容更多的是这里的sample 还有tokens 以及response 还有这里的response length
> 只要满足这里的 contract 那么就是合格的sample 可以这么理解吗？
> 这里就是对于sample的要求

已初步区分函数签名检查和结果字段检查。助手补充中间还有一次实际框架调用、末尾还检查 reward 非 None，并将“合格”限定为满足本测试列出的条件；这些边界仍待用户反馈。[本轮校准](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#contract-check-boundary)保留完整语境。

用户确认本轮阅读入口：

> 好的 那么我们来看一下这里的test plugin generate contract吧 重点看一下这里的内容吧

这段较早的表述表示确认展开测试文件，不等于当时已理解测试机制；[开始带读的过程](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#plugin-contract-test-entry)保存展开范围与证据边界，后续理解见上方本轮原话。

## 尚不清楚

- 已初步区分签名与结果检查；路径加载、中间实际执行，以及通过局部断言和满足完整使用要求的区别仍待进一步反馈。
- fixture 的替换过程与测试失败时怎样定位问题，本轮仅说明用途。
- 怎样为实际 Coding Agent 的签名和列表返回选择匹配的断言，以及一个错误／失败情形，仍待后续验证。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本轮只读核对，Slime 工作区无改动。
- [默认生成替身 74](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:74)、[结果断言 93](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:93)、[签名断言 101](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:101)、[选读测试 148](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)。
- [路径配置读取 _shared.py:46](/home/hongshi/projects/slime/tests/plugin_contracts/_shared.py:46)；[状态替换 fixture 107](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:107)。
- 本轮进行了静态源码与默认 Python 依赖探测；该解释器可找到 pytest，但未找到 torch、numpy、ray、transformers。没有安装依赖、执行原 pytest 用例或启动真实生成；上方字段表为源码推导，不是测试运行证据。
- [本步 scope](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/01-scope.md#reading-order)保留整体位置；[源码证据](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/references/source-evidence.json)保存片段校验。

</details>
