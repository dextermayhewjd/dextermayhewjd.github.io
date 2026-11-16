# BaseEnvironment.upload_file

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_file.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码定位：[src/harbor/environments/base.py:1124–1131](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1124)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独记录：Step 013，2026-11-13，用户确认本轮接口建卡范围。
- 最近认识更新：尚无针对本接口的个人复述；以下为 LLM 静态核对，建卡不代表已掌握。

[Trial._prepare：Agent 准备的位置](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) → 回查 Agent 配置上传的用法 → **upload_file 接口** · [scope 3B](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md#reading-sequence)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 准备等阶段需要把 Harbor 本地已生成的单个文件放入环境；当前用 BaseInstalledAgent._upload_config_text 的真实调用辨认方向。
2. **具体内容**：接收本地 source_path 和环境内 target_path，等待单个文件上传。这里是抽象声明，不包含传输协议或权限处理实现。
3. **建议构建的心智模型**：

   > 本地有文件内容，环境中需要这份文件；上传后，后续命令可使用环境路径。

4. **调用代码**：BaseInstalledAgent._upload_config_text:1094–1097 的真实节选；这里只借用一个消费场景，Agent 准备内部仍留到 Step 014。

   ```python
   with tempfile.TemporaryDirectory(prefix="harbor-agent-config-") as temp_dir:
       local_path = Path(temp_dir) / filename
       local_path.write_text(content)  # 配置文本先成为本地文件。
       await environment.upload_file(local_path, remote_path)  # 再送到环境路径。
   ```

## 本场景的输入与输出

这里回查“单个文件”的合同，不表示 _prepare 直接调用 upload_file；示例中的 content、filename、remote_path 由 Agent 配置准备提供。

### 接口与输入

下面为固定版本的完整抽象方法声明。实际调用选定后端对象的方法；不会先由这段声明转发到后端。

```python
@abstractmethod
async def upload_file(self, source_path: Path | str, target_path: str):
    """
    Adds a local file to the environment.

    Args:
        source_path: The path to the source local file.
        target_path: The path to which to copy the file.
    """
```

| 输入 | 当前调用现场与接口要求 |
| --- | --- |
| self / environment | 选定且已启动的环境对象 |
| source_path: Path 或 str | local_path；运行 Harbor 的机器上的文件路径 |
| target_path: str | remote_path；目标环境内的文件路径 |

### 输出与返回位置

副作用：目标环境路径获得文件内容。接口没有标注返回类型，上层仅 await，不接收文件内容或一个结果对象；未取得真实传输结果。

返回 _upload_config_text；其后按需处理文件归属和权限，再完成 Agent 配置准备。本轮不展开该 helper，也不把它列成新的必读卡。

## 我的直接表述（原话）

尚无针对本接口的职责或机制的直接复述。本轮已确认建立这些接口卡片；确认原话统一保存在 [Step 013 形成过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)，不将授权建卡记成个人技术结论。

## 尚不清楚

- 目标后端如何传二进制、处理目标父目录和权限，以及如何报告失败。
- 当前未运行文件传输，不能由接口声明判断目标适配已经支持。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 `/home/fredkeira/projects/harbor` 的 `git show v0.25.0:src/harbor/environments/base.py`，通过 AST 核对方法签名、文档和行号；未混用当前 main。
- [_upload_config_text 的本地生成与上传现场](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/base.py#L1085)：仅核对本页调用现场。
- 接口与调用代码均为静态源码材料；调用节选已标注所在分支，变量值未通过真实运行取得。没有选定或执行任何具体后端，也没有启动沙箱、安装 Agent 或操作集群。
- [Step 013 本次建卡与边界](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)。

</details>
