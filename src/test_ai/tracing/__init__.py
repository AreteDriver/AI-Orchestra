"""Distributed tracing for Gorgon workflows.

Provides W3C Trace Context compatible tracing with:
- Trace and span ID generation
- Context propagation across functions and async calls
- Integration with structured logging
- HTTP header propagation (traceparent, tracestate)
- OTLP export for OpenTelemetry-compatible backends
"""

from test_ai.tracing.context import (
    TraceContext,
    Span,
    get_current_trace,
    get_current_span,
    start_trace,
    start_span,
    trace_context,
    span_context,
)
from test_ai.tracing.propagation import (
    extract_trace_context,
    inject_trace_headers,
    TRACEPARENT_HEADER,
    TRACESTATE_HEADER,
)
from test_ai.tracing.middleware import TracingMiddleware
from test_ai.tracing.export import (
    ExportConfig,
    TraceExporter,
    ConsoleExporter,
    OTLPHTTPExporter,
    BatchExporter,
    get_batch_exporter,
    export_trace,
    shutdown_exporter,
)

__all__ = [
    # Context
    "TraceContext",
    "Span",
    "get_current_trace",
    "get_current_span",
    "start_trace",
    "start_span",
    "trace_context",
    "span_context",
    # Propagation
    "extract_trace_context",
    "inject_trace_headers",
    "TRACEPARENT_HEADER",
    "TRACESTATE_HEADER",
    # Middleware
    "TracingMiddleware",
    # Export
    "ExportConfig",
    "TraceExporter",
    "ConsoleExporter",
    "OTLPHTTPExporter",
    "BatchExporter",
    "get_batch_exporter",
    "export_trace",
    "shutdown_exporter",
]
