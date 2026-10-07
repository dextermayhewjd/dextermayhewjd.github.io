# S13 Agent Teams：持久队友与协作边界

源码基准：本地 learn-claude-code 的 ce8f9f186058939da54c9d6fead78dfb5d0fd6c3；只读取教学仓库，未修改源码。

主章延续文件夹式目录、三图对照、函数就近查看与悬停连线。图 1 直接引用 S12 的 SVG，几何与路由保持一致，六个 Cron 内部步骤标灰色虚线提示展示合并；图 2 保留累积学习骨架，将 Cron 折叠为登记／事件交付索引，完整展开启动、队友 WORK、邮箱、IDLE 与 Lead CLI 唤醒。图 3 解释持久线程的核心循环，内部函数链接关联真实代码，不列具体 spawn 工具包装。

四个现有子章节填入消息协作、计划／关机协议、任务认领与 worktree 生命周期，各有局部图和逐步代码。主章承担整体接入点，避免把全部细节堆进总图；子章节函数链接定位正文实现，保留 Worktree 的旧 S18 路径别名。

核心判断：每个队友拥有私有 system、messages、tools 与 handlers；线程可以并行，但同一队友的工具执行顺序不变。无工具表示一轮结束而非队友退出；result 是汇报，completed 是显式任务状态；完整队友历史不直接合并到 Lead。

消息由运行时收取，Lead 在 CLI 等待边界将事件追加为 user 消息后继续普通 Agent Loop。邮箱 RLock／Condition 仅在同一进程协调，消费后删除文件，没有持久 ACK；任务认领另使用线程锁加 fcntl 文件锁。关机在收信边界生效，不抢占当前 API 或工具批次。

计划闸门实际拦截 Bash、写与编辑；回复匹配 request_id、当前任务和工作版本。Lead 先提团队等确认、spawn 后结束回合是 SYSTEM 策略，不能写成 Python 已强制执行的审批状态机。

可选 worktree 必须在任务 pending 且未认领时先创建，再 spawn／claim。cwd 通过 assignment 显式传给工具，不使用全局 chdir，也不是安全沙箱。完成任务后到回合边界才释放目录租约；移除 checkout 是宿主操作，不是模型工具，分支始终保留。

独立 S13 程序包含基础工具、Hooks、Task System、Teams、协议与 worktree，未合入 Cron、后台 Bash、Memory、Skills、Compact。图中的旧接口必须注明累积复习范围。

验证记录：Hugo 构建、项目导航、总图／核心图及四个局部图的路由检查通过。S13 源码 AST、子章节锚点与 390／1180／1600 宽度浏览器检查共五项通过，覆盖上一章几何复用、悬停输入输出、精确代码查看、整页滚动保持、角色、图中文字边界、ID 唯一与窄屏布局。教学仓库 agent_teams_runtime 离线测试 64 项及 69 个子测试通过；另用截图检查总图、核心、协议和 worktree 排版。
