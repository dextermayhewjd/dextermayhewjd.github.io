# Step 008 · 本步短期记录

| 函数 | 本步范围 |
| --- | --- |
| [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#extract-segments) | 从前序调取；取出本次段列表，接收转换后的 Sample 列表 |
| [expand_segments_to_samples](functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md) | 已看排序、每段复制与委派、归属/奖励字段和列表返回 |
| [write_sample_from_segment](functions/dressage/rollout/artifacts/samples.py/write_sample_from_segment.md) | 按四段梳理全函数主干；重点是响应后缀训练表示、文本/来源和状态返回，可选分支按条件深入 |
