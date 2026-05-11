# Paper Drafts

This directory contains Git-tracked manuscript drafts for direct repository
review.

| File | Language | Role |
|---|---|---|
| [`manuscript_en.md`](./manuscript_en.md) | English | Current paper-facing manuscript draft |
| [`manuscript_zh.md`](./manuscript_zh.md) | Chinese | Chinese companion draft for project progress review |
| [`figures/`](./figures/) | Images | Tracked paper figures copied from curated local outputs |
| [`evidence/`](./evidence/) | Tables | Git-tracked evidence digest regenerated from ignored experiment outputs |
| [`export/dynamic_mask_training_section_p222.md`](./export/dynamic_mask_training_section_p222.md) | English | P217-P220 dynamic-mask training section used for manuscript insertion |
| [`export/paper_manuscript_sync_p224.md`](./export/paper_manuscript_sync_p224.md) | English | P224 audit of actual manuscript/T-RO sync status |

## Current Manuscript Status

As of P224, the P217-P220 dataset-mask-supervised dynamic/non-static front-end
route is present in the actual manuscript surfaces, not only in an export
appendix:

- `manuscript_en.md`: abstract, introduction, dynamic/non-static front-end,
  results table/prose, discussion, limitations, and evidence anchors.
- `tro_submission/abstract.tex`: T-RO abstract now names the dynamic-mask
  dataset, model metrics, held-out mask metrics, ORB proxy, and claim boundary.
- `tro_submission/main.tex`: method, results, discussion, limitations, and
  conclusion now include the P217-P220 route and explicitly separate it from
  learned persistent-map admission control.

The source evidence artifacts referenced by these drafts are mostly generated
under `/home/rui/slam/outputs/` and intentionally ignored by Git. The tracked
drafts summarize the current evidence state without committing raw datasets,
videos, model checkpoints, point clouds, or large generated outputs.

Regenerate the repository-visible evidence digest from the project root:

```bash
make evidence-pack
```
