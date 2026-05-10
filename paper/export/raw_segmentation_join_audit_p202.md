# P202 Raw Segmentation Join Audit

**Status:** JOIN_AUDIT_COMPLETE_P195_STILL_BLOCKED

## Boundary

P202 audits evidence-based joins only. It does not create labels, does not use P193/P197 weak admission fields or model predictions as targets, and does not train admission-control or semantic-stability models.

## Join Metrics

- Total rows attempted: 572
- Exact joins: 572
- Partial joins: 0
- Unmatched: 0
- Overall rates: {'total': 572, 'exact': 572, 'partial': 0, 'unmatched': 0, 'exact_rate': 1.0, 'partial_rate': 0.0, 'unmatched_rate': 0.0}

## Per-Source Join Rates

- p193: {'total': 110, 'exact': 110, 'partial': 0, 'unmatched': 0, 'exact_rate': 1.0, 'partial_rate': 0.0, 'unmatched_rate': 0.0}
- p197_boundary: {'total': 32, 'exact': 32, 'partial': 0, 'unmatched': 0, 'exact_rate': 1.0, 'partial_rate': 0.0, 'unmatched_rate': 0.0}
- p197_pair: {'total': 320, 'exact': 320, 'partial': 0, 'unmatched': 0, 'exact_rate': 1.0, 'partial_rate': 0.0, 'unmatched_rate': 0.0}
- p199: {'total': 110, 'exact': 110, 'partial': 0, 'unmatched': 0, 'exact_rate': 1.0, 'partial_rate': 0.0, 'unmatched_rate': 0.0}

## Evidence Path Existence

- raw_evidence_paths_existing: 3432
- raw_evidence_paths_total: 3432
- rows_with_observation_index: 572
- rows_with_observation_found: 572
- rows_with_manifest: 572
- rows_with_manifest_instance: 572

## Additional Raw Category Blockers

- cart_pallet_jack: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=73, ambiguous=73, absent=0)
- ceiling: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=59, ambiguous=59, absent=0)
- driveable_ground: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=79, ambiguous=79, absent=0)
- ego_vehicle: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=63, ambiguous=63, absent=0)
- goods_material: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=79, ambiguous=79, absent=0)
- misc_dynamic_feature: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=72, ambiguous=72, absent=0)
- misc_non_static_feature: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=79, ambiguous=79, absent=0)
- person: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=51, ambiguous=51, absent=0)
- text_region: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=32, ambiguous=32, absent=0)
- wall_fence_pillar: unmatched - annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata (frames=79, ambiguous=79, absent=0)

## Label Gate

- P195 status: BLOCKED
- Human label columns remain blank; no human labels, admission labels, or same-object labels were created.

## Outputs

- JSON: `paper/evidence/raw_segmentation_join_audit_p202.json`
- CSV: `paper/evidence/raw_segmentation_join_audit_p202.csv`

**P203 recommendation:** Use the P202 evidence map to build a no-label raw-frame evidence join helper, but do not materialize expanded auxiliary training rows until object-level raw category masks can be linked to observation_id/tracklet/physical_key without ambiguous AnnotatedSemanticSet route guesses. P195 remains blocked until independent human admission and same-object labels exist.
