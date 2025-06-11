# pharia-studio-sdk

Formally the `intelligence_layer/evaluation` package.

## Overview

The pharia-studio-sdk provides a set of tools for evaluating and benchmarking LLMs with the Studio applications.

## Installation
The SDK is published on [PyPI](#).

To add the SDK as a dependency to an existing project managed, run
```bash
pip install pharia-studio-sdk
```

## Usage

```python
from pharia_studio_sdk.connectors.studio.studio_client import StudioClient

studio_client = StudioClient(PROJECT_NAME,studio_url=STUDIO_URL, auth_token=AA_TOKEN, create_project=True )
```






evaluator = Evaluator(
    model_name="gpt-4o-mini",
    model_provider="openai",
)

```


## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to set up the development environment and submit changes.
