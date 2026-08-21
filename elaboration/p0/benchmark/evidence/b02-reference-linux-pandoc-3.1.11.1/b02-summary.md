# B-02 EPUB reference-environment baseline

> Benchmark evidence only. No Provider is selected and no first slice is promoted.
>
> Evidence source code: `1fabcd1e435860a20035f2751655ab92ff95a8b1`.
>
> The fixture/gold redistribution gate remains open in issue #131.

## Environment

- OS: `Linux 6.18.35` `x86_64`
- Python: `3.13.5`
- CPU: `AMD EPYC 9V74 80-Core Processor` (5 logical CPUs exposed to the run)
- Memory observed: `6219544 kB`
- GPU: not instrumented
- Pandoc measured: `3.1.11.1`
- Pandoc executable: `/usr/bin/pandoc`
- Pandoc executable SHA-256: `0336f5db0c5db91d3b7e29e3adc226bebd76d074bf28a907e50fc148bded3e8b`
- Pandoc E-02 surveyed: `3.10.2`
- Version match: `False`
- Pandoc options: `--sandbox --from=epub --to=json`
- Network traffic: not instrumented
- Timing values from the source run are single-run observations only and are not promoted as performance claims in this compact evidence record.

## B02-EPUB-001 — spine/text/anchors

- direct stdlib: text `4/4`, coordinate full-exact `4/4`, traceable `4/4`, reading-order edges `3/3`.
- Pandoc: text `4/4`, coordinate full-exact `0/4`, traceable `2/4`, reading-order edges `3/3`.
- Interpretation: on this minimal fixture Pandoc preserves text, spine order and heading anchors, but the measured mapping does not preserve authored paragraph fragment IDs. Resource paths are traceable by suffix (`ch1.xhtml`/`ch2.xhtml`) rather than exact `OEBPS/...` paths.

## B02-EPUB-002 — navigation/links

- direct stdlib: navigation exact `2/2`, semantic link `1/1`, authored target exact `1/1`, source paragraph fragment preserved.
- Pandoc: navigation exact `0/2`, semantic link `1/1`, authored target exact `0/1`, source paragraph fragment not preserved.
- The measured Pandoc AST mapping exposes the semantic cross-resource link but normalizes its target to `#ch2.xhtml#details` and does not expose a separate EPUB navigation tree.

## Negative fixtures

- `B02-EPUB-NEG-001` / direct: `degraded`, expected state satisfied. The direct parser detects script-capable content as data and emits an explicit warning without executing it.
- `B02-EPUB-NEG-001` / Pandoc: `success`, expected state satisfied through the allowed safe-success branch. `script-not-executed` remains **not measured** because the inert fixture has no observable execution probe; no file side effects were observed. `no-network-required` is only a fixture property, not proof about provider network traffic.
- `B02-EPUB-NEG-002` / direct: `rejected`, expected state satisfied; parent-traversal member is rejected before semantic parsing and no archive extraction API is used.
- `B02-EPUB-NEG-002` / Pandoc: `success`, therefore the expected `rejected-or-degraded-with-warning` state is **not satisfied**. No file side effects were observed inside the controlled temporary parent, so `no-path-escape` is only partial evidence; Pandoc internals and OS-level writes outside that parent are not instrumented, and `no-extractall` remains not measured.

This does **not** establish that Pandoc is unsafe. It establishes only that this measured route/version did not expose the expected reject/degrade state for the crafted traversal-member fixture and that the current harness cannot prove all internal security properties.

## Decision boundary

- No weighted/universal score is produced.
- Pandoc route selection blocker: measured Pandoc `3.1.11.1` differs from the E-02 surveyed `3.10.2`; rerun on an accepted current version before any route-selection decision.
- B-02 coverage is incomplete: images/captions/alt, footnotes/endnotes, tables/code/MathML, a broader realistic composite and malformed/missing-resource behavior remain open.
- Fixture/gold redistribution remains `not-established` pending #131; this evidence does not complete G-02.
- G-04 and G-05 remain open; this baseline only advances measured evidence.
- `provider_selected=false`; `first_slice_promoted=false`.
