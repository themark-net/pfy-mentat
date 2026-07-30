"""Hidden tests for 011-fizzbuzz."""
from __future__ import annotations

def run_tests(ns: dict) -> list[str]:
    fn = ns.get("fizzbuzz")
    if not callable(fn):
        return ["fizzbuzz not defined or not callable"]
    fails: list[str] = []
    cases = {
        0: [],
        1: ["1"],
        3: ["1", "2", "Fizz"],
        5: ["1", "2", "Fizz", "4", "Buzz"],
        15: [
            "1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
            "11", "Fizz", "13", "14", "FizzBuzz",
        ],
    }
    for n, expect in cases.items():
        try:
            got = fn(n)
        except Exception as e:  # noqa: BLE001
            fails.append(f"fizzbuzz({n}) raised {type(e).__name__}: {e}")
            continue
        if list(got) != expect:
            fails.append(f"fizzbuzz({n}) -> {got!r}, want {expect!r}")
    return fails
