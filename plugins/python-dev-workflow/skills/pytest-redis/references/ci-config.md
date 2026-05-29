# CI/CD Configuration for Redis Tests

## GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --dev

      - name: Run unit tests (fakeredis, no Redis needed)
        run: uv run pytest tests/unit -v

      - name: Run integration tests (requires Redis service)
        env:
          REDIS_HOST: localhost
          REDIS_PORT: 6379
        run: uv run pytest tests/integration -v -m integration

      - name: Run with coverage
        env:
          REDIS_HOST: localhost
          REDIS_PORT: 6379
        run: uv run pytest tests/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

## GitLab CI

```yaml
# .gitlab-ci.yml
test:
  image: python:3.12
  services:
    - redis:7-alpine
  variables:
    REDIS_HOST: redis
    REDIS_PORT: "6379"
  before_script:
    - pip install uv
    - uv sync --dev
  script:
    - uv run pytest tests/ -v --cov=src
```

## Azure DevOps Pipelines

[Azure Pipelines service containers](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/service-containers?view=azure-devops) can run Redis alongside tests; choose an approach based on whether the job runs in a container.

### Container job (recommended)

In container jobs, services share a Docker network and resolve by name; no port mapping is needed.

```yaml
# azure-pipelines.yml
resources:
  containers:
    - container: python_build
      image: python:3.12
    - container: redis
      image: redis:7-alpine

pool:
  vmImage: ubuntu-latest

container: python_build
services:
  redis: redis

steps:
  - script: |
      pip install uv
      uv sync --dev
    displayName: Install dependencies

  - script: uv run pytest tests/unit -v
    displayName: Run unit tests (fakeredis)

  - script: uv run pytest tests/integration -v -m integration
    displayName: Run integration tests
    env:
      REDIS_HOST: redis
      REDIS_PORT: 6379
```

Inside the container job, `redis` resolves to the service container and ports are exposed without explicit `ports` mapping.

### Non-container job (host-based)

For host VM jobs, map the Redis port and connect via `localhost`.

```yaml
# azure-pipelines.yml
resources:
  containers:
    - container: redis
      image: redis:7-alpine
      ports:
        - 6379:6379

pool:
  vmImage: ubuntu-latest

services:
  redis: redis

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: "3.12"

  - script: |
      pip install uv
      uv sync --dev
    displayName: Install dependencies

  - script: uv run pytest tests/ -v --cov=src --cov-report=xml
    displayName: Run tests with coverage
    env:
      REDIS_HOST: localhost
      REDIS_PORT: 6379

  - task: PublishTestResults@2
    inputs:
      testResultsFormat: JUnit
      testResultsFiles: "**/junit.xml"
    condition: always()

  - task: PublishCodeCoverageResults@2
    inputs:
      codeCoverageTool: Cobertura
      summaryFileLocation: "**/coverage.xml"
    condition: always()
```

For dynamic port assignment, omit the host port (`ports: - 6379`) and read the assigned port from `$(agent.services.redis.ports.6379)`.

## Testcontainers (no service container needed)

With testcontainers, fixtures manage Redis; CI only needs Docker on the runner.

```yaml
# GitHub Actions -- testcontainers approach
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv python install
      - run: uv sync --dev
      - run: uv run pytest tests/ -v
```

Use generous CI startup timeouts; containers may take 10-30s on cold runners:

```python
@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as container:
        yield container
```

pytest-timeout can guard against hung containers:

```toml
# pyproject.toml
[tool.pytest.ini_options]
timeout = 120
```
