import os
from collections.abc import Iterable, Sequence
from os import getenv
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from aleph_alpha_client import Client
from dotenv import load_dotenv
from fsspec.implementations.memory import MemoryFileSystem  # type: ignore
from pharia_inference_sdk.connectors import (
    AlephAlphaClientProtocol,
    LimitedConcurrencyClient,
)
from pharia_inference_sdk.core import Task, TaskSpan, Tracer, utc_now
from pydantic import BaseModel
from pytest import fixture

from pharia_studio_sdk.connectors.studio.studio import StudioClient
from pharia_studio_sdk.evaluation import (
    AsyncInMemoryEvaluationRepository,
    DatasetRepository,
    EvaluationOverview,
    Example,
    ExampleEvaluation,
    FileAggregationRepository,
    FileEvaluationRepository,
    FileRunRepository,
    InMemoryAggregationRepository,
    InMemoryDatasetRepository,
    InMemoryEvaluationRepository,
    InMemoryRunRepository,
    RunOverview,
)
from pharia_studio_sdk.evaluation.aggregation.aggregator import AggregationLogic
from pharia_studio_sdk.evaluation.benchmark.studio_benchmark import (
    StudioBenchmarkRepository,
)
from pharia_studio_sdk.evaluation.dataset.studio_dataset_repository import (
    StudioDatasetRepository,
)
from pharia_studio_sdk.evaluation.evaluation.evaluator.evaluator import (
    SingleOutputEvaluationLogic,
)

load_dotenv()

FAIL_IN_EVAL_INPUT = "fail in eval"
FAIL_IN_TASK_INPUT = "fail in task"


class DummyTask(Task[str, str]):
    def do_run(self, input: str, tracer: Tracer) -> str:
        if input == FAIL_IN_TASK_INPUT:
            raise RuntimeError(input)
        return input


class DummyEvaluation(BaseModel):
    result: str


class DummyAggregatedEvaluation(BaseModel):
    score: float


class DummyAggregatedEvaluationWithResultList(BaseModel):
    results: Sequence[DummyEvaluation]


class DummyEvaluationLogic(
    SingleOutputEvaluationLogic[
        str,
        str,
        str,
        DummyEvaluation,
    ]
):
    def do_evaluate_single_output(
        self,
        example: Example[str, str],
        output: str,
    ) -> DummyEvaluation:
        if output == FAIL_IN_EVAL_INPUT:
            raise RuntimeError(output)
        return DummyEvaluation(result="Dummy result")


class DummyAggregation(BaseModel):
    num_evaluations: int


class DummyAggregationLogic(AggregationLogic[DummyEvaluation, DummyAggregation]):
    def aggregate(self, evaluations: Iterable[DummyEvaluation]) -> DummyAggregation:
        return DummyAggregation(num_evaluations=len(list(evaluations)))


@fixture
def studio_client() -> StudioClient:
    project_name = str(uuid4())
    client = StudioClient(project_name)
    client.create_project(project_name)
    return client


@fixture
def mock_studio_client() -> Mock:
    return Mock(spec=StudioClient)


@fixture
def studio_benchmark_repository(
    mock_studio_client: StudioClient,
) -> StudioBenchmarkRepository:
    return StudioBenchmarkRepository(
        studio_client=mock_studio_client,
    )


@fixture
def studio_dataset_repository(
    mock_studio_client: StudioClient,
) -> StudioDatasetRepository:
    return StudioDatasetRepository(
        studio_client=mock_studio_client,
    )


class DummyStringInput(BaseModel):
    input: str = "dummy-input"


class DummyStringExpectedOutput(BaseModel):
    expected_output: str = "dummy-expected-output"


class DummyStringOutput(BaseModel):
    output: str = "dummy-output"


class DummyStringEvaluation(BaseModel):
    evaluation: str = "dummy-evaluation"


class DummyStringTask(Task[DummyStringInput, DummyStringOutput]):
    def do_run(self, input: DummyStringInput, task_span: TaskSpan) -> DummyStringOutput:
        if input.input == FAIL_IN_TASK_INPUT:
            raise RuntimeError(input)
        return DummyStringOutput()


@fixture
def dummy_string_task() -> DummyStringTask:
    return DummyStringTask()


@fixture
def dummy_string_example() -> Example[DummyStringInput, DummyStringExpectedOutput]:
    return Example(
        input=DummyStringInput(),
        expected_output=DummyStringExpectedOutput(),
        metadata={"some_key": "some_value"},
    )


@fixture
def dummy_string_examples(
    dummy_string_example: Example[DummyStringInput, DummyStringExpectedOutput],
) -> Iterable[Example[DummyStringInput, DummyStringExpectedOutput]]:
    return [dummy_string_example]


@fixture
def dummy_string_dataset_id(
    dummy_string_examples: Iterable[
        Example[DummyStringInput, DummyStringExpectedOutput]
    ],
    in_memory_dataset_repository: DatasetRepository,
) -> str:
    return in_memory_dataset_repository.create_dataset(
        examples=dummy_string_examples, dataset_name="test-dataset"
    ).id


@fixture
def sequence_examples() -> (
    Iterable[Example[DummyStringInput, DummyStringExpectedOutput]]
):
    return [
        Example(
            input=DummyStringInput(input="success"),
            expected_output=DummyStringExpectedOutput(),
            id="example-1",
        ),
        Example(
            input=DummyStringInput(input=FAIL_IN_TASK_INPUT),
            expected_output=DummyStringExpectedOutput(),
            id="example-2",
        ),
        Example(
            input=DummyStringInput(input=FAIL_IN_EVAL_INPUT),
            expected_output=DummyStringExpectedOutput(),
            id="example-3",
        ),
    ]


@fixture
def successful_example_evaluation(
    evaluation_id: str,
) -> ExampleEvaluation[DummyEvaluation]:
    return ExampleEvaluation(
        evaluation_id=evaluation_id,
        example_id="successful_example",
        result=DummyEvaluation(result="result"),
    )


@fixture
def file_aggregation_repository(tmp_path: Path) -> FileAggregationRepository:
    return FileAggregationRepository(tmp_path)


@fixture
def file_evaluation_repository(tmp_path: Path) -> FileEvaluationRepository:
    return FileEvaluationRepository(tmp_path)


@fixture
def file_run_repository(tmp_path: Path) -> FileRunRepository:
    return FileRunRepository(tmp_path)


@fixture()
def temp_file_system() -> Iterable[MemoryFileSystem]:
    mfs = MemoryFileSystem()

    try:
        yield mfs
    finally:
        mfs.store.clear()


@fixture(scope="session")
def hugging_face_test_repository_id() -> str:
    return f"Aleph-Alpha/IL-temp-tests-{uuid4()}"


@fixture(scope="session")
def hugging_face_token() -> str:
    token = getenv("HUGGING_FACE_TOKEN")
    assert isinstance(token, str)
    return token


@fixture(scope="session")
def token() -> str:
    token = getenv("AA_TOKEN")
    assert isinstance(token, str)
    return token


@fixture(scope="session")
def inference_url() -> str:
    return os.environ["CLIENT_URL"]


@fixture(scope="session")
def client(token: str, inference_url: str) -> AlephAlphaClientProtocol:
    return LimitedConcurrencyClient(
        Client(token, host=inference_url),
        max_concurrency=10,
        max_retry_time=10,
    )


@fixture
def in_memory_dataset_repository() -> InMemoryDatasetRepository:
    return InMemoryDatasetRepository()


@fixture
def in_memory_run_repository() -> InMemoryRunRepository:
    return InMemoryRunRepository()


@fixture
def in_memory_evaluation_repository() -> InMemoryEvaluationRepository:
    return InMemoryEvaluationRepository()


@fixture
def in_memory_aggregation_repository() -> InMemoryAggregationRepository:
    return InMemoryAggregationRepository()


@fixture()
def async_in_memory_evaluation_repository() -> AsyncInMemoryEvaluationRepository:
    return AsyncInMemoryEvaluationRepository()


@fixture
def run_overview() -> RunOverview:
    return RunOverview(
        dataset_id="dataset-id",
        id="run-id-1",
        start=utc_now(),
        end=utc_now(),
        failed_example_count=0,
        successful_example_count=3,
        description="test run overview 1",
        labels=set(),
        metadata=dict(),
    )


@fixture
def evaluation_id() -> str:
    return "evaluation-id-1"


@fixture
def evaluation_overview(
    evaluation_id: str, run_overview: RunOverview
) -> EvaluationOverview:
    return EvaluationOverview(
        id=evaluation_id,
        start_date=utc_now(),
        end_date=utc_now(),
        successful_evaluation_count=1,
        failed_evaluation_count=1,
        run_overviews=frozenset([run_overview]),
        description="test evaluation overview 1",
        labels=set(),
        metadata=dict(),
    )
