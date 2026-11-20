# 环境执行、文件与挂载 · U39–U47

Harbor 要从同一次 Trial 得到命令结果或读回文件。挂载查询决定是否发生复制，适合与 `download_dir` 交叉看。 [全部用法](../README.md)

| 编号 | 交接 |
| --- | --- |
| [U39](U39-upload_file%20把一个宿主文件交给环境.md#u39) | upload_file 把一个宿主文件交给环境 |
| [U40](U40-upload_dir%20把一个目录交给环境.md#u40) | upload_dir 把一个目录交给环境 |
| [U41](U41-download_file%20把一个环境文件交回宿主.md#u41) | download_file 把一个环境文件交回宿主 |
| [U42](U42-download_dir%20回收环境里的非空日志目录.md#u42) | download_dir 回收环境里的非空日志目录 |
| [U43](U43-exec%20返回%20Harbor%20的%20ExecResult.md#u43) | exec 返回 Harbor 的 ExecResult |
| [U44](U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) | Trial 回收前查询挂载是否与宿主目录对应 |
| [U45](U45-exec%20通过%20_resolve_user%20取得生效用户.md#u45) | exec 通过 _resolve_user 取得生效用户 |
| [U46](U46-exec%20通过%20_merge_env%20得到最终命令环境.md#u46) | exec 通过 _merge_env 得到最终命令环境 |
| [U47](U47-exec%20通过%20_output_callback%20转发标准输出与错误输出.md#u47) | exec 通过 _output_callback 转发标准输出与错误输出 |
