# Step 016 · 补充前序 Step 标注前的整体位置图

本文件仅保存本轮修改前的 3.1 快照；现行入口见 [scope](../01-scope.md#overall-position)。

### 3.1 整体位置

下面按正常执行关系定位；括号中的已读组件是配置的 rollout 路径的背景，不代表所有运行模式固定使用本地 worker。

```text
RolloutManager._generate
  ├─ _get_rollout_data
  │    ├─ call_rollout_fn → 配置的 rollout 入口
  │    │    └─ 生成、评分、收集结果
  │    │       （已读：generate_and_rm / group、worker、完成组过滤）
  │    └─ 展开嵌套列表 → list[Sample]          # rollout.py:567–570
  ├─ batch_builder.begin → 检查可复用的转换   # 本轮选择未命中缓存
  ├─ batch_builder.convert(data)             # rollout.py:385【本步】
  │    └─ train_data 字典
  └─ batch_builder.split_by_dp(data)          # rollout.py:390，后续边界
       └─ 交给训练侧的数据分配
```

