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

Azure Pipelines supports [service containers](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/service-containers?view=azure-devops) for running Redis alongside tests. Two approaches are available depending on whether the job itself runs in a container.

### Container job (recommended)

When the job runs inside a container, all services on the same Docker network resolve by name automatically -- no port mapping needed.

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

Inside the container job, the hostname `redis` resolves directly to the service container. All ports are exposed between containers on the same network without explicit `ports` mapping.

### Non-container job (host-based)

When the job runs directly on the host VM, explicit port mapping is required. The pipeline exposes the Redis port and the job connects via `localhost`.

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

When using testcontainers, the Redis instance is managed by the test fixtures. No CI service configuration is required -- only Docker must be available on the runner.

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

Set generous timeouts for container startup in CI (containers may take 10-30s on cold runners):

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
