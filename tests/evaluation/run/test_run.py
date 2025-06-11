from collections.abc import Iterable, Sequence
from pathlib import Path

from dotenv import load_dotenv
from pharia_inference_sdk.connectors.limited_concurrency_client import (
    AlephAlphaClientProtocol,
)
from pharia_inference_sdk.core import Task, TaskSpan
from pydantic import BaseModel
from pytest import fixture

from pharia_studio_sdk.evaluation.aggregation.aggregator import AggregationLogic
from pharia_studio_sdk.evaluation.aggregation.file_aggregation_repository import (
    FileAggregationRepository,
)
from pharia_studio_sdk.evaluation.dataset.domain import Example
from pharia_studio_sdk.evaluation.dataset.file_dataset_repository import (
    FileDatasetRepository,
)
from pharia_studio_sdk.evaluation.evaluation.evaluator.evaluator import EvaluationLogic
from pharia_studio_sdk.evaluation.run.domain import SuccessfulExampleOutput
from pharia_studio_sdk.evaluation.run_evaluation import main

load_dotenv()


@fixture
def examples() -> Sequence[Example[None, None]]:
    return [Example(input=None, expected_output=None)]


class DummyEvaluation(BaseModel):
    correct: bool


class DummyAggregation(BaseModel):
    correct_rate: float


class DummyTask(Task[None, None]):
    def __init__(self) -> None:
        pass

    def do_run(self, input: None, task_span: TaskSpan) -> None:
        return input


class DummyTaskWithClient(DummyTask):
    def __init__(self, client: AlephAlphaClientProtocol) -> None:
        pass


class DummyAggregationLogic(AggregationLogic[DummyEvaluation, DummyAggregation]):
    def aggregate(self, evaluations: Iterable[DummyEvaluation]) -> DummyAggregation:
        list(evaluations)
        return DummyAggregation(correct_rate=1.0)


class DummyEvaluationLogic(EvaluationLogic[None, None, None, DummyEvaluation]):
    def do_evaluate(
        self, example: Example[None, None], *output: SuccessfulExampleOutput[None]
    ) -> DummyEvaluation:
        return DummyEvaluation(correct=True)


def test_run_evaluation(
    tmp_path: Path, examples: Sequence[Example[None, None]]
) -> None:
    dataset_path = tmp_path / "dataset"
    dataset_repository = FileDatasetRepository(dataset_path)
    dataset_id = dataset_repository.create_dataset(
        examples=examples, dataset_name="test-dataset"
    ).id

    aggregation_path = tmp_path / "eval"
    aggregation_repository = FileAggregationRepository(aggregation_path)

    main(
        [
            "",
            "--eval-logic",
            "tests.evaluation.run.test_run.DummyEvaluationLogic",
            "--aggregation-logic",
            "tests.evaluation.run.test_run.DummyAggregationLogic",
            "--task",
            "tests.evaluation.run.test_run.DummyTask",
            "--dataset-repository-path",
            str(dataset_path),
            "--dataset-id",
            dataset_id,
            "--target-dir",
            str(aggregation_path),
            "--description",
            "dummy-evaluator",
        ]
    )
    ids = aggregation_repository.aggregation_overview_ids()
    assert len(ids) == 1
    overview = aggregation_repository.aggregation_overview(ids[0], DummyAggregation)
    assert overview
    assert overview.successful_evaluation_count == 1


def test_run_evaluation_with_task_with_client(
    tmp_path: Path, examples: Sequence[Example[None, None]]
) -> None:
    dataset_path = tmp_path / "dataset"
    dataset_repository = FileDatasetRepository(dataset_path)
    dataset_id = dataset_repository.create_dataset(
        examples=examples, dataset_name="test-dataset"
    ).id

    eval_path = tmp_path / "eval"

    main(
        [
            "",
            "--eval-logic",
            "tests.evaluation.run.test_run.DummyEvaluationLogic",
            "--aggregation-logic",
            "tests.evaluation.run.test_run.DummyAggregationLogic",
            "--task",
            "tests.evaluation.run.test_run.DummyTaskWithClient",
            "--dataset-repository-path",
            str(dataset_path),
            "--dataset-id",
            dataset_id,
            "--target-dir",
            str(eval_path),
            "--description",
            "dummy-evaluator",
        ]
    )
