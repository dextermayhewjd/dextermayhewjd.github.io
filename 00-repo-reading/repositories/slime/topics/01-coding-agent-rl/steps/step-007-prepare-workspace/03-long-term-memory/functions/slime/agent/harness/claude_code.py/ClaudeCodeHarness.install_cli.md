# ClaudeCodeHarness.install_cli

完整安装记录见 [common.py::install_npm_cli](../common.py/install_npm_cli.md)。本文件保留 Claude Code 的参数适配与委托入口。

- 源码定位：[slime/agent/harness/claude_code.py:36–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L36-L42)，由助手核对。
- 首次接触：Step 5，先在启动沙箱的骨架中定位，2026-10-22 接续展开。
- 最近认识更新：2026-10-22，用户明确指出这里主要传入参数，具体安装实现应读 common；此前关于本机材料与远端环境的表述继续保留在原始讨论中。

`ClaudeCodeHarness` 实现 `BaseHarness.install_cli` 接口。本方法读取 Node 和 Claude Code 包的路径，指定 Claude 检查命令，再 `await install_npm_cli(...)`。公共函数负责实际安装的编排；这是一处显式委托调用。

当前路径由 `SWE_AGENT="claude_code"` 选中此 Harness。`boot_agent_sandbox:111` 把已经进入的 `cand` 传为 `sb`；安装完成后返回 `None`，再回到父函数的 `sb = cand`。参数来源、场景输入输出与安装阶段统一见上面的主记录。

来源与历史：

- 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：Harness 选择见 `generate.py:45–52`，调用与返回位置见 `109–115`；配置与本方法见 `claude_code.py:19–20、36–42`；基类接口见 `harness/common.py:63–66`。
- [Step 5 · 首次进入 CLI 安装](../../../../../../../step-006-agent-sandbox/04-flow.md#install-cli-entry)保留最初原话与交接说明；[上传与远端安装](../../../../../../../step-006-agent-sandbox/04-flow.md#upload-and-remote-install)保留后续复述和疑问；[本次主次调整](../../../../../../../step-006-agent-sandbox/04-flow.md#common-install-primary-record)记录改为引用入口的依据。
- 尚未展开的等待、重试与包版本问题保存在主记录的“尚不清楚”中。本轮仅静态核对，没有读取真实配置、上传文件或运行安装。
