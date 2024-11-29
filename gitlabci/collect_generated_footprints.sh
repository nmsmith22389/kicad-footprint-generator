#!/bin/bash
# Meant for usage in CI only:
# Move generated footprints from scripts/ to generated_footprints/
set -e

SRC_ROOT=scripts/
DEST_ROOT=generated_footprints/

mkdir "$DEST_ROOT"

shopt -s globstar nullglob
for src_dir_path in "$SRC_ROOT"{**/,}*.pretty/; do
  relative_dir_path="${src_dir_path#$SRC_ROOT}"
  dest_dir_parent_path="$(dirname "$DEST_ROOT/$relative_dir_path")"
  mkdir -p "$dest_dir_parent_path"
  mv "$src_dir_path" -t "$dest_dir_parent_path"
done
