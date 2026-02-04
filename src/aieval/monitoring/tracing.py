"""OpenTelemetry distributed tracing."""

import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aieval.config import get_settings

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None


def initialize_tracing(app: Any | None = None) -> None:
    """Initialize OpenTelemetry tracing."""
    settings = get_settings()
    
    if not settings.monitoring.opentelemetry_enabled:
        logger.info("OpenTelemetry tracing disabled")
        return
    
    global _tracer_provider
    
    if _tracer_provider is not None:
        logger.info("OpenTelemetry tracing already initialized")
        return
    
    try:
        # Create resource
        resource = Resource.create(
            {
                "service.name": settings.monitoring.opentelemetry_service_name,
                "service.version": "0.1.0",
            }
        )
        
        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)
        
        # Add span processor
        if settings.monitoring.opentelemetry_endpoint:
            exporter = OTLPSpanExporter(
                endpoint=settings.monitoring.opentelemetry_endpoint,
                insecure=True,  # Use TLS in production
            )
            _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        else:
            # Use console exporter for development
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
        # Set global tracer provider
        trace.set_tracer_provider(_tracer_provider)
        
        # Instrument FastAPI
        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        try:
            SQLAlchemyInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"Failed to instrument SQLAlchemy: {e}")
        
        logger.info(
            "OpenTelemetry tracing initialized",
            service_name=settings.monitoring.opentelemetry_service_name,
            endpoint=settings.monitoring.opentelemetry_endpoint,
        )
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {e}", exc_info=True)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)
