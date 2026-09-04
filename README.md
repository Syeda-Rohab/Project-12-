# Project 12: Build a Dreaming Loop (Capstone)

A weekly loop that reads another loop's logs and proposes rule
changes as a PR — never a direct commit, never a guess without
evidence.

- **Time:** 2–3 hrs
- **Difficulty:** capstone
- **Concepts used:** Concept 12 (spine + improvement loop), Concept 11 (maker-checker), Concept 6 (schedule), Part 5 (human gate)

## Files
| File | Role |
|---|---|
| `dreaming_loop.py` | The analyzer + proposal drafter |
| `logs/loop.log` | A week of another loop's real log entries (input) |
| `logs/progress.md` | That loop's spine, for context |
| `skills/fix-lint-skill.md` | The rules file being proposed changes to |
| `dreaming-state.md` | The dreaming loop's own spine — last date checked |
| `.github/workflows/dreaming-loop.yml` | Weekly schedule (free, GitHub Actions) |

## The planted repeated failure
`logs/loop.log` has 7 days of entries from a daily lint loop
(Project 8's kind of loop). Two of them are the **same** failure,
planted by hand:
```
2026-08-30 | FAIL | RuntimeError: reviewer timed out ... scanning vendor/ (12,000+ files)
2026-09-02 | FAIL | RuntimeError: reviewer timed out ... scanning vendor/ (12,000+ files)
```

## Run it (local, free, one command)
```
python dreaming_loop.py
```

## What it did (already tested — proof)
```
[dreaming_loop] Analyzing 7 entries since 2026-08-27.
[dreaming_loop] Proposal drafted on branch 'claude/rules-update-20260904-110439'.
[dreaming_loop] New rule proposed: True
[dreaming_loop] Deletion proposed: True
```

**PR_DRAFT.md, with cited evidence:**
```
## Addition
6. Exclude vendor/, node_modules/, and other third-party directories
   from the scan — they are not our code and scanning them causes timeouts.

Evidence: Seen 2 times: 2026-08-30, 2026-09-02. Both failures are the
identical RuntimeError: the reviewer's file scan has no directory
exclusions, so it walks vendor/ (12,000+ files) every run and times
out at the 30s limit. Excluding vendor/ removes the cause directly.

## Deletion
5. Reject any file containing the literal string "DO NOT LINT" —

Evidence: Checked all 7 run(s) in this window — none mention a
"DO NOT LINT" marker being found or relevant. This rule has not been
needed by any recent run.
```

## Proof: `main` was never touched
```
$ git checkout main
$ cat skills/fix-lint-skill.md   # still has the old "DO NOT LINT" rule
$ cat dreaming-state.md          # still says last_checked: 2026-08-27
$ git branch -a
  claude/rules-update-20260904-110439
* main
```
The entire proposal — the new skill file, the updated state, the PR
description — lives only on the `claude/` branch. `main` is
byte-for-byte what it was before the loop ran.

## Proof: it doesn't guess when there's no evidence
Ran it a second time with only 1 new (non-repeated) log entry:
```
[dreaming_loop] New rule proposed: False
```
No repeated failure existed in that window, so no rule addition was
proposed — it only proposed the deletion, which had real evidence
(zero mentions across every checked run). This is the core design
requirement: **no evidence, no proposal.**

## Done-when checklist
- [x] **The PR's proposed change traces to real, cited log entries** —
      the addition names the exact two dates and quotes the identical
      error text; the deletion names the exact count of runs checked.
- [x] **A deliberately planted repeated failure was caught** — the
      `vendor/` timeout, planted by hand on 2026-08-30 and 2026-09-02,
      was correctly grouped and turned into a proposal.
- [x] **Nothing changed in the rules file without merging** — verified
      above: `main`'s `skills/fix-lint-skill.md` is untouched.

## Setting up the real weekly schedule (GitHub, free)
1. Push this repo to GitHub.
2. The workflow in `.github/workflows/dreaming-loop.yml` runs every
   Monday at 3am UTC automatically (`cron`), or on demand via
   **Actions → Dreaming Loop → Run workflow**.
3. It uses `gh pr create` (GitHub's own free CLI, pre-installed on
   Actions runners) with the repo's automatic `GITHUB_TOKEN` — no
   extra token needed, unlike Project 11's cross-repo trigger.
4. Real PRs will appear in the **Pull requests** tab, ready for you
   to review and merge (or close) — exactly like the local version,
   just automated on a real calendar.

## Why "no evidence, no proposal" matters
An improvement loop that proposes plausible-sounding rule changes
without counting real occurrences will eventually propose something
wrong — and because future runs follow whatever rules got merged,
one bad guess compounds into every run after it. Citing exact dates
and counts means a human reviewing the PR can verify the claim in
seconds instead of having to trust it.
