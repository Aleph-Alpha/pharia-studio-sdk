from collections.abc import Sequence
from datetime import datetime

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)
from pharia_inference_sdk.core import (
    CompositeTracer,
    Context,
    ExportedSpan,
    InMemoryTracer,
    PydanticSerializable,
    Span,
    TaskSpan,
)
from pharia_inference_sdk.core.tracer import (
    OpenTelemetryTracer,
    Tracer,
)

from pharia_studio_sdk.connectors.studio.studio import StudioClient


class StudioSpanExporter(OTLPSpanExporter):
    def __init__(self, client: StudioClient) -> None:
        self.client = client

        # Construct the full traces endpoint
        traces_endpoint = f"{self.client.url}/api/projects/{self.client.project_id}/traces_v2"
        super().__init__(
            endpoint=traces_endpoint,
            headers=self.client.get_headers(),
        )


class StudioSpanProcessor(SimpleSpanProcessor):
    """Signal that a processor has been registered by the SDK."""

    pass


class StudioTracer(Tracer):
    """OTLP Tracer for studio. This utilizes the traces_v2 endpoint to send traces to studio.

    It leverages the `CompositeTracer` to combine the `InMemoryTracer` and `OpenTelemetryTracer`.
    The `OpenTelemetryTracer` is used to send traces to studio, while the `InMemoryTracer` is used for local interaction with the recorded traces.
    """
    def __init__(self, client: StudioClient) -> None:
        self.client = client

        # Set up OpenTelemetry tracer for studio integration
        trace_provider = TracerProvider()
        processor = StudioSpanProcessor(
            StudioSpanExporter(
                client=self.client
            )
        )
        trace_provider.add_span_processor(processor)
        self._otel_tracer = OpenTelemetryTracer(
            tracer=trace_provider.get_tracer(__name__)
        )
        self._in_memory_tracer = InMemoryTracer()
        # NOTE: Do not change order, otherwise `export_for_viewing` will not work. This is due to `CompositeTracer` using the first tracer for `export_for_viewing`.
        self._composite_tracer = CompositeTracer([self._in_memory_tracer, self._otel_tracer])

    @property
    def context(self) -> Context | None:
        return self._composite_tracer.context

    def export_for_viewing(self) -> Sequence[ExportedSpan]:
        """Export traces from the in-memory tracer for viewing."""
        return self._composite_tracer.export_for_viewing()

    def span(self, name: str, timestamp: datetime | None = None) -> Span:
        return self._composite_tracer.span(name, timestamp)

    def task_span(
        self, name: str, input: PydanticSerializable, timestamp: datetime | None = None
    ) -> TaskSpan:
        return self._composite_tracer.task_span(name, input, timestamp)
