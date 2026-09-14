#!/bin/sh
# The 3D pane. Started by Harness with HARNESS_WORKSPACE and HARNESS_VIEWER_PORT,
# cwd = the Workshop checkout; Harness owns the process for the agent's life.
#
# Serves the workspace read-only over 127.0.0.1: the catalog lists every .step,
# .stp, .stl, .glb (and a few robot formats) under the workspace, and the page
# re-reads it every couple of seconds, so a STEP written by `gen --write`
# appears without a reload. `?file=<workspace-relative path>` opens one file.
set -eu
cd "$(dirname "$0")/../.."
: "${HARNESS_WORKSPACE:?HARNESS_WORKSPACE is required}"
: "${HARNESS_VIEWER_PORT:?HARNESS_VIEWER_PORT is required}"
unset VIEWER_SERVER_LIFETIME_MS   # no shutdown timer: Harness stops the process
VIEWER_ASSET_BACKEND=local-fs \
VIEWER_LOCAL_ROOT_DIR="" \
VIEWER_LOCAL_WORKSPACE_ROOT="$HARNESS_WORKSPACE" \
VIEWER_HOST=127.0.0.1 \
VIEWER_PORT="$HARNESS_VIEWER_PORT" \
VIEWER_DEFAULT_FILE="${WORKSHOP_VIEWER_DEFAULT_FILE:-model.step}" \
exec node harness/viewer/backend/server.mjs
