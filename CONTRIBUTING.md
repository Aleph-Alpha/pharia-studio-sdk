# Contributing to pharia-studio-sdk

## Development Setup

### Prerequisites
- [uv](https://docs.astral.sh/uv/)
- Python 3.12

### Local Development Setup

```bash
uv venv
uv sync
uv run pre-commit install
```

### Running Tests

```bash
# make sure argilla is running
docker compose up -d

# run tests
uv run pytest
```
