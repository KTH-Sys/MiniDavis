#!/bin/sh
set -eu
# Server-only environment. One process owns the town and its shared budget.
export REQUIRE_OPERATOR_TOKEN="${REQUIRE_OPERATOR_TOKEN:-true}"
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
