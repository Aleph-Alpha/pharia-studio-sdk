from pharia_studio_sdk.evaluation.aggregation.file_aggregation_repository import (
    FileSystemAggregationRepository,
)
from pharia_studio_sdk.evaluation.infrastructure.hugging_face_repository import (
    HuggingFaceRepository,
)


class HuggingFaceAggregationRepository(
    FileSystemAggregationRepository, HuggingFaceRepository
):
    # this class inherits all its behavior from its parents
    pass
