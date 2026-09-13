# Azure DevOps Pipelines for Redis Tests

[Azure Pipelines service containers](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/service-containers?view=azure-devops) can run Redis alongside tests. Choose an approach based on whether the job runs in a container.

## Container Job

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

## Host-Based Job

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
