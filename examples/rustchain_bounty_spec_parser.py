#!/usr/bin/env python3
"""
Parse RustChain/Elyan Labs machine-readable `bounty-spec` blocks safely.

This educational parser intentionally supports only the simple subset used by
the bounty issues: booleans, integers/floats, strings and one-line [lists].
It does not execute YAML tags or arbitrary Python.
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SPEC_RE = re.compile(r"```bounty-spec\s*(.*?)```", re.DOTALL | re.IGNORECASE)
TITLE_RTC_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*RTC\b", re.IGNORECASE)

ALLOWED_KEYS = {
    "paid",
    "reward_rtc",
    "per",
    "cap",
    "submit",
    "not_in_repo",
}


@dataclass(frozen=True)
class ParsedBounty:
    title_reward_rtc: float | None
    spec_reward_rtc: float | None
    effective_reward_rtc: float | None
    fields: dict[str, Any]
    warnings: tuple[str, ...]


def parse_scalar(raw: str) -> Any:
    value = raw.strip()

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = []
        for item in inner.split(","):
            item = item.strip()
            if (item.startswith('"') and item.endswith('"')) or (
                item.startswith("'") and item.endswith("'")
            ):
                items.append(ast.literal_eval(item))
            else:
                items.append(item)
        return items

    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return ast.literal_eval(value)

    return value


def extract_spec(markdown: str) -> dict[str, Any]:
    match = SPEC_RE.search(markdown)
    if not match:
        raise ValueError("No ```bounty-spec ... ``` block found")

    fields: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Malformed spec line: {raw_line!r}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        if key not in ALLOWED_KEYS:
            raise ValueError(f"Unexpected key: {key!r}")
        if key in fields:
            raise ValueError(f"Duplicate key: {key!r}")

        fields[key] = parse_scalar(raw_value)

    return fields


def title_reward(title: str) -> float | None:
    values = [float(x) for x in TITLE_RTC_RE.findall(title)]
    if not values:
        return None
    if len(values) > 1:
        raise ValueError(
            "Title contains multiple RTC figures; require human review instead of guessing"
        )
    return values[0]


def parse_bounty(title: str, markdown: str) -> ParsedBounty:
    fields = extract_spec(markdown)
    title_rtc = title_reward(title)

    raw_spec_reward = fields.get("reward_rtc")
    if raw_spec_reward is not None and not isinstance(raw_spec_reward, (int, float)):
        raise ValueError("reward_rtc must be numeric")
    spec_rtc = float(raw_spec_reward) if raw_spec_reward is not None else None

    warnings: list[str] = []
    if title_rtc is not None and spec_rtc is not None and title_rtc != spec_rtc:
        warnings.append(
            f"reward mismatch: title={title_rtc:g} RTC, spec={spec_rtc:g} RTC; "
            "using title as authoritative"
        )

    effective = title_rtc if title_rtc is not None else spec_rtc

    if fields.get("paid") is not True:
        warnings.append("spec does not explicitly say paid: true")

    return ParsedBounty(
        title_reward_rtc=title_rtc,
        spec_reward_rtc=spec_rtc,
        effective_reward_rtc=effective,
        fields=fields,
        warnings=tuple(warnings),
    )


DEMO_TITLE = "[BOUNTY: 10 RTC] Example explainer"
DEMO_MARKDOWN = r"""
A historical body may still contain an older number.

```bounty-spec
paid: true
reward_rtc: 25
per: one-time
cap: 1
submit: [comment, email]
not_in_repo: true
```
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", help="GitHub issue title")
    parser.add_argument("--markdown-file", type=Path, help="File containing issue markdown")
    parser.add_argument("--demo", action="store_true", help="Run built-in mismatch demonstration")
    args = parser.parse_args()

    if args.demo:
        title = DEMO_TITLE
        markdown = DEMO_MARKDOWN
    else:
        if not args.title or not args.markdown_file:
            parser.error("use --demo or provide both --title and --markdown-file")
        title = args.title
        markdown = args.markdown_file.read_text(encoding="utf-8")

    parsed = parse_bounty(title, markdown)

    print(f"title_reward_rtc={parsed.title_reward_rtc}")
    print(f"spec_reward_rtc={parsed.spec_reward_rtc}")
    print(f"effective_reward_rtc={parsed.effective_reward_rtc}")
    print(f"paid={parsed.fields.get('paid')}")
    print(f"per={parsed.fields.get('per')}")
    print(f"cap={parsed.fields.get('cap')}")
    print(f"submit={parsed.fields.get('submit')}")
    print(f"not_in_repo={parsed.fields.get('not_in_repo')}")
    if parsed.warnings:
        for warning in parsed.warnings:
            print(f"WARNING: {warning}")
    else:
        print("WARNING: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
