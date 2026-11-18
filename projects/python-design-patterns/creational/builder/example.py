"""
Builder - Python 3.12+ Example: typing.Self Fluent Builder
"""
from dataclasses import dataclass, field
from typing import Self


@dataclass
class Query:
    table: str = ""
    fields: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    limit: int | None = None


class QueryBuilder:
    def __init__(self) -> None:
        self._query = Query()

    def from_table(self, table: str) -> Self:
        self._query.table = table
        return self

    def select(self, *fields: str) -> Self:
        self._query.fields.extend(fields)
        return self

    def where(self, condition: str) -> Self:
        self._query.filters.append(condition)
        return self

    def take(self, count: int) -> Self:
        self._query.limit = count
        return self

    def build(self) -> Query:
        # 交出内部的查询描述对象；这里不重新创建，也不执行查询。
        return self._query


if __name__ == "__main__":
    q = (
        QueryBuilder()
        .from_table("users")
        .select("id", "email")
        .where("active = 1")
        .take(5)
        .build()
    )
    print(f"Built Query: {q}")
