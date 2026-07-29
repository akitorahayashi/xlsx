#!/usr/bin/env python3
"""
Summarize a list of numbers passed as arguments, printing one JSON document.

This is the example skill CLI for the skills-plugin-py template. It shows the
conventions every script here follows: standard library only, one JSON document
on stdout, argparse arguments, explicit validation with an actionable error, and
meaningful exit codes.

Exit codes:
- 0: summarized at least one number
- 1: no numbers were given
- 2: an argument was not a number; stderr carries JSON with an "action"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional, Union

Number = Union[int, float]


class CLIError(Exception):
    """An input error carrying an action for the user to fix."""

    def __init__(self, message: str, action: str) -> None:
        super().__init__(message)
        self.action = action


def parse_number(text: str) -> Number:
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        raise CLIError(f"Not a number: {text!r}", "Pass only numeric values, e.g. 10 6 2.5.")


def summarize(numbers: List[Number]) -> Dict[str, Any]:
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }


def run(args: argparse.Namespace) -> int:
    numbers = [parse_number(value) for value in args.values]
    if not numbers:
        print(json.dumps({"count": 0, "hint": "Pass one or more numbers to summarize."}, indent=2))
        return 1
    print(json.dumps(summarize(numbers), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a list of numbers.")
    parser.add_argument("values", nargs="*", help="The numbers to summarize.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except CLIError as error:
        print(json.dumps({"error": str(error), "action": error.action}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
