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
# make sure jaeger is running
docker compose up -d

# run tests
uv run pytest
```

## Development Roadmap

### TODO
- [ ] Add build step (package and publish)
- [ ] add docs
- [x] Figure out what to do with `LimitedConcurrencyClient`
- [ ] setup renovatebot 
- [ ] setup CI/CD 
   - [ ] Add release-please 

## Code Quality
- [x] Ruff linting is enabled for code quality checks 
