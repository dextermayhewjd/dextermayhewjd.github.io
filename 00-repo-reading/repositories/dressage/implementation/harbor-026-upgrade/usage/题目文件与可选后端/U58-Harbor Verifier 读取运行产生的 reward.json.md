# U58 · Harbor Verifier 读取运行产生的 reward.json

<a id="u58"></a>

[题目文件与可选后端目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[prepare_dataset.py 60–64](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L60-L64)

```text
python3 /tests/verify.py \\
  --stream /logs/agent/claude-code.txt \\
  --expected /tests/expected.json \\
  --reward /logs/verifier/reward.json \\
  --details /logs/verifier/details.json
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage prepare_dataset.py 126–132](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L126-L132) | 在生成的 `tests/verify.py` 写 `reward.json` 的行比较正确与错误答案。实现原文对应此处的脚本模板。 |
| ② 结果　[Harbor verifier.py 299–310](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L299-L310) | 从 Harbor 查看实际读到的 rewards 与返回的 `VerifierResult.rewards`，分别核对文件中的 1 和 0。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/verifier/verifier.py#L81-L94) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/verifier/result.py#L5) | 题目生成的 `verify.py` 接收预期答案和一份 Claude 结果流，向 `TrialPaths.reward_json_path` 写 JSON 映射 | 在临时目录用正确答案 `4`、错误答案 `5` 各运行一次，Harbor 的实际解析方法均接受 | 磁盘 `reward.json` → `VerifierResult.rewards` | 实测正确得到 `{'reward': 1}`，错误得到 `{'reward': 0}`。两次值与对应文件相同 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/verifier/verifier.py#L91-L124) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/verifier/result.py#L5) | 题目生成的 `verify.py` 接收预期答案和一份 Claude 结果流，向 `TrialPaths.reward_json_path` 写 JSON 映射 | 在临时目录用正确答案 `4`、错误答案 `5` 各运行一次，Harbor 的实际解析方法均接受 | 磁盘 `reward.json` → `VerifierResult.rewards` | 实测正确得到 `{'reward': 1}`，错误得到 `{'reward': 0}`。两次值与对应文件相同 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L91-L124) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/verifier/result.py#L5) | 题目生成的 `verify.py` 接收预期答案和一份 Claude 结果流，向 `TrialPaths.reward_json_path` 写 JSON 映射 | 在临时目录用正确答案 `4`、错误答案 `5` 各运行一次，Harbor 的实际解析方法均接受 | 磁盘 `reward.json` → `VerifierResult.rewards` | 实测正确得到 `{'reward': 1}`，错误得到 `{'reward': 0}`。两次值与对应文件相同 |

**独立 verifier 实测**　另一组从 `Trial._run_separate_verifier()` 进入，实际执行 bwrap 和 DAPO 的 `test.sh`。0.25、0.26 默认配置都在正确奖励写出后抛 `DownloadVerifierDirError`，只启用自动挂载，两版均返回 1。0.18 默认返回 1。[问题 02 的完整 Verifier 回放](../../investigations/02-output-mounts/README.md#verifier-reward)

**接续**　表中两组输入检验文件解析；沙箱内的评分与日志交付见上方独立 verifier 实测。 [prepare_dataset.py 342-347](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L342-L347) · [三版 DAPO 文件交接原始输出](../evidence/dapo-files.txt) · [文件探测与断言](../evidence/dapo_files.py) · [问题 12](../../investigations/12-reward-validity/README.md) · [问题 18](../../investigations/18-example-configs/README.md)
