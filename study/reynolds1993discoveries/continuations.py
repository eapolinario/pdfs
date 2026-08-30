#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///

"""Executable derivations accompanying Reynolds's continuations paper."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class Num:
    value: int


@dataclass(frozen=True)
class Add:
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Mul:
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Trace:
    label: str
    body: "Expr"


Expr: TypeAlias = Num | Add | Mul | Trace
IntCont: TypeAlias = Callable[[int], int]


def evaluate_direct(expr: Expr, events: list[str]) -> int:
    match expr:
        case Num(value):
            return value
        case Add(left, right):
            return evaluate_direct(left, events) + evaluate_direct(right, events)
        case Mul(left, right):
            return evaluate_direct(left, events) * evaluate_direct(right, events)
        case Trace(label, body):
            events.append(label)
            return evaluate_direct(body, events)


def evaluate_cps(expr: Expr, k: IntCont, events: list[str]) -> int:
    match expr:
        case Num(value):
            return k(value)
        case Add(left, right):
            return evaluate_cps(
                left,
                lambda left_value: evaluate_cps(
                    right,
                    lambda right_value: k(left_value + right_value),
                    events,
                ),
                events,
            )
        case Mul(left, right):
            return evaluate_cps(
                left,
                lambda left_value: evaluate_cps(
                    right,
                    lambda right_value: k(left_value * right_value),
                    events,
                ),
                events,
            )
        case Trace(label, body):
            events.append(label)
            return evaluate_cps(body, k, events)


@dataclass(frozen=True)
class Jump:
    label: str
    state: tuple[int, int]


@dataclass(frozen=True)
class Halt:
    value: int


Transfer: TypeAlias = Jump | Halt
Block: TypeAlias = Callable[[tuple[int, int]], Transfer]


def run_blocks(
    blocks: dict[str, Block], entry: str, state: tuple[int, int]
) -> int:
    transfer: Transfer = Jump(entry, state)
    while isinstance(transfer, Jump):
        transfer = blocks[transfer.label](transfer.state)
    return transfer.value


def sum_to(n: int) -> int:
    def loop(state: tuple[int, int]) -> Transfer:
        remaining, total = state
        if remaining == 0:
            return Halt(total)
        return Jump("loop", (remaining - 1, total + remaining))

    return run_blocks({"loop": loop}, "loop", (n, 0))


Failure: TypeAlias = Callable[[], str]
Success: TypeAlias = Callable[[int, Failure], str]


def choose(values: Sequence[int], succeed: Success, fail: Failure) -> str:
    if not values:
        return fail()
    head, *tail = values
    return succeed(head, lambda: choose(tail, succeed, fail))


CpsComputation: TypeAlias = Callable[[IntCont], int]
CpsFunction: TypeAlias = Callable[[int], CpsComputation]
EscapeFunction: TypeAlias = Callable[[int], CpsComputation]


def pure(value: int) -> CpsComputation:
    return lambda k: k(value)


def bind(computation: CpsComputation, f: CpsFunction) -> CpsComputation:
    return lambda k: computation(lambda value: f(value)(k))


def call_cc(f: Callable[[EscapeFunction], CpsComputation]) -> CpsComputation:
    return lambda k: f(lambda value: lambda _ignored_k: k(value))(k)


def product_until_zero(values: Sequence[int]) -> CpsComputation:
    def with_escape(escape: EscapeFunction) -> CpsComputation:
        def loop(remaining: Sequence[int]) -> CpsComputation:
            if not remaining:
                return pure(1)
            head, *tail = remaining
            if head == 0:
                return escape(0)
            return bind(loop(tail), lambda subtotal: pure(head * subtotal))

        return loop(values)

    return call_cc(with_escape)


def demonstrate_expression_cps() -> None:
    expression = Add(
        Trace("left", Num(10)),
        Mul(Trace("right-left", Num(3)), Trace("right-right", Num(2))),
    )
    direct_events: list[str] = []
    cps_events: list[str] = []

    direct_result = evaluate_direct(expression, direct_events)
    cps_result = evaluate_cps(expression, lambda value: value, cps_events)

    assert direct_result == cps_result == 16
    assert direct_events == cps_events == ["left", "right-left", "right-right"]
    print("1. Direct and CPS evaluators agree:", cps_result)
    print("   CPS makes the order explicit:", " -> ".join(cps_events))


def demonstrate_tail_transfer() -> None:
    result = sum_to(1_000_000)
    assert result == 500_000_500_000
    print("2. One million tail transfers without host stack growth:", result)


def demonstrate_two_continuations() -> None:
    result = choose(
        [1, 3, 8, 10],
        lambda value, try_next: (
            f"accepted {value}" if value % 2 == 0 else try_next()
        ),
        lambda: "no answer",
    )
    assert result == "accepted 8"
    print("3. Failure continuations implement search:", result)


def demonstrate_call_cc() -> None:
    ordinary = product_until_zero([2, 3, 4])(lambda value: value)
    escaped = product_until_zero([2, 3, 0, 999])(lambda value: value)
    assert ordinary == 24
    assert escaped == 0
    print("4. call/cc packages the current continuation:", ordinary, escaped)


def main() -> None:
    demonstrate_expression_cps()
    demonstrate_tail_transfer()
    demonstrate_two_continuations()
    demonstrate_call_cc()


if __name__ == "__main__":
    main()
