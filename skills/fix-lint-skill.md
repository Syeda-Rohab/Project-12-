# Skill: Daily Lint Sweep

1. Trailing whitespace → always safe to auto-fix.
2. Lines over 100 characters → never auto-fix (could break code) — just
   flag them for a human.
3. Only touch source files, never test files.
4. One commit per run, in its own branch — never on main.
5. Reject any file containing the literal string "DO NOT LINT" —
   check every scanned file for this marker before touching it.

6. Exclude vendor/, node_modules/, and other third-party directories from the scan — they are not our code and scanning them causes timeouts.
