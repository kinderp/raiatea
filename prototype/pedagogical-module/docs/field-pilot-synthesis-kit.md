# Field-pilot synthesis kit

Issue: #91  
Parent: #87

## Decision

Package the completed local batch-manifest, contextual intake and deterministic aggregate workflow into one reproducible, independently verified field-pilot archive. The final kit extends the existing desktop-ready evaluator archive without changing the learner pilot, learner-evidence contracts, release manifest or launcher behavior.

## Distributed composition

The archive contains the complete verified field-pilot release plus:

- `evaluator_session_record.py`;
- `evaluator_session_batch_manifest.py`;
- `evaluator_session_batch_intake.py`;
- `evaluator_session_aggregate.py`;
- version-pinned `SYNTHESIS-KIT.md` instructions;
- one deterministic two-record example under `synthesis-example/`;
- the example batch manifest, explicit digest-scoped theme assignments and canonical expected aggregate.

The earlier hyphenated evaluator-session CLI and its fixture remain present for the single-record create/validate/export/delete lifecycle. The underscored modules are copied as an importable and directly executable local synthesis toolchain.

## Build and verification sequence

1. Build the already accepted field-pilot archive for the requested opaque release version.
2. Independently verify and extract that archive into a private temporary workspace.
3. Remove only the obsolete checksum inventory from the verified copy.
4. Copy the four regular tool files and generate the deterministic example and guide.
5. Recompute `SHA256SUMS` over every distributed regular file.
6. Write a normalized POSIX USTAR archive with deterministic ordering and metadata.
7. Independently verify the final archive, release manifest, checksum coverage and file digests.
8. Install the completed archive with no-replace hard-link publication and clean the owned workspace.

The builder refuses an existing output, unsafe source tool, conflicting destination or failed independent verification. Two builds from the same sources and release version must be byte-identical.

## Example workflow

From the extracted release root, the evaluator can run:

```text
python evaluator_session_batch_manifest.py synthesis-example/batch-manifest.json
python evaluator_session_batch_intake.py synthesis-example/batch-manifest.json --root synthesis-example
python evaluator_session_aggregate.py synthesis-example/batch-manifest.json --root synthesis-example --themes synthesis-example/themes.json --output /new/path/aggregate.json
```

The generated output must equal `synthesis-example/aggregate.json`. Output creation remains explicit and no-replace. The example records contain no identity, timestamps, machine details, learner evidence or free-text observations.

## Cross-platform acceptance

Linux CI builds the final archive, verifies it in a clean destination, executes all three synthesis commands from the extracted kit and compares the produced aggregate byte-for-byte with the canonical example. The normal unit suite also checks archive reproducibility, complete checksum coverage for synthesis files, example reconstruction, version-pinned instructions, no-replace behavior and absence of network-client imports in distributed tools.

Windows CI builds and independently verifies the same final kit, executes the example through Python on PowerShell, compares SHA-256 of generated and expected aggregates, launches and stops the unchanged pilot on loopback, exercises the single-record lifecycle and retains the existing failure-diagnostic acceptance.

macOS remains documented as POSIX/Python parity with the Linux toolchain. No macOS-specific runtime behavior is claimed beyond the already accepted portable POSIX helper contract until a bounded hosted macOS job is added.

## Privacy and operational boundary

The kit reads only the manifest, root, records and optional theme-assignment file explicitly supplied by the evaluator. It does not scan unrelated files, infer themes, copy observations into the aggregate, import learner evidence, create accounts, contact remote services, upload results, start background workers, install services, create databases or retain state after evaluator-directed cleanup.

Theme labels remain restricted to the closed vocabulary defined by the aggregate contract and are assigned only to exact input SHA-256 digests. The aggregate exposes counts and sorted input digest provenance only.

## Cleanup

The evaluator explicitly deletes generated aggregates, local manifests, theme assignments, copied evaluator records, the extracted release and the downloaded archive when no longer needed. The kit creates no machine-wide state, registry entry, scheduled task, service, auto-update channel or cloud copy.

## Deferred work

Signing, authenticated publisher provenance, remote collection, collaborative review, analytics, LMS integration, account-backed storage, automatic submission and learner-evidence aggregation remain outside this increment.
