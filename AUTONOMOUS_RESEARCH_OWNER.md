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

The user has authorized continued paper execution, but not open-ended token
spend. Every expensive owner turn must have a named phase, a concrete artifact
target, and a verification criterion before it starts. If the project only needs
a fresh heartbeat or status check, the host should return a cheap local
heartbeat and must not call the planning model.

Wake policy is intentionally narrow: the host watchdog is the only active
research wake driver. The timer checks every 15 minutes with a 45-minute stale
threshold, but an expensive owner turn is only started when progress is stale or
an interrupted turn needs recovery. Fresh active phases produce only a cheap
local heartbeat. Each real wake is bounded to one owner step by default and at
most one phase may be completed per wake. The OpenClaw research-owner cron is
disabled to avoid duplicate wakeups.

Timeouts are recoverable operational events. They are recorded in the OpenClaw
host logs and should not leave the systemd timer failed or inactive.

## Execution Rules

- One wake may execute only one bounded owner step.
- One wake may complete at most one phase.
- Parallel subagents are allowed only when their modules are explicit and all
  outputs feed the same active phase.
- A progress turn must produce or refresh a concrete artifact, draft section,
  audit, manifest/checklist entry, or GitHub-facing progress note.
- After every completed non-trivial phase, the owner must inspect the paper
  manuscript state and either update the relevant paper text/tables/appendix
  links or explicitly record why the phase is evidence-only and does not change
  the manuscript body yet.
- No new dataset downloads, larger-window/full-trajectory protocols, or
  downstream navigation/planning claims are allowed without explicit approval.
- After non-trivial progress, update `RESEARCH_PROGRESS.md`, commit and push
  safe GitHub-facing files, and send the Telegram progress payload.

Current primary purpose: execute `P120-thick-manuscript-draft`, which turns the
closed evidence package into a substantial first paper draft. The phase should
produce thick English and Chinese manuscripts with stronger related work,
problem formulation, method explanation, protocol narrative, results
interpretation, failure-case analysis, limitations, figures, and evidence
tables.

Current non-purpose: generic polishing, repeated citation checking without a new
gap, fresh-status model calls, new data acquisition, or new experiment protocol
launches.

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
