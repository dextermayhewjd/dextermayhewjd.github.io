"""
Template Method - Python 3.12+ Example: PEP 695 Generic Workflow & @override
"""
from typing import override


class BaseWorkflow[T, R]:
    def execute(self, payload: T) -> R:
        # 外层固定先清洗再处理；具体步骤由子类重写。
        cleaned = self.sanitize(payload)
        return self.process(cleaned)

    def sanitize(self, payload: T) -> T:
        return payload

    def process(self, payload: T) -> R:
        raise NotImplementedError


class TextWorkflow(BaseWorkflow[str, int]):
    @override
    def sanitize(self, payload: str) -> str:
        return payload.strip()

    @override
    def process(self, payload: str) -> int:
        return len(payload)


if __name__ == "__main__":
    wf = TextWorkflow()
    count = wf.execute("   Hello World   ")
    print(f"Workflow processed count: {count}")
