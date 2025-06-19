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

## Example Usage
This example demonstrates how to define, run, and evaluate a custom task using the pharia-studio-sdk.
It serves as a reference point for creating your own evaluation logic with Pharia Studio.
Before running the example, make sure to set up the necessary configuration values: `STUDIO_URL`, `INFERENCE_URL`, and `AA_TOKEN`.

```python
from statistics import mean
from typing import Iterable

from aleph_alpha_client import Client
from pharia_inference_sdk.core import (
    CompleteInput,
    ControlModel,
    Llama3InstructModel,
    Task,
    TaskSpan,
)
from pydantic import BaseModel

from pharia_studio_sdk import StudioClient
from pharia_studio_sdk.evaluation import (
    AggregationLogic,
    Example,
    SingleOutputEvaluationLogic,
    StudioBenchmarkRepository,
    StudioDatasetRepository,
)

# Studio Configuration
PROJECT_NAME = "My first project"
BENCHMARK_NAME = "My first benchmark"
STUDIO_URL = "<studio_url>"

# Inference Configuration
INFERENCE_URL = "<inference_url>"
AA_TOKEN = "<aa_token>"

# Define a task with the `pharia-inference-sdk` module
class ExtractIngredientsTaskInput(BaseModel):
    recipe: str

class ExtractIngredientsTaskOutput(BaseModel):
    ingredients: list[str]

class ExtractIngredientsTask(Task[ExtractIngredientsTaskInput, ExtractIngredientsTaskOutput]):
    PROMPT_TEMPLATE = """Given the following recipe, extract the list of ingredients. Write one ingredient per line, do not add the quantity, do not add any text besides the list.

Recipe:
{recipe}
"""    
    def __init__(self, model: ControlModel):
        self._model = model


    def do_run(
            self, input: ExtractIngredientsTaskInput, task_span: TaskSpan
        ) -> ExtractIngredientsTaskOutput:
            
            prompt = self._model.to_instruct_prompt(
                self.PROMPT_TEMPLATE.format(recipe=input.recipe)
            )

            completion_input = CompleteInput(
                 prompt=prompt,
                 model=self._model)
            completion = self._model.complete(completion_input, tracer=task_span)
            ingredients = completion.completions[0].completion.split('\n')
            return ExtractIngredientsTaskOutput(ingredients=ingredients)

# Define a logic for evaluation
class IngredientsEvaluation(BaseModel):
    correct_number_of_ingredients: bool

class IngredientsAggregatedEvaluation(BaseModel):
    avg_result: float

class IngredientsEvaluationLogic(
    SingleOutputEvaluationLogic[
        ExtractIngredientsTaskInput,
        ExtractIngredientsTaskOutput,
        ExtractIngredientsTaskOutput,
        IngredientsEvaluation,
    ]
):
    def do_evaluate_single_output(
        self,
        example: Example[ExtractIngredientsTaskInput, ExtractIngredientsTaskOutput],
        output: ExtractIngredientsTaskOutput,
    ) -> IngredientsEvaluation:
        return IngredientsEvaluation(
            correct_number_of_ingredients=len(output.ingredients) == len(example.expected_output.ingredients),
        )
class IngredientsAggregationLogic(
    AggregationLogic[IngredientsEvaluation, IngredientsAggregatedEvaluation]
):
    def aggregate(
        self, evaluations: Iterable[IngredientsEvaluation]
    ) -> IngredientsAggregatedEvaluation:
        evaluation_list = list(evaluations)
        return IngredientsAggregatedEvaluation(
            avg_result=mean(evaluation.correct_number_of_ingredients for evaluation in evaluation_list)
        )

aa_client = Client(token=AA_TOKEN, host=INFERENCE_URL)
studio_client = StudioClient(PROJECT_NAME,studio_url=STUDIO_URL, auth_token=AA_TOKEN, create_project=True)
studio_benchmark_repository = StudioBenchmarkRepository(studio_client=studio_client)
studio_dataset_repository = StudioDatasetRepository(studio_client=studio_client)

evaluation_logic = IngredientsEvaluationLogic()
aggregation_logic = IngredientsAggregationLogic()

# Create a dataset with example inputs and expected outputs
examples = [   Example(
        input=ExtractIngredientsTaskInput(
            recipe="""# Pike Burger

- Pike (the bigger the better)
- Breadcrumbs
- Onions
- Garlic 
- Eggs
- Mustard
- Flour
- Spices
- Salt
- Pepper
- Oil

1. Fish pike
2. Filet fish into pieces
3. Grind the fish and onions into a paste
4. Mix paste with all other ingredients beside the flour and oil, add breadcrumbs until the consistency is right for forming patties
5. Form the paste into patties and coat them in flour
6. Let them rest in the fridge for 30min to firm up
7. Shallow fry them in a pan with a lot of oil
"""
        ),
        expected_output=ExtractIngredientsTaskOutput(
            ingredients=[
               "Pike", "Breadcrumbs", "Onions", "Garlic", "Eggs", "Mustard", "Flour", "Spices", "Salt", "Pepper", "Oil"
            ]
        ),
    )]
dataset = studio_dataset_repository.create_dataset(
    examples=examples,
    dataset_name="My first dataset",
    metadata={"description": "dataset_description"},
)

model = Llama3InstructModel(name="llama-3.1-8b-instruct", client=aa_client)
task = ExtractIngredientsTask(model=model)
# Create and run a benchmark
benchmark = studio_benchmark_repository.create_benchmark(
    dataset_id=dataset.id,
    eval_logic=evaluation_logic,
    aggregation_logic=aggregation_logic,
    name=BENCHMARK_NAME,
    metadata={"key": "value"},
)
benchmark.execute(
    task=task,
    name=BENCHMARK_NAME,
)

# Go see the benchmark result in PhariaStudio
```


## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/Aleph-Alpha/pharia-studio-sdk/blob/main/CONTRIBUTING.md) for details on how to set up the development environment and submit changes.
