#!/bin/bash
# Build importdesign against a LOCAL panda-social-backend checkout.
# Nothing is committed to the backend repo — cmd/importdesign is copied in,
# built, and the binary lands in ~/text2cad/bin/. (Policy: pipeline stays
# inside the VM; no PRs to the production repo.)
set -euo pipefail
BACKEND="${1:-/root/psb-import}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HOME/text2cad/bin"
mkdir -p "$BACKEND/cmd/importdesign" "$OUT"
cp "$HERE/main.go" "$BACKEND/cmd/importdesign/main.go"
cd "$BACKEND"
PATH="/usr/local/go/bin:$PATH" go build -o "$OUT/importdesign" ./cmd/importdesign
echo "built: $OUT/importdesign"
