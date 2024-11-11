#! /usr/bin/env bash
set -e  # abort whole script and return non-zero exit status on first error

# Recursively search for generate.sh scripts and execute them
# -mindepth 2 is required to avoid running this script itself
# -maxdepth 2 is required:
#   e.g. Connectors/generate.sh will execute Connectors/Samtec/generate.sh itself,
#   so we shouldn't execute Connectors/Samtec/generate.sh again
# We exit with code 255 from the inner shells so that the entire xargs
# invocation fails immediately instead of running the remaining generate.sh
# scripts when one of them fails.
find . -mindepth 2 -type f -name generate.sh -printf '%h\0' \
  | xargs -0 -r -n 1 bash -c 'cd $0 && ./generate.sh || exit 255'
# Packages itself has no generate.sh script, but subdirs have one
find Packages -mindepth 2 -type f -name generate.sh -printf '%h\0' \
  | xargs -0 -r -n 1 bash -c 'cd $0 && ./generate.sh || exit 255'
