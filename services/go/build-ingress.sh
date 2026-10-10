#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/outbox_delivery"
# Preserve the existing no-module regression suite, while building a separate
# fully linked executable only when the PostgreSQL driver is available.
go build -o "${CB_GO_BINARY_OUTPUT:-/tmp/capitalbridge-go-ingress}"   -tags capitalbridge_service .
