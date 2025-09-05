from collections.abc import Iterable, Sequence
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from _pytest.fixtures import FixtureRequest
from pharia_inference_sdk.core import Output, utc_now
from pydantic import BaseModel, ValidationError
from pytest import fixture

from pharia_studio_sdk.evaluation import ExampleOutput, RunOverview, RunRepository
from pharia_studio_sdk.evaluation.run.run_repository import (
    FailedExampleRun,
    RecoveryData,
)
from pharia_studio_sdk.evaluation.run.studio_run_repository import StudioRunRepository
from pharia_studio_sdk.studio_tracer import StudioTracer
from tests.conftest import DummyStringInput


@fixture
def studio_run_repository(mock_studio_client: Mock) -> StudioRunRepository:
    # Configure the mock client with required attributes
    mock_studio_client.url = "https://studio.example.com"
    mock_studio_client.project_id = "test-project-id"
    mock_studio_client.get_headers.return_value = {
        "Accept": "application/json",
        "Authorization": "Bearer test-token",
    }
    return StudioRunRepository(mock_studio_client)


@fixture
def run_overviews() -> Sequence[RunOverview]:
    run_overview_ids = [str(uuid4()) for _ in range(10)]
    run_overviews = []
    for run_id in run_overview_ids:
        run_overview = RunOverview(
            dataset_id="dataset-id",
            id=run_id,
            start=utc_now(),
            end=utc_now(),
            failed_example_count=0,
            successful_example_count=1,
            description="test run overview",
            labels=set(),
            metadata=dict(),
        )
        run_overviews.append(run_overview)
    return run_overviews


def get_example_via_both_retrieval_methods(
    run_repository: RunRepository,
    run_id: str,
    example_id: str,
    output_type: type[Output],
) -> Iterable[ExampleOutput[Output] | ExampleOutput[FailedExampleRun] | None]:
    yield run_repository.example_output(run_id, example_id, output_type)
    yield next(iter(run_repository.example_outputs(run_id, output_type)))



def test_stores_and_returns_example_output(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_id = "run-id"
    example_id = "example-id"
    example_output = ExampleOutput(run_id=run_id, example_id=example_id, output=None)

    run_repository.store_example_output(example_output)
    for stored_example_output in get_example_via_both_retrieval_methods(
        run_repository, run_id, example_id, type(None)
    ):
        assert stored_example_output == example_output



def test_example_output_creating_with_dict_subtype_and_reading_with_actual_type_works(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    class TestClass(BaseModel):
        data: str

    run_repository: RunRepository = studio_run_repository
    run_id = "run-id"
    example_id = "example-id"
    data = "test-data"
    example_output = ExampleOutput(
        run_id=run_id, example_id=example_id, output=TestClass(data=data).model_dump()
    )

    run_repository.store_example_output(example_output)
    for stored_example_output in get_example_via_both_retrieval_methods(
        run_repository, run_id, example_id, TestClass
    ):
        assert stored_example_output is not None
        assert type(stored_example_output.output) is TestClass
        assert stored_example_output.output.data == "test-data"

def test_example_output_can_retrieve_failed_examples(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    class TestClass(BaseModel):
        data: str

    run_repository: RunRepository = studio_run_repository
    run_id = "run-id"
    example_id = "example-id"
    data = FailedExampleRun(error_message="error")
    example_output = ExampleOutput(
        run_id=run_id,
        example_id=example_id,
        output=data,
    )

    run_repository.store_example_output(example_output)
    for stored_example_output in get_example_via_both_retrieval_methods(
        run_repository, run_id, example_id, TestClass
    ):
        assert stored_example_output is not None
        assert stored_example_output.output == data


def test_example_output_does_not_work_with_incorrect_types(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_id = "run-id"
    example_id = "example-id"
    example_output = ExampleOutput(run_id=run_id, example_id=example_id, output=None)

    run_repository.store_example_output(example_output)
    with pytest.raises(ValidationError):
        run_repository.example_output(run_id, example_id, str)

    with pytest.raises(ValidationError):
        next(iter(run_repository.example_outputs(run_id, str)))



@pytest.mark.filterwarnings("ignore::UserWarning")
def test_example_output_returns_none_for_not_existing_example_id(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_id = "run-id"
    example_id = "example-id"
    example_output = ExampleOutput(run_id=run_id, example_id=example_id, output=None)
    run_repository.store_example_output(example_output)

    assert (
        run_repository.example_output(run_id, "not-existing-example-id", type(None))
        is None
    )


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_example_output_returns_none_for_not_existing_run_id(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_id = "run-id"
    example_id = "example-id"
    example_output = ExampleOutput(run_id=run_id, example_id=example_id, output=None)
    run_repository.store_example_output(example_output)

    assert (
        run_repository.example_output("not-existing-run-id", example_id, type(None))
        is None
    )
    assert (
        run_repository.example_output(
            "not-existing-run-id", "not-existing-example-id", type(None)
        )
        is None
    )


@patch("pharia_studio_sdk.evaluation.run.studio_run_repository.StudioTracer")
def test_can_store_and_return_example_evaluation_tracer_and_trace(
    mock_studio_tracer_class: Mock,
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    # Create a mock tracer instance
    mock_tracer_instance = Mock()
    mock_task_span = Mock()
    mock_processor = Mock()

    # Configure the mock tracer instance
    mock_tracer_instance.task_span.return_value = mock_task_span
    mock_tracer_instance.processor = mock_processor
    mock_tracer_instance.context = "mock_context"

    # Configure the mock class to return our mock instance
    mock_studio_tracer_class.return_value = mock_tracer_instance

    run_repository: RunRepository = studio_run_repository
    run_id = "run_id"
    example_id = "example_id"
    now = datetime.now()

    tracer = run_repository.create_tracer_for_example(run_id, example_id)
    task_span = tracer.task_span(
        "task", DummyStringInput(input="input"), now
    )
    task_span.end()


    example_tracer = run_repository.example_tracer(run_id, example_id)

    # Verify that StudioTracer was instantiated with the correct client
    mock_studio_tracer_class.assert_called_once_with(studio_run_repository.client)

    # Verify that the tracer methods were called correctly
    mock_tracer_instance.task_span.assert_called_once_with(
        "task", DummyStringInput(input="input"), now
    )
    mock_task_span.end.assert_called_once()

    # Verify that the same tracer instance is returned
    assert tracer == mock_tracer_instance
    assert example_tracer == mock_tracer_instance
    assert tracer.context == example_tracer.context


def test_create_tracer_for_example_returns_studio_tracer(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    """Test that StudioRunRepository returns StudioTracer instances."""
    run_repository: StudioRunRepository = studio_run_repository
    run_id = "run_id"
    example_id = "example_id"

    tracer = run_repository.create_tracer_for_example(run_id, example_id)

    assert isinstance(tracer, StudioTracer)
    assert tracer.client == run_repository.client


def test_run_example_output_ids_returns_all_sorted_ids(
    studio_run_repository: StudioRunRepository, request: FixtureRequest, run_overview: RunOverview
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_repository.store_run_overview(run_overview)
    example_ids = [str(uuid4()) for _ in range(10)]
    for example_id in example_ids:
        example_output = ExampleOutput(
            run_id=run_overview.id, example_id=example_id, output=None
        )
        run_repository.store_example_output(example_output)

    example_output_ids = run_repository.example_output_ids(run_overview.id)

    assert example_output_ids == sorted(example_ids)


def test_run_example_outputs_returns_sorted_run_example_outputs(
    studio_run_repository: StudioRunRepository, request: FixtureRequest, run_overview: RunOverview
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_repository.store_run_overview(run_overview)
    example_ids = [str(uuid4()) for _ in range(10)]
    expected_example_outputs = []
    for example_id in example_ids:
        example_output = ExampleOutput(
            run_id=run_overview.id, example_id=example_id, output=None
        )
        run_repository.store_example_output(example_output)
        expected_example_outputs.append(example_output)

    example_outputs = list(run_repository.example_outputs(run_overview.id, type(None)))

    assert example_outputs == sorted(
        expected_example_outputs,
        key=lambda example: (example.run_id, example.example_id),
    )


def test_stores_and_returns_a_run_overview(
    studio_run_repository: StudioRunRepository, request: FixtureRequest, run_overview: RunOverview
) -> None:
    run_repository: RunRepository = studio_run_repository

    run_repository.store_run_overview(run_overview)
    stored_run_overview = run_repository.run_overview(run_overview.id)

    assert stored_run_overview == run_overview


def test_run_overview_returns_none_for_not_existing_run_id(
    studio_run_repository: StudioRunRepository, request: FixtureRequest, run_overview: RunOverview
) -> None:
    run_repository: RunRepository = studio_run_repository

    stored_run_overview = run_repository.run_overview("not-existing-id")

    assert stored_run_overview is None


def test_run_overviews_returns_all_sorted_run_overviews(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
    run_overviews: Iterable[RunOverview],
) -> None:
    run_repository: RunRepository = studio_run_repository

    for run_overview in run_overviews:
        run_repository.store_run_overview(run_overview)

    stored_run_overviews = list(run_repository.run_overviews())

    assert stored_run_overviews == sorted(
        run_overviews, key=lambda overview: overview.id
    )



def test_run_overview_ids_returns_all_sorted_ids(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
    run_overviews: Iterable[RunOverview],
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_overview_ids = [run_overview.id for run_overview in run_overviews]
    for run_overview in run_overviews:
        run_repository.store_run_overview(run_overview)

    stored_run_overview_ids = list(run_repository.run_overview_ids())

    assert stored_run_overview_ids == sorted(run_overview_ids)



def test_failed_example_outputs_returns_only_failed_examples(
    studio_run_repository: StudioRunRepository, request: FixtureRequest, run_overview: RunOverview
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_repository.store_run_overview(run_overview)

    run_repository.store_example_output(
        ExampleOutput(
            run_id=run_overview.id,
            example_id="1",
            output=FailedExampleRun(error_message="test"),
        )
    )
    run_repository.store_example_output(
        ExampleOutput(run_id=run_overview.id, example_id="2", output=None)
    )

    failed_outputs = list(
        run_repository.failed_example_outputs(
            run_id=run_overview.id, output_type=type(None)
        )
    )

    assert len(failed_outputs) == 1
    assert failed_outputs[0].example_id == "1"



def test_successful_example_outputs_returns_only_successful_examples(
    studio_run_repository: StudioRunRepository, request: FixtureRequest, run_overview: RunOverview
) -> None:
    run_repository: RunRepository = studio_run_repository
    run_repository.store_run_overview(run_overview)

    run_repository.store_example_output(
        ExampleOutput(
            run_id=run_overview.id,
            example_id="1",
            output=FailedExampleRun(error_message="test"),
        )
    )
    run_repository.store_example_output(
        ExampleOutput(run_id=run_overview.id, example_id="2", output=None)
    )

    successful_outputs = list(
        run_repository.successful_example_outputs(
            run_id=run_overview.id, output_type=type(None)
        )
    )

    assert len(successful_outputs) == 1
    assert successful_outputs[0].example_id == "2"



def test_recovery_from_crash(
    studio_run_repository: StudioRunRepository,
    request: FixtureRequest,
) -> None:
    run_repository: RunRepository = studio_run_repository
    test_hash = str(uuid4())
    run_id = str(uuid4())

    expected_recovery_data = RecoveryData(
        run_id=run_id, finished_examples=[str(uuid4()), str(uuid4())]
    )

    # Create
    run_repository.create_temporary_run_data(test_hash, run_id)

    # Write
    for example_id in expected_recovery_data.finished_examples:
        run_repository.temp_store_finished_example(
            tmp_hash=test_hash, example_id=example_id
        )

    # Read
    finished_examples = run_repository.finished_examples(test_hash)
    assert finished_examples == expected_recovery_data

    # Delete
    run_repository.delete_temporary_run_data(test_hash)
    assert run_repository.finished_examples(test_hash) is None
