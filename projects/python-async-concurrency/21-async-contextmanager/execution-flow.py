# T = 执行顺序；L = example.py 的真实行号。
# 两条泳道共用一个 Task；每行只在一处执行代码。
# CALLER = exercise；RESOURCE = boot_agent_sandbox 的生成器函数体。
# WAIT(loop) = Task 暂停，等事件循环再次调度；RESUME = 从 await 恢复。
# YIELD(sb) = 生成器交出资源并暂停，当前 Task 转回 CALLER。
# ENTER / EXIT = async with 的进入 / 退出调用；它们本身不是挂起标记。
# +------+------------------------------+---------------------------------+------------------------+
# | STEP | CALLER (exercise)            | RESOURCE (boot_agent_sandbox)   | OUTPUT                 |
# +------+------------------------------+---------------------------------+------------------------+
# | T01  | L20-21 create; print         |                                 | manager created        |
# | T02  | L22 ENTER -> T03             |                                 |                        |
# | T03  |                              | L7 print; L8 WAIT(loop)         | boot demo-image case-1 |
# | T04  |                              | L8 RESUME; L9-10 prepare        |                        |
# | T05  |                              | L11 YIELD(sb) -> T06            |                        |
# | T06  | L22 as sandbox; L23 print    |                                 | inside True            |
# | T07  | L24 WAIT(loop)               |                                 |                        |
# | T08  | L24 RESUME; body ends        |                                 |                        |
# | T09  | L22 EXIT -> T10              |                                 |                        |
# | T10  |                              | L11 resume; L13 print           | closing case-1         |
# | T11  |                              | L14 WAIT(loop)                  |                        |
# | T12  |                              | L14 RESUME; L15-16 close; END   | closed case-1          |
# | T13  | L22 exit done; L25 print     |                                 | outside False          |
# +------+------------------------------+---------------------------------+------------------------+
# T02-T05: CALLER 的 L22 还在进入阶段，准备完成后才到 T06 使用资源。
# T03/T11: Task 分别停在 L8/L14；CALLER 不能提前执行使用区或块外代码。
# T05-T06: yield 仅暂停生成器，不把当前 Task 交回事件循环。
# T05-T10: 生成器停在 L11，直到 T09 请求退出，才在 T10 继续。
# T07-T08: Task 停在使用区的 L24；生成器仍停在 L11。
# T09-T12: 使用区已结束；L22 的退出流程再次推进生成器，完成 finally。
# T13: 退出清理已结束，CALLER 才运行 L25；END 表示生成器函数体结束。
