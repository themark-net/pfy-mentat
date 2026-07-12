"""Hidden tests for task 002-fix-sum-evens."""

from __future__ import annotations


def run_tests(ns: dict) -> list[str]:
    """Return list of failure messages (empty = pass)."""
    fn = ns.get("sum_evens")
    if not callable(fn):
        return ["sum_evens not defined or not callable"]

    cases = [
        ([], 0),
        ([1, 2, 3, 4], 6),
        ([1, 3, 5], 0),
        ([2, 4, 6], 12),
        ([0, -2, 3], -2),
        ([10], 10),
        ([9], 0),
    ]
    fails: list[str] = []
    for nums, expect in cases:
        try:
            got = fn(list(nums))
        except Exception as e:  # noqa: BLE001
            fails.append(f"sum_evens({nums!r}) raised {type(e).__name__}: {e}")
            continue
        if got != expect:
            fails.append(f"sum_evens({nums!r}) -> {got!r}, want {expect!r}")
    return fails
