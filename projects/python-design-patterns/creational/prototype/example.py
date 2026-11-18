"""
Prototype - Python 3.12+ Example: typing.Self Type-Safe Cloning
"""
from dataclasses import dataclass, replace
from typing import Self

type Properties = dict[str, str | int]


@dataclass(frozen=True)
class DocumentTemplate:
    title: str
    content: str
    properties: Properties

    def clone_with(self, **changes) -> Self:
        # 依据已有模板创建新实例，覆盖指定字段；未修改的字段值继续复用。
        return replace(self, **changes)


if __name__ == "__main__":
    base_doc = DocumentTemplate(
        title="Report Template",
        content="Standard body text",
        properties={"version": 1, "status": "draft"},
    )
    custom_doc = base_doc.clone_with(title="Q4 Financial Report")
    print(f"Base: {base_doc.title}")
    print(f"Copy: {custom_doc.title}")
