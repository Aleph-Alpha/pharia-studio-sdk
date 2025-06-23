# Core Concepts

## Evaluation

An important part of the Intelligence Layer is the tooling that helps to evaluate custom tasks. Evaluation helps to measures how well the implementation of a task performs given real world examples. The outcome of an entire evaluation process is an aggregated evaluation result that consists of metrics aggregated over all examples.

The evaluation process helps to:

- Optimize a task's implementation by comparing and verifying if changes improve the performance.
- Compare the performance of one implementation of a task with that of other (already existing) implementations.
- Compare the performance of models for a given task implementation.
- Verify how changes to the environment (such as a new model version or new finetuning version) affect the performance of a task.

## Dataset

The basis of an evaluation is a set of examples for the specific task-type to be evaluated. A single `Example` consists of:

- an instance of the `Input` for the specific task, and
- optionally an _expected output_ that can be anything that makes sense in context of the specific evaluation.

For example, the expected output might be, in the case of a classification, the correct classification result. In the case of a Q&A, it could contain a _golden answer_. However, if an evaluation is only about comparing results with the results from other runs, the expected output could be empty.

To enable reproducibility of evaluations, datasets are immutable. A single dataset can be used to evaluate all tasks of the same type, that is, with the same `Input` and `Output` types.

## Evaluation Process

The Intelligence Layer supports different kinds of evaluation techniques. Most important are:

- Computing absolute metrics for a task where the aggregated result can be compared with results of previous result in a way that they can be ordered. Text classification could be a typical use case for this. In that case the aggregated result could contain metrics like accuracy which can easily compared with other aggregated results.
- Comparing the individual outputs of different runs (all based on the same dataset) in a single evaluation process and produce a ranking of all runs as an aggregated result. This technique is useful when it is hard to come up with an absolute metric to evaluate a single output, but it is easier to compare two different outputs and decide which one is better. A typical use case could be summarization.

To support these techniques the Intelligence Layer differentiates between three consecutive steps:

1. Run a task by feeding it all inputs of a dataset and collecting all outputs.
2. Evaluate the outputs of one or several runs and produce an evaluation result for each example. Typically a single run is evaluated if absolute metrics can be computed, and several runs are evaluated when the outputs of runs are to be compared.
3. Aggregate the evaluation results of one or several evaluation runs into a single object containing the aggregated metrics. Aggregating over several evaluation runs supports amending a previous comparison result with comparisons of new runs without the need to re-execute the previous comparisons again.

The following table shows how these three steps are represented in code:

| Step         | Executor     | Custom Logic       | Repository              |
| ------------ | ------------ | ------------------ | ----------------------- |
| 1. Run       | `Runner`     | `Task`             | `RunRepository`         |
| 2. Evaluate  | `Evaluator`  | `EvaluationLogic`  | `EvaluationRepository`  |
| 3. Aggregate | `Aggregator` | `AggregationLogic` | `AggregationRepository` |

The columns indicate the following:

- "Executor" lists concrete implementations provided by the Intelligence Layer.
- "Custom Logic" lists abstract classes that need to be implemented with the custom logic.
- "Repository" lists abstract classes for storing intermediate results. The Intelligence Layer provides different implementations for these. See the next section for details.

## Data Storage

During an evaluation process a lot of intermediate data is created before the final aggregated result can be produced. To avoid repeating expensive computations if new results are to be produced based on previous ones, all intermediate results are persisted. To do this, the different executor classes use the following repositories:

- The `DatasetRepository` offers methods to manage datasets. The `Runner` uses it to read all `Example`s of a dataset and feeds them to the `Task`.
- The `RunRepository` is responsible for storing a task's output (in the form of an `ExampleOutput`) for each `Example` of a dataset which is created when a `Runner` runs a task using this dataset. At the end of a run a `RunOverview` is stored containing some metadata concerning the run. The `Evaluator` reads these outputs given a list of runs it needs to evaluate to create an evaluation result for each `Example` of the dataset.
- The `EvaluationRepository` enables the `Evaluator` to store the evaluation result (in the form of an `ExampleEvaluation`) for each example along with an `EvaluationOverview`. The `Aggregator` uses this repository to read the evaluation results.
- The `AggregationRepository` stores the `AggregationOverview` containing the aggregated metrics on request of the `Aggregator`.

The following diagrams illustrate how the different concepts play together in case of the different types of evaluations:

![PhariaStudio Absolute Evaluation](../_static/assets/studio-absolute-evaluation.drawio.svg)

1. The `Runner` reads the `Example`s of a dataset from the `DatasetRepository` and runs a `Task` for each `Example.input` to produce `Output`s.
2. Each `Output` is wrapped in an `ExampleOutput` and stored in the `RunRepository`.
3. The `Evaluator` reads the `ExampleOutput`s for a given run from the `RunRepository` and the corresponding `Example` from the `DatasetRepository` and uses the `EvaluationLogic` to compute an `Evaluation`.
4. Each `Evaluation` gets wrapped in an `ExampleEvaluation` and stored in the `EvaluationRepository`.
5. The `Aggregator` reads all `ExampleEvaluation`s for a given evaluation and feeds them to the `AggregationLogic` to produce an `AggregatedEvaluation`.
6. The `AggregatedEvalution` is wrapped in an `AggregationOverview` and stored in the `AggregationRepository`.

The following diagram illustrates the more complex case of a relative evaluation:

![PhariaStudio Relative Evaluation](../_static/assets/studio-relative-evaluation.drawio.svg)

1. Multiple `Runner`s read the same dataset and produce the corresponding `Output`s for different `Task`s.
2. For each run, all `Output`s are stored in the `RunRepository`.
3. The `Evaluator` gets as input previous evaluations (that were produced on the basis of the same dataset, but by different `Task`s) and the new runs of the current task.
4. Given the previous evaluations and the new runs the `Evaluator` can read the `ExampleOutput`s of both the new runs and the runs associated with previous evaluations, collect all that belong to a single `Example` and pass them along with the `Example` to the `EvaluationLogic` to compute an `Evaluation`.
5. Each `Evaluation` gets wrapped in an `ExampleEvaluation` and is stored in the `EvaluationRepository`.
6. The `Aggregator` reads all `ExampleEvaluation`s from all involved evaluations
   and feeds them to the `AggregationLogic` to produce an `AggregatedEvaluation`.
7. The `AggregatedEvalution` is wrapped in an `AggregationOverview` and stored in the `AggregationRepository`.