# pharia-studio-sdk

Formerly the `intelligence_layer/evaluation` package.

## Overview

The pharia-studio-sdk provides a set of tools for evaluating and benchmarking LLMs with the Studio applications.

## Installation
The SDK is published on [PyPI](https://pypi.org/project/pharia-studio-sdk/).

To add the SDK as a dependency to an existing project managed, run
```bash
pip install pharia-studio-sdk
```

## Usage

```python
from pharia_studio_sdk.connectors.studio.studio_client import StudioClient
from pharia_studio_sdk.evaluation.aggregation.aggregator import AggregationLogic
from pharia_studio_sdk.evaluation.evaluation.evaluator.evaluator import EvaluationLogic
from pharia_studio_sdk.evaluation.benchmark.studio_benchmark import StudioBenchmarkRepository
from pharia_studio_sdk.evaluation.dataset.studio_dataset_repository import StudioDatasetRepository

studio_client = StudioClient(PROJECT_NAME,studio_url=STUDIO_URL, auth_token=AA_TOKEN, create_project=True )
studio_benchmark_repository = StudioBenchmarkRepository(studio_client)
studio_dataset_repository = StudioDatasetRepository(studio_client=studio_client)


task = Task(...)
examples = [...]
evaluation_logic = EvaluationLogic(...)
aggregation_logic = AggregationLogic(...)

dataset = studio_dataset_repo.create_dataset(
    examples=examples,
    dataset_name="dataset_name",
    metadata={"description": "dataset_description"},
)

benchmark = studio_benchmark_repository.create_benchmark(
    dataset_id=dataset.id,
    eval_logic=evaluation_logic,
    aggregation_logic=aggregation_logic,
    name="benchmark_name",
    metadata={"key": "value"},
    description="benchmark_description",
)

benchmark.execute(
    task=task
    name="benchmark_name",
)

```


## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/Aleph-Alpha/pharia-studio-sdk/blob/main/CONTRIBUTING.md) for details on how to set up the development environment and submit changes.
