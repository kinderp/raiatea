# Evaluator-session aggregate summary

Issue: #90  
Parent: #87

Define one deterministic local summary from the immutable validated record snapshots produced by #89.

The summary contains only the fixed format/version, accepted record count, sorted input SHA-256 provenance, per-platform and per-launcher counts, and true/false totals for the eight canonical evaluator-session result keys.

No observations, free text, names, paths, timestamps, learner data, machine details, accounts or automatically collected metadata are copied into the summary.

Inputs are never modified. Output serialization is canonical and reproducible. Existing output files are not replaced.

This increment does not package the workflow, add remote behavior, infer themes, import learner evidence or create a dashboard. Packaging and cross-platform kit acceptance remain #91.
