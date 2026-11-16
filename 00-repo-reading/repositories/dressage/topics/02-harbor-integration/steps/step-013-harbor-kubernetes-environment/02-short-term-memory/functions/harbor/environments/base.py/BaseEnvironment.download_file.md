# BaseEnvironment.download_file

- 源码定位：[src/harbor/environments/base.py:1144–1151](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1144)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独记录：Step 013，2026-11-13，用户确认本轮接口建卡范围。
- 最近认识更新：尚无针对本接口的个人复述；以下为 LLM 静态核对，建卡不代表已掌握。

[scope 3B：文件传输合同](../../../../../01-scope.md#reading-sequence) → 用下载辅助流程定位消费 → **download_file 接口** · [对照 upload_file](BaseEnvironment.upload_file.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：需要把环境中的单个文件取回运行 Harbor 的机器。当前以基类下载辅助流程中的真实调用说明合同，不新增该辅助流程的深读范围。
2. **具体内容**：接收环境内 source_path 和本地 target_path，等待文件下载；基类只声明单文件传输接口。
3. **建议构建的心智模型**：

   > 环境里已经产生文件，Harbor 用本地目标路径接收它；得到的是落盘文件。

4. **调用代码**：BaseEnvironment.download_dir_filtered:1337–1341 的真实节选。其特定场景是取回已在环境中准备好的归档；本卡只看单文件传输，不展开打包/过滤算法。

   ```python
   host_tar_path = Path(host_tmp_dir) / env_tar_filename
   await self.download_file(
       source_path=env_tar_path,  # 环境里已生成的归档文件。
       target_path=host_tar_path, # 本地临时目录中的目标文件。
   )
   ```

## 本场景的输入与输出

这是接口回查示例，不是已读 _prepare 之后必然紧接着运行的语句。已有输入为环境归档路径与本地临时路径；无需在此展开它们的构造算法。

### 接口与输入

下面为固定版本的完整抽象方法声明。实际调用选定后端对象的方法；不会先由这段声明转发到后端。

```python
@abstractmethod
async def download_file(self, source_path: str, target_path: Path | str):
    """
    Downloads a file from the environment to the local machine.

    Args:
        source_path: The path to the source file in the environment.
        target_path: The local path to which to copy the file.
    """
```

| 输入 | 当前调用现场与接口要求 |
| --- | --- |
| self | 执行下载的具体环境对象 |
| source_path: str | env_tar_path；源文件在环境里 |
| target_path: Path 或 str | host_tar_path；目标文件在 Harbor 本地 |

### 输出与返回位置

副作用：源文件被下载到本地 target_path。接口没有标注返回类型；调用方 await 后从本地文件继续处理，不从返回值取得字节内容。未取得真实下载文件。

在本例返回 download_dir_filtered，后续读取并解包已落到本地的归档。这里用于辨认单文件合同，不表示 _prepare 会执行下载；后续具体 Agent/产物流程也可使用此接口。

## 我的直接表述（原话）

尚无针对本接口的职责或机制的直接复述。本轮已确认建立这些接口卡片；确认原话统一保存在 [Step 013 形成过程](../../../../../04-flow.md#environment-interface-cards-20261113)，不将授权建卡记成个人技术结论。

## 尚不清楚

- 目标后端如何处理缺失文件、覆盖、父目录和二进制内容。
- 当前没有运行下载或解包，辅助流程的内部算法暂缓。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 `/home/fredkeira/projects/harbor` 的 `git show v0.25.0:src/harbor/environments/base.py`，通过 AST 核对方法签名、文档和行号；未混用当前 main。
- [download_dir_filtered 对单文件接口的真实调用](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1337)：仅核对本页调用现场。
- 接口与调用代码均为静态源码材料；调用节选已标注所在分支，变量值未通过真实运行取得。没有选定或执行任何具体后端，也没有启动沙箱、安装 Agent 或操作集群。
- [Step 013 本次建卡与边界](../../../../../04-flow.md#environment-interface-cards-20261113)。

</details>
