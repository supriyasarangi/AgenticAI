# Observability

The SIP Calculator backend emits traces and metrics via OpenTelemetry to a
local Collector → Tempo (traces) / Prometheus (metrics) → Grafana stack.

Instrumented:
- **Inbound HTTP** — every FastAPI route (`FastAPIInstrumentor`, automatic)
- **Outbound HTTP** — every call to the World Bank API (`HTTPXClientInstrumentor`, automatic)
- **System metrics** — CPU, memory, network (`SystemMetricsInstrumentor`, automatic)
- **One manual span** — `inflation_adjustment` inside `POST /api/calculate` (`backend/main.py`), nested under the automatic request span

There is no database in this app, so there are no DB spans.

## 1. Start everything

```bash
./start.sh
```

This starts the collector/Tempo/Prometheus/Grafana containers (`docker compose up -d`), then runs the FastAPI app on the host with `OTEL_EXPORTER_OTLP_ENDPOINT` pointed at the collector.

If you'd rather run the pieces yourself:

```bash
docker compose up -d
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=sip-calculator-backend
.venv/bin/uvicorn backend.main:app --reload --port 8000
```

## 2. Generate some traffic

```bash
curl -X POST http://localhost:8000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"monthly_investment": 5000, "annual_return_rate": 12, "years": 10, "country_code": "IN", "include_inflation_adjustment": true}'

curl http://localhost:8000/api/inflation/IN
```

## 3. Log into Grafana

Open [http://localhost:3000](http://localhost:3000). Default first-run login is `admin` / `admin` — Grafana will offer to let you set a new password, you can skip that for local testing.

Prometheus and Tempo are already provisioned as datasources (`grafana/provisioning/datasources/datasources.yml`) — nothing to configure by hand.

## 4. Verify traces

**Explore** (left sidebar) → select the **Tempo** datasource → search by `service.name = sip-calculator-backend`. Open a `POST /api/calculate` trace — you should see the automatic FastAPI span, the manual `inflation_adjustment` child span, and the automatic outbound httpx span to `api.worldbank.org` nested inside it.

## 5. Verify metrics

**Explore** → select the **Prometheus** datasource → try:
- `http_server_duration_milliseconds_count` — request counts per route
- `system_cpu_utilization` / `system_memory_usage` — system metrics

## Troubleshooting

- `docker compose logs otel-collector` — the collector's `debug` exporter logs every trace/metric batch it receives, so this confirms data is arriving even before it's visible in Grafana.
- `docker compose ps` — confirm all four containers (`otel-collector`, `tempo`, `prometheus`, `grafana`) are up.
- If Grafana shows no data, double check the app was actually started with `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` set — without it the SDK defaults to the same address, but it's worth confirming nothing else overrode it.
