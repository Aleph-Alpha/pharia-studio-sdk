from pharia_inference_sdk.core import utc_now
from pytest import fixture

from pharia_studio_sdk.evaluation import AggregationOverview, EvaluationOverview
from tests.conftest import DummyAggregatedEvaluation


@fixture
def dummy_aggregated_evaluation() -> DummyAggregatedEvaluation:
    return DummyAggregatedEvaluation(score=0.5)


@fixture
def aggregation_overview(
    evaluation_overview: EvaluationOverview,
    dummy_aggregated_evaluation: DummyAggregatedEvaluation,
) -> AggregationOverview[DummyAggregatedEvaluation]:
    return AggregationOverview(
        evaluation_overviews=frozenset([evaluation_overview]),
        id="aggregation-id",
        start=utc_now(),
        end=utc_now(),
        successful_evaluation_count=5,
        crashed_during_evaluation_count=3,
        description="dummy-evaluator",
        statistics=dummy_aggregated_evaluation,
    )
