# First runnable pilot finding log

Issue: #60  
Pull request: #61

## Reviewed implementation

The increment packages two existing canonical modules behind one local launcher without duplicating the module renderer or changing evidence contracts.

## Findings

### F1 — resolved — browser tests originally served only one standalone module

The previous Playwright configuration built and served only `self-attention.html`, so it could not test a launcher or cross-module route.

Resolution: browser setup now builds the complete pilot directory and serves it from `index.html`. Existing module URLs remain available inside the same directory.

### F2 — resolved — CI did not prove the packaged pilot existed

Standalone module builds were verified, but the launcher, closed manifest, and two-module output were not part of CI.

Resolution: `validate-and-build` now builds `/tmp/raiatea-pilot` and verifies the launcher, both module documents, manifest, and launcher links.

### F3 — resolved — a non-developer had no direct launch walkthrough

The prototype README documented individual module builds but not a complete evaluator journey.

Resolution: `PILOT.md` provides build, serve, stop, URL, expected files, and a ten-step evaluator checklist using only Python and a browser.

### F4 — resolved — launcher navigation lacked browser-level coverage

Unit tests proved generated strings and relative links, but not that a browser could traverse the route.

Resolution: `browser-tests/pilot.spec.js` opens the launcher, enters the first module, follows the next link, returns to the previous module and index, and refuses console errors.

### F5 — infrastructure observation — Actions run 656 did not start job steps

The initial run and its failed-job rerun both reported `failure` for both jobs while GitHub returned no job steps or downloadable logs. This is recorded as an infrastructure observation rather than a code finding because no repository command was executed according to the available job metadata.

Resolution boundary: the next commit triggers a fresh workflow run. Product changes will be made only for reproducible test output, not to guess at runner-start failures.

## Open findings

None in the reviewed product diff. Green Actions and two consecutive clean reviews on one unchanged final head remain required before merge.
