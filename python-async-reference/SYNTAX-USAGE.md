# 语言语法统计

以下按 AST 节点计数，独立于 API 调用。async def 与异步生成器定义分开，后者内部 yield 另计。

| 语法类别 | slime | areal | verl |
| --- | ---: | ---: | ---: |
| async_comprehension | 0 | 6 | 3 |
| async_def | 281 | 1641 | 541 |
| async_for | 1 | 16 | 21 |
| async_generator_def | 7 | 63 | 18 |
| async_protocol_def | 0 | 2 | 0 |
| async_with | 42 | 424 | 42 |
| async_yield | 7 | 92 | 28 |
| await | 409 | 2328 | 799 |
