# Supervised pilot runbook finding log

Issue/PR: #94  
Parent: #93

## Resolved findings

- **F1 — Session phases could be reordered or expanded silently.** Resolved by one canonical ordered phase tuple and a closed `phases` object.
- **F2 — Checklist status could contradict phase results.** Resolved by explicit fail-closed rules for `not-started`, `in-progress`, `completed` and `stopped`.
- **F3 — Platform and launcher could be paired incorrectly.** Resolved by fixed Windows/PowerShell and Linux/macOS/POSIX pairing.
- **F4 — Completion could be declared before cleanup.** Resolved by requiring every phase, including owned-state and temporary-copy cleanup, to be true for `completed`.
- **F5 — A stopped session could omit the stop action.** Resolved by requiring `pilotStopped=true` for `stopped`.
- **F6 — The checklist could collect identifying or free-form data.** Resolved by a closed top-level field set with no names, class IDs, answers, timestamps, observations or device details.
- **F7 — Checklist output could overwrite an existing record.** Resolved by exclusive no-replace installation from a closed temporary descriptor.
- **F8 — Symbolic-link or non-file inputs could be accepted.** Resolved by regular-file-only loading and symlink rejection.

## Open findings

None.
