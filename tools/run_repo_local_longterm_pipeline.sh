#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONDA_SH="/home/rui/miniconda3/etc/profile.d/conda.sh"
ENV_NAME="openvla"

RGB_PATH="${1:-$REPO_ROOT/notebooks/videos/bedroom/00000.jpg}"
PROMPT="${2:-bed.}"
RUN_NAME="${3:-repo_local_demo_run}"
OUTPUT_ROOT="$REPO_ROOT/outputs/$RUN_NAME"
MANIFEST_DIR="$OUTPUT_ROOT/frontend_output"
OBS_DIR="$OUTPUT_ROOT/observation_output"
TRK_DIR="$OUTPUT_ROOT/tracklet_output"
MAP_DIR="$OUTPUT_ROOT/map_output"
SAM2_CKPT="$REPO_ROOT/checkpoints/sam2_hiera_small.pt"
SAM2_CFG="configs/sam2/sam2_hiera_s.yaml"
SLAM_DEVICE="${SLAM_DEVICE:-auto}"

if [ ! -f "$CONDA_SH" ]; then
  echo "Missing conda init script: $CONDA_SH" >&2
  exit 1
fi
if [ ! -f "$RGB_PATH" ]; then
  echo "Missing RGB image: $RGB_PATH" >&2
  exit 1
fi
if [ ! -f "$SAM2_CKPT" ]; then
  echo "Missing SAM2 checkpoint: $SAM2_CKPT" >&2
  exit 1
fi

mkdir -p "$OUTPUT_ROOT"
source "$CONDA_SH"

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/run_repo_local_grounded_sam2_image_to_manifest.py" \
  --rgb "$RGB_PATH" \
  --output-dir "$MANIFEST_DIR" \
  --prompt "$PROMPT" \
  --sam2-checkpoint "$SAM2_CKPT" \
  --sam2-config "$SAM2_CFG" \
  --device "$SLAM_DEVICE"

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/build_object_observations.py" \
  --manifest "$MANIFEST_DIR/all_instances_manifest.json" \
  --output-dir "$OBS_DIR" \
  --session-id "$RUN_NAME" \
  --frame-index 0

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/build_session_tracklets.py" \
  --observations-index "$OBS_DIR/observations_index.json" \
  --output-dir "$TRK_DIR" \
  --session-id "$RUN_NAME"

conda run -n "$ENV_NAME" python "$REPO_ROOT/tools/update_long_term_object_map.py" \
  --tracklets-index "$TRK_DIR/tracklets_index.json" \
  --output-dir "$MAP_DIR" \
  --session-id "$RUN_NAME"

cat <<EOF
DONE
manifest: $MANIFEST_DIR/all_instances_manifest.json
observations: $OBS_DIR/observations_index.json
tracklets: $TRK_DIR/tracklets_index.json
map_objects: $MAP_DIR/map_objects.json
map_revisions: $MAP_DIR/map_revisions.json
EOF
