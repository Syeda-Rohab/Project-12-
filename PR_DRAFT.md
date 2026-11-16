# Proposed rules-file update (dreaming loop)
Analyzed runs from 2026-08-27 to 2026-09-03 in `logs/loop.log`.
## Addition
```
6. Exclude vendor/, node_modules/, and other third-party directories from the scan — they are not our code and scanning them causes timeouts.
```
**Evidence:** Seen 2 times: 2026-08-30, 2026-09-02. Both failures are the identical RuntimeError: the reviewer's file scan has no directory exclusions, so it walks vendor/ (12,000+ files) every run and times out at the 30s limit. Excluding vendor/ removes the cause directly — it is not our code and never needs linting.
## Deletion
```
5. Reject any file containing the literal string "DO NOT LINT" —
```
**Evidence:** Checked all 7 run(s) in this window — none mention a 'DO NOT LINT' marker being found or relevant. This rule has not been needed by any recent run.

_This PR was drafted automatically. Nothing here takes effect until a human merges it._
