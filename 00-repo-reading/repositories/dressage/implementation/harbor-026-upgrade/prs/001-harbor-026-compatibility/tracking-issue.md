## Motivation

I want to enable Dressage jobs to use a wider range of sandbox backends through Harbor (such as Kubernetes-based `agent-sandbox`). I also want to explore whether Harbor’s `JobPlan` can be paired with sandbox pre-warming or direct claiming (e.g., `SandboxClaim` / lookahead provisioning) to overlap sandbox startup with training and reduce the time GPUs spend waiting for samples.

This migration focuses on preserving the existing CLI rollout and Slime training workflows on Harbor `0.26.0`. That includes checking that each planned trial maps to the intended task, agent, and attempt. After a retry, the recorded trajectory, verifier reward, and sample returned to Slime must all belong to the attempt Harbor selected. Scheduling changes, pre-warming integration, and GPU idle-time benchmarks will be tracked separately.

## Proposed Plan & Task List

### Phase 1 — Audit existing Harbor usage and configuration

- [x] Map the existing integration at Dressage commit `3e3142f`. I identified 61 distinct Harbor usages across configuration, job planning, agent routing, trial callbacks, sandbox execution, log collection, and result handling.
- [ ] Compare each usage on `0.18.0` and `0.26.0`, including calls from Harbor back into Dressage. Check signatures, defaults, configuration precedence, and the result the downstream caller actually receives. Record whether each difference requires a Dressage code change, a user configuration change, or further runtime verification.

I’ll share the compatibility matrix in a follow-up comment on this issue, with the affected usages, proposed fixes, and evidence for each finding.

### Phase 2 — Fix confirmed regressions and update the dependency pin

- [ ] Land the bwrap preflight, log collection, and separate-verifier fixes with their regression tests. Work is underway in my fork. A local Oracle trial on `0.26.0` has produced an agent log and returned a verifier reward of `1`.
- [ ] Align the dependency pin, runtime version checks, and installation instructions. Verify that the effective agent configuration routes model requests through the Dressage Gateway using the credential for that trial.

I’ll propose separate PRs where a change can be merged and tested independently. Fixes that require the `0.26.0` API will be reviewed together with the version switch.

### Phase 3 — Validate the migration through the existing entry points

- [ ] Run a CLI rollout on the agreed sandbox backends. Check that a real agent request reaches the expected Gateway, that logs and rewards reach the host, and that cancellation releases the trial route.
- [ ] Exercise a retry through the Slime training entry point. Verify that the final Harbor result, the Dressage manifest, and the returned training samples all identify the same attempt.

## Questions for Maintainers

1. Can Dressage move its exact Harbor pin directly from `0.18.0` to `0.26.0`, or are there deployments that still need `0.18.0` compatibility?
2. Which sandbox backends should pass an end-to-end rollout before the pin changes? I’ve started with local bwrap. Should E2B also be part of the initial acceptance criteria?
