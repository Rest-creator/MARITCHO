import logging
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize logger with trace correlation formats
logging.basicConfig(
    format=(
        "%(asctime)s [%(levelname)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] "
        "%(name)s: %(message)s"
    ),
    level=logging.INFO,
)
logger = logging.getLogger("maricho-api")

class TraceIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            record.otelTraceID = format(current_span.get_span_context().trace_id, "032x")
            record.otelSpanID = format(current_span.get_span_context().span_id, "016x")
        else:
            record.otelTraceID = "00000000000000000000000000000000"
            record.otelSpanID = "0000000000000000"
        return True

logging.getLogger().handlers[0].addFilter(TraceIDFilter())

def setup_telemetry(app: FastAPI, service_name: str) -> None:
    # Build Resource definitions conforming to OTel semantic conventions
    resource = Resource.create(attributes={
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("APP_ENV", "production")
    })

    # Configure Tracer Provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP Exporter target
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

    # Set processor utilizing Batch handling
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="health/live,health/ready,metrics"
    )
    logger.info("OpenTelemetry trace instrumentation initialized.")
