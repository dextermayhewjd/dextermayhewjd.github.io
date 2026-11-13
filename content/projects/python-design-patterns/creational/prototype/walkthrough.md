### 3.1 只覆盖 title，新实例的其他字段从哪里来？ {#prototype-field-reuse}

**新建的是一个完整的 DocumentTemplate 实例，不是只创建被修改的 title 字段。** `replace` 用旧实例补齐没有指定的字段。

针对这个简单 dataclass，下面的写法可以帮助理解字段值的来源；它不是 `replace` 的源码：

```python
custom_doc = DocumentTemplate(
    title="Q4 Financial Report",  # 本次指定的新值。
    content=base_doc.content,     # 没有指定，沿用旧实例的字段值。
    properties=base_doc.properties,  # 沿用的是同一个字典引用。
)
```

| 字段 | 原实例 base_doc | 新实例 custom_doc |
| --- | --- | --- |
| `title` | `"Report Template"` | `"Q4 Financial Report"` |
| `content` | `"Standard body text"` | 沿用同一个字符串值 |
| `properties` | 原来的字典 | 指向同一个字典，没有另外复制 |

因此，两种身份判断的结果不同：

```python
print(custom_doc is base_doc)  # False：外层是两个实例。
print(custom_doc.properties is base_doc.properties)  # True：字段引用的是同一个字典。
```

如果通过其中一个实例修改这个共享字典，另一个实例也会看到变化。`frozen=True` 限制实例字段重新赋值，但不会把字段指向的字典也冻结。

**这里的“覆盖”是为新实例选用字段值；“新实例”不等于内部所有对象都被深拷贝。**
