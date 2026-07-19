# Evaluator-session batch manifest

Issue: #88  
Parent: #87

## Goal

Define a closed deterministic local manifest for explicitly supplied evaluator-session v1 JSON files.

## Entry contract

Each entry contains exactly a canonical relative POSIX path, a lowercase SHA-256 digest, and the expected evaluator-session format/version. Entries are non-empty and sorted by path.

Absolute paths, backslashes, dot segments, parent traversal, duplicate paths and duplicate digests are rejected.

## Scope

This increment validates manifest structure only. It does not read referenced records, aggregate results or create summaries. Those steps remain #89 and #90.

## Privacy boundary

The manifest contains no names, learner data, observations, timestamps, machine details, accounts or remote locations. Files remain local and explicitly supplied.

## Verification

Tests cover closed fields, path safety, digest syntax, ordering, duplicates and unsupported versions. Merge requires green Actions, a complete finding log and two clean final-head reviews.
