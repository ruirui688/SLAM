# Paper Drafts

This directory contains Git-tracked manuscript drafts for direct repository
review.

| File | Language | Role |
|---|---|---|
| [`manuscript_en.md`](./manuscript_en.md) | English | Current paper-facing manuscript draft |
| [`manuscript_zh.md`](./manuscript_zh.md) | Chinese | Chinese companion draft for project progress review |
| [`figures/`](./figures/) | Images | Tracked paper figures copied from curated local outputs |
| [`evidence/`](./evidence/) | Tables | Git-tracked evidence digest regenerated from ignored experiment outputs |
| [`export/dynamic_mask_training_section_p222.md`](./export/dynamic_mask_training_section_p222.md) | English | P217-P220 dynamic-mask training section for manuscript insertion |

The source evidence artifacts referenced by these drafts are mostly generated
under `/home/rui/slam/outputs/` and intentionally ignored by Git. The tracked
drafts summarize the current evidence state without committing raw datasets,
videos, model checkpoints, point clouds, or large generated outputs.

Regenerate the repository-visible evidence digest from the project root:

```bash
make evidence-pack
```
