#! /usr/bin/env bash

# Recursively search for generate.sh scripts and execute them
# -mindepth 2 is required to avoid running this script itself
# -maxdepth 2 is required:
#   e.g. Connectors/generate.sh will execute Connectors/Samtec/generate.sh itself,
#   so we shouldn't execute Connectors/Samtec/generate.sh again
find . -mindepth 2 -type f -name generate.sh -execdir ./generate.sh \;
# Packages itself has no generate.sh script, but subdirs have one
find Packages -mindepth 2 -type f -name generate.sh -execdir ./generate.sh \;
