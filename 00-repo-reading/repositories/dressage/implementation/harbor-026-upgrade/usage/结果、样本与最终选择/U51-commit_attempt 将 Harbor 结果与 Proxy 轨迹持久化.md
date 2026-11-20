# U51 · commit_attempt 将 Harbor 结果与 Proxy 轨迹持久化

<a id="u51"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[artifacts.py 484](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L484)

```python
await asyncio.to_thread(self._write_model_atomic, output_path, bundle)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 769–782](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L769-L782) | 在 END 提交时记下本次物理 ID、传入的 TrialResult、Trial 目录和 Proxy 会话。 |
| ② 结果　[Dressage artifacts.py 480–493](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L480-L493) · [Dressage plugin.py 797–800](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L797-L800) | 在 disk 模式回读同一 ID 的 bundle，核对返回对象、磁盘内容和插件索引中的 reward 与失败状态。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/hooks.py#L44) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L69-L129) | TrialResult、同一 attempt 身份、trial_dir 加上 Proxy 的片段。Store 目标位于 Trial 外 | 用真实 TrialResult 及受控输入实测 | 返回及写入 HarborTrajectoryBundle，可按物理 id 找回 reward、failures、trainable | 磁盘回读的 trial_id 与奖励映射实测吻合 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/hooks.py#L44) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L75-L169) | TrialResult、同一 attempt 身份、trial_dir 加上 Proxy 的片段。Store 目标位于 Trial 外 | 用真实 TrialResult 及受控输入实测 | 返回及写入 HarborTrajectoryBundle，可按物理 id 找回 reward、failures、trainable | 同输入实测磁盘回读与 0.18 一致 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/hooks.py#L44) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L91-L189) | TrialResult、同一 attempt 身份、trial_dir 加上 Proxy 的片段。Store 目标位于 Trial 外 | 用真实 TrialResult 及受控输入实测 | 返回及写入 HarborTrajectoryBundle，可按物理 id 找回 reward、failures、trainable | 同输入磁盘回读与 0.18 吻合 |

**接续**　三版 Job 的正常 END 均调用一次真实 Store，使用固定 Proxy 输入并从磁盘读回；真实 Agent、verifier 和 Proxy 仍需联测。 [artifacts.py 473-486](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L473-L486) · [plugin.py 778](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L778) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 08](../../investigations/08-trial-output-redaction/README.md) · [问题 12](../../investigations/12-reward-validity/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)

[三版 Job 的磁盘读回](../../investigations/22-retry-policy/job-trial-output.txt)
