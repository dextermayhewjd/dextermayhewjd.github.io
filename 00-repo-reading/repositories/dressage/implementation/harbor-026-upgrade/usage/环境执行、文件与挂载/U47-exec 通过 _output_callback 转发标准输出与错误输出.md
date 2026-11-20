# U47 · exec 通过 _output_callback 转发标准输出与错误输出

<a id="u47"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 525–530](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L525-L530)

```python
callback = self._output_callback()
if callback is not None:
    if stdout_text:
        await callback(stdout_text, "stdout")
    if stderr_text:
        await callback(stderr_text, "stderr")
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage environment.py 523–530](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L523-L530) | 在有订阅的 Trial 里让命令各写一行 stdout 和 stderr，记录实际送入回调的文本和流名。 |
| ② 结果　[Harbor trial.py 580–595](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L580-L595) | 看 Trial 的输出钩子收到两条对应记录。再用无订阅场景核对 exec 仍返回自己的输出。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L477-L486) | 无参数，读取当前 Harbor 作用域登记的输出回调 | 源码可接收 | 无订阅时返回 None，有订阅时返回可等待的回调。Dressage 用 `(text, "stdout"/"stderr")` 调用 | 源码吻合，独立输入待实测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L676-L685) | 无参数，读取当前 Harbor 作用域登记的输出回调 | 源码可接收 | 无订阅时返回 None，有订阅时返回可等待的回调。Dressage 用 `(text, "stdout"/"stderr")` 调用 | 源码吻合，独立输入待实测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L741-L750) | 无参数，读取当前 Harbor 作用域登记的输出回调 | 源码可接收 | 无订阅时返回 None，有订阅时返回可等待的回调。Dressage 用 `(text, "stdout"/"stderr")` 调用 | 源码吻合，独立输入待实测 |

**接续**　需要支持订阅输出时，分别观察两种流收到的文本与标签。 [environment.py 526-531](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L526-L531) · [问题 08](../../investigations/08-trial-output-redaction/README.md)
