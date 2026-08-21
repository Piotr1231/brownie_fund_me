# Parse RustChain bounty specs safely: never trust one number blindly

Elyan Labs and RustChain bounty issues often include a small machine-readable block named `bounty-spec`. That is useful for agents because it exposes fields such as whether a task is paid, the RTC reward, whether the reward is per item or one-time, the cap, and the allowed submission routes. But automation has a subtle failure mode: **metadata can become stale while the human-facing title changes**.

The current RustChain content-round rules explicitly warn about this documentation debt and say that the **figure in the issue title is authoritative** when an older issue body still contains a different pre-adjustment amount. The bounty repository is here: <https://github.com/Scottcjn/rustchain-bounties>, and the main RustChain project is here: <https://github.com/Scottcjn/Rustchain>.

This tutorial builds a small, defensive Python parser for those `bounty-spec` blocks. It does not scrape GitHub and it does not submit claims. Its job is narrower: take a title plus Markdown that you already obtained through an approved API or connector, extract the simple machine-readable fields, compare the title reward with `reward_rtc`, and **fail toward human review instead of silently guessing**.

## Why this matters to an agent

Suppose an old issue body says:

```text
reward_rtc: 25
```

but the title now says:

```text
[BOUNTY: 10 RTC] Example explainer
```

A naive agent may optimize its time around 25 RTC, do the work, and only discover at payout that the current rate is 10 RTC. The reverse mistake is also possible: an agent could ignore a newly increased title reward because it cached the body. Neither outcome is acceptable for autonomous work.

A robust workflow should therefore separate three concepts:

1. **Title reward** — the RTC number explicitly visible in the current issue title.
2. **Spec reward** — the numeric `reward_rtc` field in the fenced block.
3. **Effective reward** — the value the current program says to use when the two disagree.

For the current Elyan Labs rule, the effective reward is the title reward when one is present.

## The safe subset

The runnable example is in [`examples/rustchain_bounty_spec_parser.py`](../examples/rustchain_bounty_spec_parser.py).

It deliberately does **not** load arbitrary YAML. A general YAML loader has far more features than these bounty blocks need. The parser accepts only a small allowlist:

- `paid`
- `reward_rtc`
- `per`
- `cap`
- `submit`
- `not_in_repo`

It understands booleans, integers, simple decimal numbers, strings, and one-line lists such as `[comment, email]`. Unknown keys, duplicate keys, malformed lines, and ambiguous titles are rejected.

That is a useful security property. When an automation is reading data from public issue text, the parser should treat that text as untrusted input rather than as configuration code.

## Run the built-in mismatch demo

No third-party packages are needed. Run:

```bash
python examples/rustchain_bounty_spec_parser.py --demo
```

The demonstration intentionally provides a title containing `10 RTC` and a machine-readable body containing `reward_rtc: 25`.

The expected output is:

```text
title_reward_rtc=10.0
spec_reward_rtc=25.0
effective_reward_rtc=10.0
paid=True
per=one-time
cap=1
submit=['comment', 'email']
not_in_repo=True
WARNING: reward mismatch: title=10 RTC, spec=25 RTC; using title as authoritative
```

The important line is not merely the final number. It is the warning. An agent should preserve the discrepancy in its audit trail so a later reviewer can understand why the automation chose 10 rather than 25.

## Parse a saved issue body

If your approved GitHub tool saves the issue Markdown into `issue.md`, you can run:

```bash
python examples/rustchain_bounty_spec_parser.py \
  --title "[BOUNTY: 8 RTC] Example task" \
  --markdown-file issue.md
```

The code never needs a GitHub token. Fetching and authorization stay outside the parser. This keeps responsibilities clean: the connector reads the issue; the parser interprets a small data contract.

## Why the parser refuses multiple RTC figures

The title extractor intentionally raises an error when it finds multiple separate `N RTC` figures. For example, a title such as:

```text
[BOUNTY: 10 RTC base + 5 RTC bonus]
```

is economically ambiguous. Automatically selecting the first or largest number would invent policy. A safe agent should stop and inspect the rules.

The same principle applies when `paid` is missing or false. The program emits a warning rather than treating the presence of `reward_rtc` as proof that money is actually available.

## Turning this into an autonomous bounty filter

A production agent can put this parser between issue discovery and actual work:

```text
GitHub/API read
    ↓
current title + current body
    ↓
strict bounty-spec parser
    ↓
reward mismatch / paid / cap checks
    ↓
human or agent policy decision
    ↓
only then: perform work
```

Before spending compute or changing a repository, the agent can require all of the following:

- the issue is currently open;
- `paid: true` is present, or current maintainer text otherwise confirms funding;
- the effective reward is known;
- the cap is not already exhausted;
- the permitted submission route is usable;
- no later maintainer comment says the bounty has already been awarded.

This matters because an **open GitHub issue is not the same thing as an unclaimed funded bounty**. A stale open issue can remain visible long after a one-time reward has been paid.

## What this example does not prove

This parser does not prove that a treasury has enough RTC, that a maintainer will accept a deliverable, or that a claim is first in line. It also does not override live maintainer comments. Those are separate checks.

What it does provide is a reproducible first gate: **machine-readable metadata is useful, but current human-visible policy wins when the project explicitly says so, and discrepancies should be surfaced rather than hidden**.

For autonomous agents that are expected to spend real time chasing bounties, that small discipline prevents a surprisingly expensive class of mistakes.

## Validation

The example was executed locally with Python and also compiled with `py_compile`. The captured output is available in [`evidence/rustchain_bounty_spec_parser_output.txt`](../evidence/rustchain_bounty_spec_parser_output.txt).

**AI assistance disclosure:** this tutorial and example were developed with substantial assistance from OpenAI GPT-5.6 Sol under operator authorization. The code shown here was actually executed before publication.
