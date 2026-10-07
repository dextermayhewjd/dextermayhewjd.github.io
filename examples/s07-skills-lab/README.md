# S07 Skills Lab

S07 最后附录的完整练习包。目标是在同一个 review-diff 场景中观察结构、发现、调用、渐进披露、渲染、权限、Hook、子 Agent、评估和主循环接入。

## 环境与入口
脚本面向 Linux/macOS：Python 3.10+、Git、Bash。文件与配置可阅读；实际 Skill 调用还需要支持相应字段的 Claude Code。无第三方 Python 依赖。
默认项目使用 Python 标准库复现 S07.8 的空输入回归；机制与该节 JavaScript 示例相同。

从本目录生成独立练习仓库：
```bash
python3 tools/new_case.py --destination /tmp/s07-inline-case --variant inline --case empty-list
cd /tmp/s07-inline-case
claude
```

在 Claude Code 中：
```text
/review-diff src 空输入
```

每个变体使用一个新目录和新会话。不要在同一个已加载 Skill 的会话里反复替换文件后假定全部状态已清空。

## 变体
inline 是完整主例；manual、model-only、fork-wait、fork-background、preload、worktree、render-failure 分别覆盖互斥设置或失败路径。
worktree 变体用于观察工作目录隔离，不应期待子工作树自动带入父目录未提交的回归。代理文件在基线提交中已存在，才便于隔离工作区加载它。

## 文件、章节和注意点
manifest.json 为每个文件记录用途、对应章节与注意点；博客附录从这份索引直接生成目录和文件内容。
discovery/ 是个人、管理、额外目录、插件与账号来源的实验模板，不会由生成器自动安装。
profiles/ 是显式传给 --settings 的对照配置，不自动应用到你的全局设置。
evals/ 提供提示、预期与结果表；空结果表不表示评估已经通过。

## 本地验证
```bash
python3 tools/verify_lab.py
python3 tools/trace_inline.py /tmp/s07-inline-case --caller model --arguments "src empty-input"
```

verify_lab 检查可确定的回归、Hook JSON 和脚本。trace_inline 是自定义教学模拟，没有模型调用，不实现官方调度、权限或完整消息协议。
真实的触发质量、一次性 Hook 生命周期、正文去重、后台行为仍需按博客步骤在 Claude Code 中记录。

## 对应博客
https://dextermayhewjd.github.io/projects/learn-claude-code/s07/10-appendix/
