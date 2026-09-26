"""OpenTelemetry initialization: global TracerProvider + MeterProvider,
plus automatic instrumentation for FastAPI (inbound HTTP), httpx (outbound
HTTP to the World Bank API), and basic system metrics (CPU/memory/network).

There is no database in this app, so no DB instrumentation is registered.
"""

import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "sip-calculator-backend")
OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


def configure_otel(app: FastAPI) -> trace.Tracer:
    resource = Resource.create({ResourceAttributes.SERVICE_NAME: SERVICE_NAME})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Automatic instrumentation: system metrics, outbound httpx, inbound FastAPI/ASGI.
    SystemMetricsInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    FastAPIInstrumentor.instrument_app(app)

    # Handed back so callers can add manual spans on top of the automatic ones.
    return trace.get_tracer(SERVICE_NAME)
