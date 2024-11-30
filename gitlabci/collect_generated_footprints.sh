#!/bin/bash
# Meant for usage in CI only:
# Move generated footprints from scripts/ to generated_footprints/
set -e

SRC_ROOT=scripts/
DEST_ROOT=generated_footprints/

mkdir "$DEST_ROOT"

shopt -s globstar nullglob
for src_fp_path in "$SRC_ROOT"**/*.kicad_mod; do
  relative_fp_path="${src_fp_path#$SRC_ROOT}"
  dest_fp_parent_path="$(dirname "$DEST_ROOT/$relative_fp_path")"
  mkdir -p "$dest_fp_parent_path"
  mv "$src_fp_path" -t "$dest_fp_parent_path"
done

# Hack: For any directories that contain .kicad_mod files but don't have the
# .pretty suffix, we rename them so they do (needed for html_diff.py to work
# properly)
# (TODO: This should probably be solved differently later on, e.g. by teaching
# subsequent processes to treat these dirs no different from ones with .pretty)
for dir_path in "$DEST_ROOT"**/; do
  fps=( "$dir_path"/*.kicad_mod )
  if [[ -n "${fps[0]}" && ! "$dir_path" =~ \.pretty/$ ]]; then
    # Extra _renamed suffix added to avoid collisions, because at least one
    # directory (Fuse) exists in both .pretty and bare form
    renamed_dir_path="${dir_path%*/}_renamed.pretty"
    echo "Hack: Renaming $dir_path -> $renamed_dir_path"
    mv -T "$dir_path" "$renamed_dir_path"
  fi
done
