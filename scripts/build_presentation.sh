#!/bin/sh
set -eu
MINIDAVIS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if ! command -v tectonic >/dev/null 2>&1; then
  echo 'Install Tectonic, then run this script again.' >&2
  exit 1
fi
mkdir -p "$MINIDAVIS_ROOT/output/pdf"
cd "$MINIDAVIS_ROOT/docs/presentation"
exec tectonic --outdir "$MINIDAVIS_ROOT/output/pdf" MiniDavis-Presentation-Guide.tex
