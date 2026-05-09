#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/rui/slam/data/TorWIC_SLAM_Dataset}"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
STAGE_DIR="${STAGE_DIR:-/home/rui/slam/data/.gdown_stage}"
PROXY_PROBE_URL="${PROXY_PROBE_URL:-https://www.google.com/generate_204}"

select_download_proxy() {
  if [[ -n "${TORWIC_DOWNLOAD_PROXY:-}" ]]; then
    echo "$TORWIC_DOWNLOAD_PROXY"
    return 0
  fi
  if [[ -n "${DOWNLOAD_PROXY:-}" ]]; then
    echo "$DOWNLOAD_PROXY"
    return 0
  fi

  local proxy
  for proxy in \
    "http://127.0.0.1:17898" \
    "http://127.0.0.1:17899" \
    "http://127.0.0.1:7897"; do
    if timeout 20s curl -x "$proxy" -fsS --max-time 15 -o /dev/null "$PROXY_PROBE_URL"; then
      echo "$proxy"
      return 0
    fi
  done
  return 1
}

DOWNLOAD_PROXY="$(select_download_proxy)"
export DOWNLOAD_PROXY
export HTTP_PROXY="${HTTP_PROXY:-$DOWNLOAD_PROXY}"
export HTTPS_PROXY="${HTTPS_PROXY:-$DOWNLOAD_PROXY}"
export ALL_PROXY="${ALL_PROXY:-$DOWNLOAD_PROXY}"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,::1}"
export http_proxy="${http_proxy:-$HTTP_PROXY}"
export https_proxy="${https_proxy:-$HTTPS_PROXY}"
export all_proxy="${all_proxy:-$ALL_PROXY}"
export no_proxy="${no_proxy:-$NO_PROXY}"

echo "USING download proxy: $DOWNLOAD_PROXY"

mkdir -p "$ROOT/Jun. 15, 2022" "$ROOT/Jun. 23, 2022" "$ROOT/Oct. 12, 2022" "$STAGE_DIR"

validate_zip() {
  local zip_path="$1"
  unzip -tq "$zip_path" >/dev/null
}

cleanup_target_state() {
  local target="$1"
  shopt -s nullglob
  local target_parts=("${target}"*.part)
  shopt -u nullglob
  for part in "${target_parts[@]}"; do
    echo "REMOVE stale target partial: $part"
    rm -f "$part"
  done
}

download() {
  local file_id="$1"
  local target="$2"
  local stage_zip="$STAGE_DIR/${file_id}.zip"
  mkdir -p "$(dirname "$target")"

  cleanup_target_state "$target"

  if [[ -s "$target" ]]; then
    if validate_zip "$target"; then
      echo "SKIP existing valid zip: $target"
    else
      local corrupt_target="${target}.corrupt-$(date +%Y%m%d-%H%M%S)"
      echo "CORRUPT existing zip: $target -> $corrupt_target"
      mv "$target" "$corrupt_target"
    fi
  fi

  if [[ ! -s "$target" ]]; then
    if [[ -s "$stage_zip" ]] && ! validate_zip "$stage_zip"; then
      local corrupt_stage="${stage_zip}.corrupt-$(date +%Y%m%d-%H%M%S)"
      echo "CORRUPT staging zip: $stage_zip -> $corrupt_stage"
      mv "$stage_zip" "$corrupt_stage"
    fi

    echo "DOWNLOAD $target via staging $stage_zip"
    "$PYTHON_BIN" -m gdown --proxy "$DOWNLOAD_PROXY" --continue -O "$stage_zip" "$file_id"

    if ! validate_zip "$stage_zip"; then
      local corrupt_stage="${stage_zip}.corrupt-$(date +%Y%m%d-%H%M%S)"
      echo "ERROR invalid staging zip after download: $stage_zip -> $corrupt_stage" >&2
      mv "$stage_zip" "$corrupt_stage"
      return 1
    fi

    mv "$stage_zip" "$target"
  fi

  if ! validate_zip "$target"; then
    local corrupt_target="${target}.corrupt-$(date +%Y%m%d-%H%M%S)"
    echo "ERROR invalid target zip after staging move: $target -> $corrupt_target" >&2
    mv "$target" "$corrupt_target"
    return 1
  fi

  local out_dir="${target%.zip}"
  if [[ -f "$out_dir/.extract_done" ]]; then
    echo "SKIP extracted: $out_dir"
  else
    rm -rf "$out_dir"
    mkdir -p "$out_dir"
    echo "EXTRACT $target -> $out_dir"
    unzip -o "$target" -d "$out_dir"
    echo ok > "$out_dir/.extract_done"
  fi
}

download "15-6AxGxLR7CbbiHlMwFk0GxG_x7XTgyN" "$ROOT/Jun. 15, 2022/Aisle_CCW_Run_1.zip"
download "1T-n-6Ou3SPM3zT863ArohAUa768ufr0c" "$ROOT/Jun. 23, 2022/Aisle_CCW_Run_1.zip"
download "1hplx0_5tDKz4zF6iRgTfwuQNIund0URn" "$ROOT/Oct. 12, 2022/Aisle_CCW.zip"

echo "DONE benchmark batch1 download/extract" 
