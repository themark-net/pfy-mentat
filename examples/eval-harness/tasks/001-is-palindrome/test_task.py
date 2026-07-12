"""Hidden tests for task 001-is-palindrome. Loaded after candidate code."""

from __future__ import annotations


def run_tests(ns: dict) -> list[str]:
    """Return list of failure messages (empty = pass)."""
    fn = ns.get("is_palindrome")
    if not callable(fn):
        return ["is_palindrome not defined or not callable"]

    # Exact reverse (case-sensitive) — reliable for small local coding models
    cases = [
        ("", True),
        ("a", True),
        ("aba", True),
        ("ab", False),
        ("Aa", False),
        ("racecar", True),
        ("hello", False),
        ("12321", True),
    ]
    fails: list[str] = []
    for s, expect in cases:
        try:
            got = fn(s)
        except Exception as e:  # noqa: BLE001
            fails.append(f"is_palindrome({s!r}) raised {type(e).__name__}: {e}")
            continue
        if bool(got) is not expect:
            fails.append(f"is_palindrome({s!r}) -> {got!r}, want {expect!r}")
    return fails
