# BaseEnvironment.start

- 源码：[src/harbor/environments/base.py · BaseEnvironment.start](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 013，2026-11-13。
- 最近认识更新：2026-11-13，用户已判断这里仅为接口、没有其他实现，询问是否还需单独阅读；具体 K8s 实现仍待定位。

[上层调用 Trial._start_agent_environment](../../trial/trial.py/Trial._start_agent_environment.md) → **当前核对 start 的接口约定** · [其余接口从 exec 继续](BaseEnvironment.exec.md) · [scope](../../../../../01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：框架调用选定环境对象的 start，需要各后端提供共同的启动接口。
2. **具体内容**：以抽象方法声明异步 start，接收 force_build，约定启动环境并可强制构建，正常返回类型为 None；这里没有具体后端操作。
3. **建议构建的心智模型**：

   > 这是各后端要实现的启动接口说明；具体 K8s 后端负责把它落实为自己的资源操作。

4. **调用代码**（上层节选）：

   ```python
   await asyncio.wait_for(
       self.agent_environment.start(
           force_build=self.config.environment.force_build
       ),
       timeout=self._environment_build_timeout_sec,
   )
   ```

## 本场景的输入与输出

### 为什么从调用处回查这个定义？

前面已读到 self.agent_environment.start(...)。当前查看 BaseEnvironment，是为了确定目标 K8s 适配需要提供什么接口。实际执行时调用具体对象实现的 start；并非先运行这个抽象方法，再由它调用 K8s。

### 完整接口声明

下面是当前方法的全部源码，只增加两行中文注释：

```python
@abstractmethod                         # 由具体后端实现这个接口。
async def start(self, force_build: bool) -> None:
    """Starts the environment and optionally forces a build."""
    # 接收是否强制构建的标志；启动逻辑由后端提供。
```

| 内容 | 这里明确了什么 |
| --- | --- |
| self | 要启动的那个后端环境对象 |
| force_build: bool | 调用方传入是否强制构建的标志；具体如何落实取决于后端能力与实现 |
| async def | 调用方可以异步等待启动方法完成 |
| -> None | 接口约定正常完成时不返回另一份环境对象 |

这里没有写创建 Pod、等待 Ready、使用哪张镜像或如何处理 Claim 的代码，也没有定义这些条件具体如何判断。不能从这几行直接断言某个 K8s 适配已经具备这些能力。

### 返回后由谁继续？

具体后端的 start 正常结束后，返回 Trial._start_agent_environment，再回到上层计时包装；随后 _prepare 继续健康检查与 Agent 准备。若抛出异常，则沿已有异常路径传播。当前只核对接口，尚未进入或运行具体后端。

## 我的直接表述（原话）

用户确认本轮入口：

> 好的 那么现在看一下这里的这个start函数吧

用户随后判断：

> 好的 那么请和我一起看一下这里的这个baseEnvironment的start应该是怎么写的吧
> 简单来看 这里就只是一个接口
> 没有别的内容
> 还有什么需要我单独看的吗？

这与当前源码一致：此处只声明接口，不包含具体启动行为。基类方法到此可结束首轮阅读；实现代码应在目标后端子类中核对，不继续追读 BaseEnvironment 全部工具方法。当时建议下一处定位实际 K8s 适配类；2026-11-13 用户随后明确暂缓具体后端，当前先从 [exec 与 ExecResult](BaseEnvironment.exec.md) 补齐运行接口。


## 尚不清楚

- 2026-11-13 本地复核：Harbor 0.25 未找到该目标的内置实现；Agent Sandbox 示例引用 AgentSandboxEnvironment，但安装目录在当前 checkout 缺失。具体适配仍待复用或补齐，不能按示例名直接开始读不存在的实现。
- 该实现怎样准备镜像、创建或取得沙箱，怎样决定 start 可以返回。
- force_build 在目标后端怎样支持或明确拒绝，以及失败后的资源清理。

<details>
<summary>来源与验证边界</summary>

- [官方 BaseEnvironment.start](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py)：本轮仅核对抽象方法声明；未将通用工具方法或其他后端实现列为已读。
- [上层调用](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)由前面函数卡承接。是否有目标适配实现，仍按项目代码和配置另行核对，不能用旧示例名称代替实现证据。
- [Step 013 本次记录](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#base-environment-start-entry-20261113)。没有调用抽象方法或真实后端、创建 Pod 或运行集群验证。

</details>
