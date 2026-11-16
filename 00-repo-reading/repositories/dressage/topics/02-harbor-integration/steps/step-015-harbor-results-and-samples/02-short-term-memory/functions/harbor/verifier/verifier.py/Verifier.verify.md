# Verifier.verify

- 代码归属：**Harbor**；本卡不是 Dressage Proxy 或 reward model 的实现。
- 源码：[verifier.py:198](/home/hongshi/projects/harbor/src/harbor/verifier/verifier.py:198)，v0.25.0，提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独阅读：2026-11-16，Step 015。用户确认继续看实际评测，尚无本函数的个人复述。
- 本轮范围：普通单步任务、Linux、SHARED、需要上传测试目录的路径；不展开多步骤、Windows 和全部失败包装。
- 验证方式：静态核对实现与仓库自带任务示例，没有执行测试、容器或模型。

[本步 scope](../../../../../01-scope.md) · [返回评测安排卡](../../trial/single_step.py/SingleStepTrial._run_verifier.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：上层已选好环境、构造 Verifier，现在需要执行题目的评测并返回评分。
2. **具体内容**：找到并部署测试脚本，清掉旧奖励，执行测试，取得评测输出目录，解析奖励文件，返回 VerifierResult。
3. **建议构建的心智模型**：

   > 题目的测试脚本负责检查成果、写出奖励；Verifier.verify 负责运行它并读回奖励。不是从 Agent 的最终回复或测试日志里猜分数。

4. **调用位置**（调用关系示意，不是同一函数体）：

   ```text
   SingleStepTrial._run_verifier
     → Trial._run_shared_verifier       创建具体 Verifier，使用原 Agent 环境
       → Trial._verify_with_timeout     包裹超时
         → Verifier.verify              当前：真正执行测试并读分数
       ← VerifierResult
     → self.result.verifier_result      上层写回本次尝试
   ```

## 本场景的输入与输出

### 1. 带着什么来到这里

self 已持有 task、environment、trial_paths 和评测环境变量等配置。SHARED 路径下，Agent 产生的文件还在原环境中，不需要把本地产物重新复制回去才能评测。

本卡改用仓库自带的最小任务 `examples/tasks/hello-world-multiple-solutions`。它比前面的 calc.py 教学例子更便于直接对照真实脚本，不表示两个例子是同一次运行。

| 已有输入 | 本例用途 |
| --- | --- |
| 题目的 `tests/test.sh` | 规定如何检查 `hello.txt` 并写奖励 |
| 环境中的 `/logs/artifacts/hello.txt` | Agent 应产生的成果，测试脚本读取它 |
| `self.trial_paths.verifier_dir` | 本地 `<trial_dir>/verifier/`，保存评测日志和奖励文件 |

输出是 **VerifierResult 对象**，例如 `VerifierResult(rewards={"reward": 1.0})`；同时留下评测文件。与上层 `_run_verifier` 返回 None 不同，这个函数确实返回评分对象。

### 2. 准备：找测试、清旧奖励、上传测试目录

下面是原实现的主干节选；省略文件筛选、异常包装和平台路径细节。upload_dir 位于原实现对筛选目录的循环中，不能把片段当作完整可运行函数。

```python
test_source_dirs, tests_source_dir, host_test_path = self._resolve_tests()
await self._remove_reward_files()

# 普通路径中，将筛选后的测试目录上传至环境；原码在循环内：
await self.environment.upload_dir(
    source_dir=source_dir,
    target_dir=str(env_paths.tests_dir),
)
```

本例本地的 `tests/test.sh` 会放到环境的 `/tests/test.sh`。清旧奖励是为了避免本次没有生成评分，却读到上次留下的 reward。若使用已包含测试的评测镜像，上传会跳过；本轮不展开该分支。

### 3. 执行：评分规则在题目的脚本里

主干节选：原码还会合并环境变量、计算输出路径，并在需要时 chmod。

```python
command = build_execution_command(
    test_script_path,
    stdout_path=test_stdout_path,
    task_os=self.environment.os,
)
await self.environment.exec(
    command=command,
    env=env,
)
```

**真正的评分规则**来自下列完整官方仓库示例 [tests/test.sh](/home/hongshi/projects/harbor/examples/tasks/hello-world-multiple-solutions/tests/test.sh:1)：

```bash
#!/bin/bash

if [ "$(cat /logs/artifacts/hello.txt 2>/dev/null)" = "Hello, world!" ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

这里脚本检查文件内容，并自己决定写 1 还是 0。Verifier 不负责理解“Hello, world!”为什么算正确。换一道题可以使用不同检查命令，最终仍按约定输出奖励。

```text
Agent 留下 hello.txt
        ↓ 测试脚本读取
内容符合预期 → reward.txt 写 1
内容不符/缺失 → reward.txt 写 0
```

“得到 0 分”和“没生成奖励文件”不是同一种结果。脚本打印成功、命令执行结束，也不等于已提供符合约定的评分。

### 4. 取回并解析：奖励文件变成返回对象

非挂载且未配置日志筛选的普通路径节选：

```python
await self.environment.download_dir(
    source_dir=str(env_paths.verifier_dir),
    target_dir=self.trial_paths.verifier_dir,
)
```

如果该目录已经挂载，直接访问共享文件；配置了日志筛选时走 filtered 下载，并保护奖励文件不被过滤掉。

原实现的奖励选择与返回（异常文本省略）：

```python
if self.trial_paths.reward_json_path.exists():
    rewards = self._parse_reward_json()
elif self.trial_paths.reward_text_path.exists():
    rewards = self._parse_reward_text()
else:
    raise RewardFileNotFoundError(...)

return VerifierResult(rewards=rewards)
```

| 文件形式 | 文件内容示例 | 解析结果 |
| --- | --- | --- |
| `reward.txt` | `1` | `{"reward": 1.0}` |
| `reward.json` | `{"correctness": 1, "quality": 0.8}` | 对应名称到数值的字典 |

上表 JSON 是字段形式的教学示例，不是该 hello-world 脚本写出的文件。两种文件同时存在时优先读取 JSON；缺少奖励文件报错，空文件或非法奖励也不能当作正常评分。

### 5. 同一次成功评测的数据流

按上述官方脚本静态推演，假设 hello.txt 内容正确；这不是实测记录：

```text
环境 /logs/artifacts/hello.txt
  Hello, world!
        ↓ /tests/test.sh 执行检查
环境 /logs/verifier/reward.txt
  1
        ↓ 下载或挂载访问
本地 <trial_dir>/verifier/reward.txt
  1
        ↓ _parse_reward_text()
{"reward": 1.0}
        ↓ Verifier.verify 返回
VerifierResult(rewards={"reward": 1.0})
        ↓ 沿调用链回到 SingleStepTrial._run_verifier
self.result.verifier_result = 这个返回对象
```

读取到这里即可回上层：评分对象已经有来源。测试目录筛选、平台命令、超时和具体环境传输本轮保持接口级理解，不逐个建立辅助函数卡。

## 我的直接表述（原话）

用户确认进入实际评测函数：

> 好的那么单独看一下这个部分吧

本轮初步理解（原话）：

> 简单来说就是这里的这个verifier在上传了这个test之后需要看一下这里的这个reward到底是能够拿多少分是我的理解

助手校准：上传后先执行测试脚本，由脚本检查 Agent 的成果并写出奖励文件；Verifier 再读取、解析并封装分数。这里不是上传后直接检查一个已有分数，也不是 Verifier 自行决定题目评分规则。用户对这一顺序校准的理解尚待反馈。

## 尚不清楚

- 其他真实题目的测试与评分规则，可按任务需要再读，不从最小示例推断所有题目都只给 0/1。
- 多步骤任务的测试选择、Windows 命令、日志过滤与错误归档，本轮未展开。
- 真实环境中跑完整任务与奖励读取尚未验证。

<details>
<summary>源码与样例依据</summary>

- [Verifier.verify](/home/hongshi/projects/harbor/src/harbor/verifier/verifier.py:198)：上传测试、执行命令、取得评测目录、奖励优先级与返回。
- [文本解析](/home/hongshi/projects/harbor/src/harbor/verifier/verifier.py:70)、[JSON 解析](/home/hongshi/projects/harbor/src/harbor/verifier/verifier.py:91)：数值与有限值检查。
- [环境路径](/home/hongshi/projects/harbor/src/harbor/models/trial/paths.py:44)、[本地评测路径](/home/hongshi/projects/harbor/src/harbor/models/trial/paths.py:250)。
- [官方仓库示例脚本](/home/hongshi/projects/harbor/examples/tasks/hello-world-multiple-solutions/tests/test.sh:1)：本文原样展示，没有实际执行。
- [本步形成过程](../../../../../04-flow.md)。

</details>
