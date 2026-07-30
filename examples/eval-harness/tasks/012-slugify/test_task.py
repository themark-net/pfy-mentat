"""Hidden tests for 012-slugify."""
from __future__ import annotations

def run_tests(ns: dict) -> list[str]:
    fn = ns.get("slugify")
    if not callable(fn):
        return ["slugify not defined or not callable"]
    fails: list[str] = []
    cases = [
        ("Hello World", "hello-world"),
        ("  Foo__Bar!! ", "foo-bar"),
        ("---", ""),
        ("", ""),
        ("ABC-123", "abc-123"),
        ("a   b", "a-b"),
        ("###", ""),
    ]
    for s, expect in cases:
        try:
            got = fn(s)
        except Exception as e:  # noqa: BLE001
            fails.append(f"slugify({s!r}) raised {type(e).__name__}: {e}")
            continue
        if got != expect:
            fails.append(f"slugify({s!r}) -> {got!r}, want {expect!r}")
    return fails
