#!/usr/bin/env bash
# Meant to be run in CI only.
# Adapted from kicad-library-utils/tools/gitlabci/visual_diff.sh
# => TODO: Refactor to extract common functionality?
set -ex

source "$CI_BUILDS_DIR/kicad-library-utils/tools/gitlabci/common.sh"

BASE_DIR=base_footprints/  # baseline/reference
TARGET_DIR=generated_footprints/  # after changes

# Required due to bug (?) or thing I don't understand in html_diff.py
# (TODO: Try to fix there?)
unset CI_MERGE_REQUEST_ID

echo "Comparing $BASE_DIR to $TARGET_DIR"
for target_path in $(git diff --no-index --name-only "$BASE_DIR" "$TARGET_DIR" | xargs dirname | sort | uniq | grep '\.pretty$'); do
    base_path="$BASE_DIR/${target_path#$TARGET_DIR}"
    echo "Diffing $base_path against $target_path"
    python3 "$CI_BUILDS_DIR/kicad-library-utils/html-diff/src/html_diff.py" -j0 -v "$base_path" "$target_path"
done

# Hack to get around render_index_html only looking at top-level directories:
# Move everything to top-level replacing / with __ to avoid name collisions:
# (=> TODO: Implement nested dirs in render_index_html to get rid of this)
shopt -s globstar nullglob
for diff_src in {,**/}*.diff; do
    diff_dest="${diff_src//"/"/__}"
    mv "$diff_src" "$diff_dest"
done

# If there is at least one *.diff, create the index.html
# The link path must be relative to ../ because index.html will be placed in the "index.html.diffs" directory
python3 "$CI_BUILDS_DIR/kicad-library-utils/html-diff/src/render_index_html.py" . -p "../"
# Move index.html to index.html.diff, so it will get moved by the (unmodified) gitlab-ci.yml
# to the [diffs] directory. We can't create this directory here, because then [mkdir diff]
# in .gitlab-ci.yml will fail
mkdir -p index.html.diff
mv index.html index.html.diff/index.html
