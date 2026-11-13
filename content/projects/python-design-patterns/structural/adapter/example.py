"""
Adapter - Python 3.12+ Example: PEP 695 Generic Adapter & @override
"""
from collections.abc import Callable
from typing import Protocol

type Converter[In, Out] = Callable[[In], Out]


class DataSource(Protocol):
    def fetch_raw_data(self) -> dict[str, str]: ...


class XMLService:
    def get_xml_payload(self) -> str:
        return "<record><id>101</id><name>Alice</name></record>"


class XMLToDictAdapter[T: XMLService]:
    def __init__(self, service: T, parser: Converter[str, dict[str, str]]) -> None:
        self._service = service
        self._parser = parser

    def fetch_raw_data(self) -> dict[str, str]:
        # 从已有服务取出 XML 字符串，再交给转换函数。
        raw = self._service.get_xml_payload()
        return self._parser(raw)


if __name__ == "__main__":
    adapter = XMLToDictAdapter(
        XMLService(),
        lambda xml: {"parsed": xml.replace("<", "[").replace(">", "]")},
    )
    print(f"Adapted output: {adapter.fetch_raw_data()}")
