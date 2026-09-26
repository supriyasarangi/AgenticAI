#!/usr/bin/env bash
set -euo pipefail

docker compose up -d

export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=sip-calculator-backend

.venv/bin/uvicorn backend.main:app --reload --port 8000
