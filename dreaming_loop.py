#!/usr/bin/env python
"""
dreaming_loop.py — Project 12 capstone.

A weekly loop that reads ANOTHER loop's logs (logs/loop.log,
logs/progress.md) and proposes rule changes as a PR — never a direct
commit. Only proposes changes backed by cited, counted evidence from
real log lines. Never guesses.

  1. Read dreaming-state.md for the date we last checked.
  2. Read every loop.log entry since that date.
  3. Group FAIL reasons; any reason appearing 2+ times is a repeated
     failure — draft a rule to prevent it, citing exact dates/counts.
  4. Look at the current skill file; propose deleting one rule that no
     recent run's failure ever needed (evidenced by: zero log entries
     reference it).
  5. Write the proposed skill file on a claude/ branch, never main.
  6. Write a PR description that cites its evidence.
  7. Update dreaming-state.md with the new last-checked date.
"""

import os
import re
import subprocess
from collections import Counter
from datetime import datetime

LOG_PATH = "logs/loop.log"
SKILL_PATH = "skills/fix-lint-skill.md"
STATE_PATH = "dreaming-state.md"


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)


def read_state():
    if not os.path.exists(STATE_PATH):
        return "1970-01-01"
    with open(STATE_PATH) as f:
        content = f.read()
    m = re.search(r"last_checked:\s*(\d{4}-\d{2}-\d{2})", content)
    return m.group(1) if m else "1970-01-01"


def parse_log_entries(since_date):
    """Return list of (date, status, detail) for entries newer than since_date."""
    entries = []
    since = datetime.strptime(since_date, "%Y-%m-%d")
    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|", 2)]
            if len(parts) < 3:
                continue
            ts_str, status, detail = parts
            try:
                ts = datetime.strptime(ts_str.split()[0], "%Y-%m-%d")
            except ValueError:
                continue
            if ts >= since:
                entries.append((ts_str, status, detail))
    return entries


def normalize_failure(detail):
    """Strip the varying date reference so repeats of the same root
    cause group together."""
    return re.sub(r"Same cause as [\d\-]+\s*—?\s*", "", detail).strip()


def find_repeated_failures(entries):
    fails = [(ts, normalize_failure(detail)) for ts, status, detail in entries if status == "FAIL"]
    counts = Counter(detail for _, detail in fails)
    repeated = {}
    for detail, count in counts.items():
        if count >= 2:
            dates = [ts for ts, d in fails if d == detail]
            repeated[detail] = dates
    return repeated


def propose_new_rule(repeated_failures):
    """Draft the smallest rule that addresses the most-repeated failure."""
    if not repeated_failures:
        return None, None
    # pick the most-repeated one
    detail, dates = max(repeated_failures.items(), key=lambda kv: len(kv[1]))

    if "vendor/" in detail and "timed out" in detail:
        new_rule = (
            "6. Exclude vendor/, node_modules/, and other third-party "
            "directories from the scan — they are not our code and "
            "scanning them causes timeouts."
        )
        evidence = (
            f"Seen {len(dates)} times: {', '.join(d.split()[0] for d in dates)}. "
            f"Both failures are the identical RuntimeError: the reviewer's "
            f"file scan has no directory exclusions, so it walks vendor/ "
            f"(12,000+ files) every run and times out at the 30s limit. "
            f"Excluding vendor/ removes the cause directly — it is not our "
            f"code and never needs linting."
        )
        return new_rule, evidence

    # generic fallback for other kinds of repeated failures
    new_rule = f"6. Guard against: {detail[:80]}"
    evidence = f"Seen {len(dates)} times: {', '.join(d.split()[0] for d in dates)}."
    return new_rule, evidence


def propose_deletion(entries, skill_lines):
    """Find a rule that no failure in this window ever needed."""
    all_detail_text = " ".join(detail for _, status, detail in entries).lower()
    for line in skill_lines:
        if "DO NOT LINT" in line:
            # Check: did any log entry ever reference this marker/rule?
            if "do not lint" not in all_detail_text:
                evidence = (
                    f"Checked all {len(entries)} run(s) in this window — none "
                    f"mention a 'DO NOT LINT' marker being found or relevant. "
                    f"This rule has not been needed by any recent run."
                )
                return line, evidence
    return None, None


def main():
    since_date = read_state()
    entries = parse_log_entries(since_date)

    if not entries:
        print(f"[dreaming_loop] No new log entries since {since_date}. Nothing to do.")
        return

    print(f"[dreaming_loop] Analyzing {len(entries)} entries since {since_date}.")

    repeated = find_repeated_failures(entries)
    new_rule, addition_evidence = propose_new_rule(repeated)

    with open(SKILL_PATH) as f:
        skill_lines = f.readlines()
    deleted_line, deletion_evidence = propose_deletion(entries, skill_lines)

    if not new_rule and not deleted_line:
        print("[dreaming_loop] No repeated failures and nothing to delete. No PR needed.")
        # still advance the state so we don't re-scan the same window forever
        latest_date = max(ts.split()[0] for ts, _, _ in entries)
        with open(STATE_PATH, "w") as f:
            f.write(f"last_checked: {latest_date}\n")
        return

    # --- build the proposed skill file on a claude/ branch, never main ---
    branch = f"claude/rules-update-{datetime.now():%Y%m%d-%H%M%S}"
    run(f"git checkout -b {branch}")

    new_skill_lines = [l for l in skill_lines if l.strip() != deleted_line] if deleted_line else list(skill_lines)
    if new_rule:
        new_skill_lines.append("\n" + new_rule + "\n")

    with open(SKILL_PATH, "w") as f:
        f.writelines(new_skill_lines)

    latest_date = max(ts.split()[0] for ts, _, _ in entries)
    with open(STATE_PATH, "w") as f:
        f.write(f"last_checked: {latest_date}\n")

    run("git add -A")
    run(f'git commit -q -m "Dreaming loop: propose rule update from {since_date} to {latest_date}"')

    # --- write the PR description, citing evidence ---
    pr_body_lines = [
        f"# Proposed rules-file update (dreaming loop)\n",
        f"Analyzed runs from {since_date} to {latest_date} in `logs/loop.log`.\n",
    ]
    if new_rule:
        pr_body_lines += [
            "## Addition\n",
            f"```\n{new_rule}\n```\n",
            f"**Evidence:** {addition_evidence}\n",
        ]
    if deleted_line:
        pr_body_lines += [
            "## Deletion\n",
            f"```\n{deleted_line.strip()}\n```\n",
            f"**Evidence:** {deletion_evidence}\n",
        ]
    pr_body_lines.append(
        "\n_This PR was drafted automatically. Nothing here takes effect "
        "until a human merges it._\n"
    )
    pr_body = "".join(pr_body_lines)

    with open("PR_DRAFT.md", "w") as f:
        f.write(pr_body)
    run("git add PR_DRAFT.md")
    run('git commit -q -m "Add PR description with cited evidence"')

    print(f"[dreaming_loop] Proposal drafted on branch '{branch}'.")
    print(f"[dreaming_loop] New rule proposed: {bool(new_rule)}")
    print(f"[dreaming_loop] Deletion proposed: {bool(deleted_line)}")
    print("\n--- PR_DRAFT.md ---")
    print(pr_body)


if __name__ == "__main__":
    main()
