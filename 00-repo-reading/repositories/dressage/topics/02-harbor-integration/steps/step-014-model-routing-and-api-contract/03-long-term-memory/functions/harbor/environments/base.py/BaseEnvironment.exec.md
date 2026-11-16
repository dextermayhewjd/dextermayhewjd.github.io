# BaseEnvironment.exec

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.exec.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码定位：[src/harbor/environments/base.py:1359–1378](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1359)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`；ExecResult 定义位于同文件 108–111 行。
- 首次单独记录：Step 013，2026-11-13，用户确认本轮接口建卡范围。
- 最近认识更新：尚无针对本接口的个人复述；以下为 LLM 静态核对，建卡不代表已掌握。

[Trial._prepare：启动之后的健康检查](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-healthcheck-call) → [run_healthcheck](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.run_healthcheck.md#healthcheck-next) → **exec 的接口与 ExecResult** · [scope 3A](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md#reading-sequence)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：环境已启动，健康检查、Agent 准备/运行或 Verifier 需要在其中执行命令。本卡先沿已读 _prepare 的健康检查调用回查接口。
2. **具体内容**：接收 command、cwd、env、timeout_sec、user，异步取得 ExecResult；三个结果字段为 stdout、stderr、return_code。基类只声明接口，命令执行由实际环境对象实现。
3. **建议构建的心智模型**：

   > Harbor 把命令交给环境对象，等待一次执行结果；调用方再根据退出码和输出决定怎样继续。

4. **调用代码**：BaseEnvironment.run_healthcheck:1592–1596，真实代码节选；hc 已由该函数取得，当前仅保留成功返回分支，不展开重试。

   ```python
   result = await self.exec(hc.command, timeout_sec=int(hc.timeout_sec))
   if result.return_code == 0:
       return  # 健康检查通过，返回 _prepare；随后继续 skills 与 Agent 准备。
   ```

## 本场景的输入与输出

输入已有启动后的环境对象和健康检查配置；没有创建新环境，也没有切换具体后端。当前只对照接口，未调用命令。

### 接口与输入

下面为固定版本的完整抽象方法声明。实际调用选定后端对象的方法；不会先由这段声明转发到后端。

```python
@abstractmethod
async def exec(
    self,
    command: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout_sec: int | None = None,
    user: str | int | None = None,
) -> ExecResult:
    """
    Executes a command in the environment.

    Args:
        command: The command to execute.
        cwd: The working directory in which to execute the command.
        env: The environment  variables to set.
        timeout_sec: The timeout in seconds.
        user: Username or UID to run the command as. None falls back to
            ``self.default_user``; if that is also None the environment's
            container default (typically root) is used.
    """
```

| 输入 | 当前调用现场与接口要求 |
| --- | --- |
| self | 已启动的具体环境对象；这里从基类定义回查其共同要求 |
| command: str | hc.command，即健康检查命令；其他调用方可传安装、Agent 或验证命令 |
| cwd: str 或 None | 当前调用未传；接口允许指定环境内的工作目录 |
| env: dict[str, str] 或 None | 当前调用未传；接口允许给命令传环境变量 |
| timeout_sec: int 或 None | 当前传 int(hc.timeout_sec)，单位为秒 |
| user: str、int 或 None | 当前未显式传；None 先使用 self.default_user，再回落到容器默认用户 |

### 输出与返回位置

```python
class ExecResult(BaseModel):
    stdout: str | None = None
    stderr: str | None = None
    return_code: int
```

这是源码中的结果结构，并非一次运行所得的输出。调用方接住 `result`，健康检查直接读取 `return_code`；其他调用方也可读取两个输出字段。stdout/stderr 是命令的输出内容，是否再打印由调用方决定；它们本身不是模型 API 请求记录。

具体后端返回 ExecResult → run_healthcheck 检查退出码 → 检查通过后回到 _prepare，继续 _upload_injected_skills。Agent.setup 的另一处调用也使用同一接口，但本卡不展开安装流程。

## 我的直接表述（原话）

尚无针对本接口的职责或机制的直接复述。本轮已确认建立这些接口卡片；确认原话统一保存在 [Step 013 形成过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)，不将授权建卡记成个人技术结论。

## 尚不清楚

- 目标 Agent Sandbox 后端如何实现 cwd/env/user、超时以及输出收集。
- 非零退出码、执行异常与取消怎样映射到结果或异常，待实现/运行核对。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 `/home/fredkeira/projects/harbor` 的 `git show v0.25.0:src/harbor/environments/base.py`，通过 AST 核对方法签名、文档和行号；未混用当前 main。
- [健康检查与 exec 的实际消费](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1560)：仅核对本页调用现场。
- [Agent.setup 的命令执行调用，只核对使用位置](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/base.py#L1126)：仅核对本页调用现场。
- 接口与调用代码均为静态源码材料；调用节选已标注所在分支，变量值未通过真实运行取得。没有选定或执行任何具体后端，也没有启动沙箱、安装 Agent 或操作集群。
- [Step 013 本次建卡与边界](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)。

</details>
