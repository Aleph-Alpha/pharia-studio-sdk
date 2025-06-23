# Quick Start

This guide will help you get started with the Pharia Studio SDK quickly.

## Installation

The SDK is published on [PyPI](https://pypi.org/project/pharia-studio-sdk/).

```bash
pip install pharia-studio-sdk
```

## Basic Usage

Here's a complete example showing how to use the Pharia Studio SDK:

```python
from pharia_studio_sdk.connectors.studio.studio_client import StudioClient
from pharia_studio_sdk.evaluation.aggregation.aggregator import AggregationLogic
from pharia_studio_sdk.evaluation.evaluation.evaluator.evaluator import EvaluationLogic
from pharia_studio_sdk.evaluation.benchmark.studio_benchmark import StudioBenchmarkRepository
from pharia_studio_sdk.evaluation.dataset.studio_dataset_repository import StudioDatasetRepository

# Initialize the Studio client
studio_client = StudioClient(
    PROJECT_NAME, 
    studio_url=STUDIO_URL, 
    auth_token=AA_TOKEN, 
    create_project=True
)

# Create repositories
studio_benchmark_repository = StudioBenchmarkRepository(studio_client)
studio_dataset_repository = StudioDatasetRepository(studio_client=studio_client)

# Create dataset and benchmark
dataset = studio_dataset_repository.create_dataset(
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

# Execute benchmark
benchmark.execute(task=task, name="benchmark_name")
```

## Next Steps

- Explore the complete [API Reference](references) for detailed documentation
- Check out the [GitHub Repository](https://github.com/Aleph-Alpha/pharia-studio-sdk) for examples
- Visit the [PyPI Package](https://pypi.org/project/pharia-studio-sdk/) page for more information 