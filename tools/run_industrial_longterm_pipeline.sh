#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONDA_SH="/home/rui/miniconda3/etc/profile.d/conda.sh"
ENV_NAME="openvla"

if [ $# -lt 4 ]; then
  echo "Usage: $0 <rgb_path> <depth_path_or_NONE> <prompt> <session_id> [frame_index] [output_root]" >&2
  exit 1
fi

RGB_PATH="$1"
DEPTH_PATH="$2"
PROMPT="$3"
SESSION_ID="$4"
FRAME_INDEX="${5:-0}"
OUTPUT_ROOT="${6:-$REPO_ROOT/outputs/$SESSION_ID}"

MANIFEST_DIR="$OUTPUT_ROOT"
OBS_DIR="$OUTPUT_ROOT/observation_output"
TRK_DIR="$OUTPUT_ROOT/tracklet_output"
MAP_DIR="$OUTPUT_ROOT/map_output"
SAM2_CKPT="$REPO_ROOT/checkpoints/sam2_hiera_small.pt"
SAM2_CFG="configs/sam2/sam2_hiera_s.yaml"

if [ ! -f "$CONDA_SH" ]; then
  echo "Missing conda init script: $CONDA_SH" >&2
  exit 1
fi
if [ ! -f "$RGB_PATH" ]; then
  echo "Missing RGB image: $RGB_PATH" >&2
  exit 1
fi
if [ "$DEPTH_PATH" != "NONE" ] && [ ! -f "$DEPTH_PATH" ]; then
  echo "Missing depth image: $DEPTH_PATH" >&2
  exit 1
fi
if [ ! -f "$SAM2_CKPT" ]; then
  echo "Missing SAM2 checkpoint: $SAM2_CKPT" >&2
  exit 1
fi

mkdir -p "$OUTPUT_ROOT"
source "$CONDA_SH"

DEPTH_ARGS=()
if [ "$DEPTH_PATH" != "NONE" ]; then
  DEPTH_ARGS+=(--depth "$DEPTH_PATH")
fi

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/run_repo_local_rgbd_ready_pipeline.py" \
  --rgb "$RGB_PATH" \
  "${DEPTH_ARGS[@]}" \
  --output-dir "$MANIFEST_DIR" \
  --prompt "$PROMPT" \
  --session-id "$SESSION_ID" \
  --frame-index "$FRAME_INDEX" \
  --sam2-checkpoint "$SAM2_CKPT" \
  --sam2-config "$SAM2_CFG" \
  --device cpu

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/build_object_observations.py" \
  --manifest "$MANIFEST_DIR/all_instances_manifest.json" \
  --output-dir "$OBS_DIR" \
  --session-id "$SESSION_ID" \
  --frame-index "$FRAME_INDEX"

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/build_session_tracklets.py" \
  --observations-index "$OBS_DIR/observations_index.json" \
  --output-dir "$TRK_DIR" \
  --session-id "$SESSION_ID"

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/update_long_term_object_map.py" \
  --tracklets-index "$TRK_DIR/tracklets_index.json" \
  --output-dir "$MAP_DIR" \
  --session-id "$SESSION_ID"

cat <<EOF
DONE
session: $SESSION_ID
manifest: $OUTPUT_ROOT/frontend_output/all_instances_manifest.json
observations: $OBS_DIR/observations_index.json
tracklets: $TRK_DIR/tracklets_index.json
map_objects: $MAP_DIR/map_objects.json
map_revisions: $MAP_DIR/map_revisions.json
EOF
