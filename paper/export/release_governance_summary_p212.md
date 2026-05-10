# P212 Release Governance Summary

**Release readiness:** `BLOCKED_STALE_ARTIFACTS`
**Current commit:** `6f8e260710fc` - exp: add P211 cross-phase evidence index
**P195 gate:** `BLOCKED`
**P210 readiness:** `READY_EMPTY`

## Governance Checks

- P211 artifact hash comparison: `PASS` (0 mismatches / 22 artifacts)
- Relevant dirty tracked/untracked status: `FAIL`
- P195 remains blocked with blank labels: `PASS`
- P209 safety status: `PASS` (6/6 cases)
- P210 quality-only readiness: `PASS`
- Label/proxy leakage scan: `PASS`
- P212 output schema scan: `PASS`

## Dirty Worktree Scope

- Relevant tracked dirty paths: 2
- Relevant untracked dirty paths: 0
- Protected untracked paths ignored for readiness blocking: 202
  - ` M` `paper/evidence/raw_evidence_diverse_packet_p206.json`
  - ` M` `paper/evidence/raw_evidence_diverse_packet_triage_p206.json`

## Artifact Drift

- All P206-P211 artifact file hashes match the P211 index.

## Claim Boundary

P212 is release governance for no-label evidence only. It does not create or infer human admission or same-object labels, does not train models, does not modify real notes or raw data, and does not support admission-control claims.

## Recommendation

P213 should either restore/regenerate and commit the relevant dirty P206-P211 evidence artifacts before paper export, or explicitly archive this blocked governance summary as evidence that the current worktree is not release-clean. Keep P195 blocked until independent human admission and same-object labels exist.
