#!/usr/bin/env bash
# Build a self-contained release bundle: the Nuxt SPA packaged inside the Python wheel.
#
#   scripts/build.sh            → dist/rubit-finance-<version>.zip
#
# Run the result with:  uvx --from dist/rubit_finance-<version>-py3-none-any.whl rubit
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
STATIC="$ROOT/api/src/rubit/static"

echo "==> Building the web app"
pnpm -C "$ROOT/web" install --frozen-lockfile
pnpm -C "$ROOT/web" generate

echo "==> Packaging the SPA into the wheel"
rm -rf "$STATIC"
cp -r "$ROOT/web/.output/public" "$STATIC"

VERSION="$(cd "$ROOT/api" && uv version --short)"
rm -rf "$DIST"
mkdir -p "$DIST"
(cd "$ROOT/api" && uv build --wheel --out-dir "$DIST")

WHEEL="$(cd "$DIST" && ls rubit_finance-*.whl)"
cat > "$DIST/INSTALL.txt" <<EOF
Rubit Finance $VERSION

Requires uv (https://docs.astral.sh/uv/). From this folder, run:

    uvx --from $WHEEL rubit

The app opens in your browser at http://127.0.0.1:8000/.
Data is stored in your user data folder (override with RUBIT_DB_PATH).
EOF

ZIP="$DIST/rubit-finance-$VERSION.zip"
(cd "$DIST" && python3 -m zipfile -c "$ZIP" "$WHEEL" INSTALL.txt)
echo "==> Built $ZIP"
