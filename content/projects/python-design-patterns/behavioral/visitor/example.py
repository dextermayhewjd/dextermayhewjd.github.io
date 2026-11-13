"""
Visitor - Python 3.12+ Example: PEP 695 Type Alias & Pattern Matching
"""
from dataclasses import dataclass

type Expression = Num | BinOp


@dataclass
class Num:
    value: int


@dataclass
class BinOp:
    left: Expression
    op: str
    right: Expression


def evaluate_expression(expr: Expression) -> int:
    match expr:
        case Num(val):
            return val
        case BinOp(l, "+", r):
            # 递归计算左右子表达式，再组合为加法结果。
            return evaluate_expression(l) + evaluate_expression(r)
        case BinOp(l, "*", r):
            return evaluate_expression(l) * evaluate_expression(r)
        case _:
            raise ValueError(f"Unknown operation: {expr}")


if __name__ == "__main__":
    ast: Expression = BinOp(Num(3), "*", BinOp(Num(4), "+", Num(5)))
    print("Evaluated AST:", evaluate_expression(ast))
