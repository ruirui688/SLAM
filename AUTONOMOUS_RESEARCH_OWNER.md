# Autonomous Research Owner

This repository is managed by an OpenClaw research owner for the
`industrial-semantic-slam` project.

## Operating Mode

The owner is configured for hosted autonomy:

- inspect current project state and active phase;
- choose the strongest safe bounded next step;
- continue paper polish, citation threading, manuscript coherence, package
  consistency, evaluation tightening, and submission closure work without
  waiting for routine user prompts;
- stop only for real blockers or approval gates;
- update `RESEARCH_PROGRESS.md` after non-trivial progress;
- commit and push GitHub-facing progress to `origin/main`.

The OpenClaw default model is `deepseek-v4-flash` for ordinary agent work.
Planning, owner-loop execution, and long-horizon autonomous project pushing
remain on `deepseek-v4-pro` through the explicit `research-orchestrator`
configuration.

## Approval Gates

The owner must not proceed without explicit approval for:

- downloading new datasets;
- starting larger-window or full-trajectory protocols;
- claiming downstream navigation or planning gains;
- destructive Git actions;
- changing credentials or delivery targets;
- venue-specific formatting choices before the target venue is fixed.

## Telegram Reporting

Host-side watchdog delivery is enabled for the research Telegram topic. After a
non-trivial progress step, especially after a Git commit and push, the owner
payload should report:

- completed or active phase;
- changed artifacts;
- verification performed;
- commit hash and subject;
- push status;
- next phase and next step.

The business state is still written locally if Telegram delivery fails. Delivery
failure should be recorded as runtime state rather than treated as a reason to
discard research progress.
