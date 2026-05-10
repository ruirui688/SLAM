# P201 No-Label Semantic Category Inventory

**Status:** INVENTORY_COMPLETE_EXPANSION_BLOCKED_BY_MISSING_SAFE_JOIN

## Boundary

P201 inventories no-human-label semantic assets only. It does not create human labels, does not use P193/P197 weak admission targets/model predictions as target labels, and does not claim admission control.

## Inventory Counts

- Annotated raw label JSON files: 237
- Annotated semantic categories with positive pixels: 15
- Candidate raw map-object/movable-clutter categories: 10
- Existing all-instances manifests: 94
- Existing observation indexes: 93
- Extracted segmentation directories: 88
- Extracted segmentation PNGs: 144620

## Candidate Categories

- Static-like object candidates: `['fixed_machinery', 'misc_static_feature', 'rack_shelf']`
- Static context only: `['ceiling', 'driveable_ground', 'wall_fence_pillar']`
- Dynamic/non-static object or clutter candidates: `['cart_pallet_jack', 'fork_truck', 'goods_material', 'misc_dynamic_feature', 'misc_non_static_feature', 'person', 'pylon_cone']`
- Context-only/excluded categories: `['ceiling', 'driveable_ground', 'ego_vehicle', 'text_region', 'unlabeled', 'wall_fence_pillar']`

## Feasibility Answer

- Can current local data break the P199/P200 category=target degeneracy? **NO**
- Additional raw candidate categories beyond P199: `['cart_pallet_jack', 'goods_material', 'misc_dynamic_feature', 'misc_non_static_feature', 'person']`
- Additional safely joined manifest categories beyond P199: `[]`
- Target policy if a safe join is added later: category-derived static_like versus dynamic_or_non_static_like auxiliary target only; context-only categories excluded from object admission rows; no admit/reject labels.

## Missing Joins

- Existing object observations/front-end manifests are still prompt-limited mostly to forklift, rack, work table, and barrier/yellow barrier.
- The richer AnnotatedSemanticSet_Finetuning.zip categories have frame/image IDs and mask pixels, but no local join to observation_id, tracklet_id, physical_key, or cross-session object clusters.
- Extracted sequence segmentation_color/greyscale directories do not include per-frame raw_labels_2d.json metadata in the extracted folders, and raw category masks are not connected to current observation manifests.
- Using P193 target_admit/current_weak_label/selection_v5/model predictions would create prohibited target leakage, so those fields are not used.

## Label Audit

- P195 status remains: `BLOCKED`
- No `human_admit_label` or `human_same_object_label` values were created or filled.

## Outputs

- JSON: `paper/evidence/semantic_category_inventory_p201.json`
- CSV: `paper/evidence/semantic_category_inventory_p201.csv`

**P202 recommendation:** Build a safe raw-segmentation-to-observation join first: map raw sequence/date/frame/camera/category masks to observation_id/tracklet/physical_key and then rerun a no-label auxiliary dataset build. Keep P195 blocked until independent human labels exist.
