import os
from os import getenv

from aleph_alpha_client import Client
from dotenv import load_dotenv
from pharia_inference_sdk.connectors import (
    AlephAlphaClientProtocol,
    LimitedConcurrencyClient,
)
from pharia_inference_sdk.core import utc_now
from pytest import fixture

from pharia_studio_sdk.evaluation import (
    AsyncInMemoryEvaluationRepository,
    EvaluationOverview,
    InMemoryAggregationRepository,
    InMemoryDatasetRepository,
    InMemoryEvaluationRepository,
    InMemoryRunRepository,
    RunOverview,
)


@fixture(scope="session")
def token() -> str:
    load_dotenv()
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
