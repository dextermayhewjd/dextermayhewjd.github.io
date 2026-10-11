# Exec Commands：源码与材料校验

已确认仓库 `/home/fredkeira/projects/slime`；固定提交 `22a89f96835969a47055a659c588f46151f8b07a`。

本稿为候选，未替换正式章节。静态核对源码，另用记录型依赖执行原函数；SDK、远端命令、CLI和模型均未运行。
旧图文与本章相关核心源码一致；本轮新图只描述当前执行机制。运行记录见 `示例.json`，复现脚本为 `verify_example.py`。

## C01

**核对事实：** generate 的 run await 经 Harness 与 launch_and_wait 下钻到 run_agent；缩进骨架仅作阅读导航，run_agent委派执行并向上返回整数状态。

- 外层任务调用：[examples/coding_agent_rl/generate.py:205](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L205-L213)
- Harness 中间交接：[slime/agent/harness/common.py:97](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L97-L104)
- 启动调用：[slime/agent/harness/claude_code.py:57](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L57-L71)
- 本章调用者：[slime/agent/harness/common.py:107](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L107-L122)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## C02

**核对事实：** 函数生成局部路径及脚本内容，调用write_file后CLI尚未启动。输出路径允许由调用方提供。

- 参数合同：[slime/agent/sandbox.py:82](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82-L105)
- 路径及脚本：[slime/agent/sandbox.py:107](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L107-L113)
- 调用方固定参数：[slime/agent/harness/common.py:111](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L111-L121)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## C03

**核对事实：** 清理和防重启动是两次环境请求；env仅在启动传入，后台命令的返回不同于CLI最终退出状态。

- 清理与防重约束：[slime/agent/sandbox.py:115](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L115-L128)
- 后台启动：[slime/agent/sandbox.py:129](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L129-L138)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## C04

**核对事实：** 等待函数先睡5秒再检查文件；ec是检查命令状态，文件文本转换的整数才是CLI状态。预算从进入等待时计时。

- 等待标记：[slime/agent/sandbox.py:62](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L62-L79)
- 等待调用：[slime/agent/sandbox.py:139](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L139-L139)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## C05

**核对事实：** 成功且不需要输出返回空文本，需要输出时读文件，否则取最多512字节尾部；run_agent忽略output。

- 输出返回分支：[slime/agent/sandbox.py:139](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L139-L145)
- 上层只保留状态：[slime/agent/harness/common.py:111](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L111-L122)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## C06

**核对事实：** 防重目录只防同次传输重放；相同tag不允许重叠；预算耗尽不杀CLI，异常和取消向外传播，回收由外层处理。

- 防重源码注释：[slime/agent/sandbox.py:115](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L115-L121)
- 等待预算：[slime/agent/sandbox.py:62](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L62-L79)
- 工作环境finally：[examples/coding_agent_rl/generate.py:131](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L131-L134)
- 销毁尝试：[slime/agent/sandbox.py:302](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L302-L307)
- 源码契约测试：[tests/test_agent/test_sandbox_exec_and_wait.py:147](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_sandbox_exec_and_wait.py#L147-L184)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## C07

**核对事实：** 正常返回后外层收集diff并退出工作环境再评估；CLI模型请求发生在执行期间，调用配置指向Adapter。

- 任务接回状态和diff：[examples/coding_agent_rl/generate.py:203](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L203-L219)
- 模型入口及调用：[slime/agent/harness/claude_code.py:57](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L57-L71)

**核对方式与结果：** 静态检查调用与定义，范围见 `source-groups.json`；运行返回分支另见受控依赖记录，防重目录的真实shell行为仅静态核对。

## 阅读伪代码

开头的缩进骨架用于说明调用下钻和本章范围，不是源码摘录，也不是完整可执行 Python。其调用关系由 C01／C07 核对，具体执行和返回由 C02–C06 核对；真实摘录单独记录在 `source-groups.json` 的 `excerpts` 中。
