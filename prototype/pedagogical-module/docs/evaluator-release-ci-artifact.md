# Evaluator release CI artifact publication and validation contract

Status: initial implementation contract for issue #73 under parent #69.

## Goal

Have GitHub Actions build, upload, download, independently verify and smoke-test the exact reproducible evaluator archive produced from canonical sources, without publishing a GitHub Release or adding any runtime cloud dependency.

## Artifact identity

The CI artifact uses one fixed bounded test version derived from repository content, not from user input or secrets. The uploaded artifact contains exactly one `raiatea-evaluator-<version>.tar` file. Artifact naming is deterministic and does not contain branch names, actor names, timestamps, run IDs, credentials or learner data.

## Producer job

A dedicated least-privilege job:

1. checks out the repository;
2. sets up Python;
3. runs the existing archive builder for the fixed CI version;
4. runs the independent verifier locally;
5. records archive SHA-256 and expected filename;
6. uploads only the validated tar file with bounded retention.

The producer must fail before upload when build or verification fails.

## Consumer job

A separate job depending only on the uploaded artifact:

1. downloads the artifact into a new directory;
2. rejects unexpected file count or names;
3. invokes the independent archive verifier into another new directory;
4. validates `release-manifest.json`, `RELEASE-NOTES.md` and `SHA256SUMS` through the verifier;
5. serves the extracted `pilot/` directory on loopback;
6. performs a bounded smoke test of `index.html`, both module files and the pilot manifest;
7. stops the local server and cleans temporary state.

The consumer must not rely on producer workspace files.

## Trigger, permissions and retention

The job runs only for non-draft pull requests that affect the pedagogical-module release path and for explicit manual dispatch. Repository permissions remain read-only. Artifact retention is short and explicit. No secrets, tokens beyond the default read-only checkout token, deployment credentials or external services are required.

## Security and privacy

The artifact contains only the static evaluator release. It must not include `.git`, source checkout, caches, test reports, environment files, credentials, personal data, learner progress or browser state. Uploading the artifact to GitHub Actions storage is a CI transport step, not public hosting or a runtime dependency.

## Verification

Tests and workflow review must prove:

- bounded triggers and explicit permissions;
- producer/consumer separation;
- exact artifact name and one-file payload;
- short retention;
- independent download and verification;
- extracted pilot smoke test on loopback;
- failure diagnostics and no secret usage;
- all existing unit and browser regressions remain green.

## Boundary

No GitHub Release, public URL, package registry, signing, installer, deployment, cloud runtime, analytics, learner identity or auto-update behavior.
