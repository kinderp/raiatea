# First runnable pilot finding log

Issue: #60  
Pull request: #61

## Reviewed implementation

Initial review targeted head `fc48feafe49333f797aa06d7a0c64962fc3b0331`. Concurrent implementation commits through `a959f88a1f6343ae7648c344af4c989eeddd96f5` added the initial browser harness, workflow build, evaluator README, and final HTML validation. Final Actions and two clean reviews must target one unchanged head after all findings below are resolved.

## Findings

### F1 — major — resolved — final installation could replace a concurrent destination

The initial builder checked `output.exists()` before staging, then called `os.replace(staging, output)`. A directory created after the check could be silently replaced when platform rename semantics allowed it; a dangling symlink was also not covered by `Path.exists()`.

Resolution: the builder treats every lexically existing destination as occupied, reserves the final directory with atomic no-replace creation, installs only validated regular files using no-overwrite hard links, revalidates the installed directory, and removes only files created by the current build on failure. Existing or concurrently created destination bytes are preserved.

### F2 — major — resolved — the pilot route was pedagogically inverted

The initial route started with query/key/value and continued to self-attention. Canonical module context states that query/key/value follows an earlier orientation in which the learner has already located self-attention in the model.

Resolution: the route is now self-attention orientation followed by query/key/value. Launcher copy, manifest order, previous/next links, unit tests, browser tests, evaluator README, and normative documentation use the same order.

### F3 — major — resolved — route metadata duplicated and contradicted canonical identity

The initial route hardcoded `self-attention` while the canonical module ID is `self-attention-orientation`; titles were also duplicated independently from module JSON.

Resolution: the route registry contains only canonical source paths and output filenames. ID, opaque revision, and title are derived from loaded validated modules and included in the closed manifest. Duplicate canonical identities and duplicate outputs fail closed.

### F4 — major — resolved — required failure and determinism rows were missing

The initial tests covered successful output, relative links, privacy exclusions, and a destination that existed before the build, but not invalid source cleanup, a destination race, deterministic bytes, or CLI refusal.

Resolution: regressions now cover byte-deterministic independent builds, invalid module cleanup with no staging residue, pre-existing and concurrently created destination preservation, and CLI success/refusal.

### F5 — major — resolved — browser acceptance did not initially exercise the pilot launcher

The pre-pilot Playwright server built only the standalone self-attention artifact. Concurrent work added a pilot smoke test and changed the server to build the pilot, but the assertions followed the original inverted/noncanonical route.

Resolution: Playwright builds the complete pilot into `.browser-artifacts`, preserving the existing `/self-attention.html` interaction suite. The smoke test opens `index.html`, enters the canonical self-attention module, navigates to query/key/value, returns to the index, and asserts every request remains on the local test origin.

### F6 — minor — resolved — evaluator and architecture entry points were incomplete or inconsistent

The initial contract described build/serve commands while the dedicated evaluator README and documentation index were added later with the original inverted route.

Resolution: `PILOT.md` is the concise evaluator-facing README with exact build, serve, open, stop, and click-through instructions; the normative pilot contract and architecture documentation index reference the same canonical order and boundaries.

### F7 — minor — resolved — final injected navigation was not initially part of HTML validation

The first builder validated renderer output before injecting the pilot navigation, so the exact packaged document was not the validated document.

Resolution: final HTML validation runs after navigation injection and before staging output is installed.

## Open findings

None. GitHub Actions and two consecutive clean review rounds are required on one unchanged final head before merge.
