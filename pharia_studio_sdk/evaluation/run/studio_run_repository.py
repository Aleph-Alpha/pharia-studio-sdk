from pharia_inference_sdk.core.tracer import Tracer

from pharia_studio_sdk.connectors.studio.studio import StudioClient
from pharia_studio_sdk.evaluation.run.in_memory_run_repository import (
    InMemoryRunRepository,
)
from pharia_studio_sdk.studio_tracer import StudioTracer


class StudioRunRepository(InMemoryRunRepository):
    """Run repository that uses the studio tracer to record traces.

    The runs overviews are stored in the in-memory run repository.
    The traces are stored in the studio tracer, which is used to send traces to studio.
    """
    def __init__(self, client: StudioClient):
        self.client = client
        super().__init__()

    def example_tracer(self, run_id: str, example_id: str) -> Tracer | None:
        return self._example_traces.get(f"{run_id}/{example_id}")

    def create_tracer_for_example(self, run_id: str, example_id: str) -> Tracer:
        tracer = StudioTracer(self.client)
        self._example_traces[f"{run_id}/{example_id}"] = tracer
        return tracer
