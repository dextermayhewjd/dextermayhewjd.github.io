### 3.1 Adapter 具体在适配什么？ {#adapter-role}

**使用心智模型：保留旧服务，在外面接一个转换层，让它能按调用方期待的方法和数据格式工作。**

| 位置 | 方法与数据 |
| --- | --- |
| 旧服务 XMLService | `get_xml_payload()` 返回 XML 字符串 |
| 调用方期望的 DataSource 接口 | `fetch_raw_data()` 返回字典 |
| XMLToDictAdapter | 提供新接口，内部调用旧服务，再把结果交给 parser 转换 |

真正的适配行为是主例中的两行：

```python
raw = self._service.get_xml_payload()  # 按旧服务的接口拿到字符串。
return self._parser(raw)  # 把字符串转换成调用方需要的字典。
```

适配器不重新实现旧服务，也不负责生成这份原始 XML。它封装了方法调用和格式转换，使调用方只需面对 `fetch_raw_data()`。

`DataSource` 只描述调用方期望的接口；`Converter[In, Out]` 和 `T` 描述类型。真正工作的仍是上面两次函数调用。

### 3.2 用具名函数做真正的字段解析 {#adapter-parse-record}

原例的 lambda 只替换尖括号，再把整段文本放进 `parsed` 字段，适合作为类型转换演示，但不容易看出 XML 数据的实际用途。

更直观的使用方式是：**保留主例的类定义，把转换函数换成解析字段的 `parse_record`。** 下面是补充用法，不改动本地项目的原始主例：

```python
from xml.etree import ElementTree


def parse_record(xml: str) -> dict[str, str]:
    root = ElementTree.fromstring(xml)  # 将 XML 字符串解析成元素树。
    return {child.tag: child.text or "" for child in root}  # 取第一层子元素的名称和文本。


source: DataSource = XMLToDictAdapter(XMLService(), parse_record)
record = source.fetch_raw_data()  # 调用方使用期望的接口，得到字典。
print(record)
print(record["name"])
```

输出：

```text
{'id': '101', 'name': 'Alice'}
Alice
```

现在可以看清完整关系：旧服务给 XML，适配器调用解析函数，调用方得到可按字段读取的字典。更换转换函数，不需要修改 XMLService 或 XMLToDictAdapter 的实现。

这个 parse_record 只处理本例“一层 record 子元素都是文本”的结构，不是通用 XML 转字典算法。复杂嵌套、重复标签等数据需要按实际接口约定处理。

**一句话：Adapter 让调用方不必迁就旧接口，由转换层负责连接两边的差异。**
