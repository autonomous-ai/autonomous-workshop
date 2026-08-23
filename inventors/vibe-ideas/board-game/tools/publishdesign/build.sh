#!/bin/bash
# Build publishdesign against a LOCAL panda-social-backend checkout.
#
# The binary has to be compiled INSIDE the pandasocial module: it calls
# services.ImportDesign, whose config argument is a type from
# pandasocial/internal/config, and Go forbids importing an `internal/` package
# from another module. So main.go is copied into <backend>/cmd/publishdesign,
# built, and the copy is removed again — the backend checkout is left exactly
# as it was found, and nothing of this pipeline is ever committed there.
#
#   ./build.sh [path/to/panda-social-backend]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BACKEND="${1:-$(cd "$HERE/../../../../panda-social-backend" && pwd)}"
OUT="$HERE/../bin"

[ -f "$BACKEND/go.mod" ] || { echo "not a Go checkout: $BACKEND" >&2; exit 1; }
grep -q '^module pandasocial$' "$BACKEND/go.mod" || { echo "not panda-social-backend: $BACKEND" >&2; exit 1; }

STAGE="$BACKEND/cmd/publishdesign"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE" "$OUT"
cp "$HERE/main.go" "$STAGE/main.go"
(cd "$BACKEND" && go build -o "$OUT/publishdesign" ./cmd/publishdesign)
echo "built: $OUT/publishdesign (against $BACKEND)"
