# Mocking

Mocks isolate code from what is slow, external, or nondeterministic. They are
never the thing under test. Test what the code does, not what the mocks do.

## Boundaries

- Mock I/O boundaries, not pure functions.
- Mock database and cache clients, HTTP clients, the filesystem, subprocesses,
  clocks, and third-party APIs at the client-factory or injected-dependency
  level.
- Do not mock individual query strings or cache commands unless that operation
  is the behavior under test.
- Prefer dependency injection; otherwise patch the name where the module under
  test looks it up.
- Use `unittest.mock` or `pytest-mock`. Prefer `create_autospec()` or
  `autospec=True` so a mock fails when the real signature changes.
- Assert an interaction only when the interaction itself is the contract.
- For Redis, use fakeredis or a real server, never a hand-rolled mock; see
  [Redis](../domains/redis.md).

## Anti-pattern 1: Testing mock behavior

```python
# Bad: proves the mock was configured, not that registration works
def test_register_user_saves(mocker):
    repo = mocker.Mock()
    repo.save.return_value = True
    assert UserService(repo).register(user) is True
    repo.save.assert_called_once()
```

```python
# Good: a real in-memory repository, and an observable outcome
def test_register_user_is_retrievable():
    repo = InMemoryUserRepository()
    UserService(repo).register(user)
    assert repo.get(user.id) == user
```

Before asserting on a mock, ask whether the assertion checks real behavior or
only the mock. If only the mock, delete the assertion or stop mocking that
collaborator.

## Anti-pattern 2: Test-only methods in production

```python
# Bad: reset() exists only so tests can clean up
class TokenCache:
    def reset(self) -> None:
        self._tokens.clear()
```

```python
# Good: the fixture owns the lifecycle; production has no test hook
@pytest.fixture
def token_cache():
    return TokenCache()  # a fresh instance per test
```

Before adding a method to a production class, ask whether only tests call it.
If yes, put the cleanup in a fixture or test helper. Also ask whether the class
owns that resource's lifecycle; if not, the method belongs elsewhere.

## Anti-pattern 3: Mocking without understanding

```python
# Bad: the patched method also writes the config the duplicate check reads
def test_add_server_rejects_duplicate(mocker):
    mocker.patch("app.servers.catalog.discover_and_cache_tools")
    add_server(config)
    add_server(config)  # should raise, but the config was never written
```

```python
# Good: patch only the slow network call; the config write stays real
def test_add_server_rejects_duplicate(mocker):
    mocker.patch("app.servers.catalog.http_client.fetch_tools", return_value=[])
    add_server(config)
    with pytest.raises(DuplicateServerError):
        add_server(config)
```

Before mocking a method, list its side effects and check whether the test
depends on any of them. If it does, mock one level lower, at the actual slow or
external operation. If unsure, run the test against the real implementation
first, observe what it needs, then add the smallest mock at the right level.

## Anti-pattern 4: Incomplete mocks

```python
# Bad: only the fields this test reads; downstream code also reads metadata
response = {"status": "success", "data": {"user_id": "123"}}
```

```python
# Good: the complete documented structure
response = {
    "status": "success",
    "data": {"user_id": "123", "name": "Alice"},
    "metadata": {"request_id": "req-789", "timestamp": 1234567890},
}
```

A partial mock hides structural assumptions and passes while the real
integration fails. Build mock data from the real schema, a recorded response, or
the project's model type, and include every field the system may consume.

## When mocks become too complex

Warning signs:

- mock setup is longer than the test logic;
- everything is mocked to make the test pass;
- the mock lacks methods the real component has;
- the test breaks when the mock changes, not when behavior changes.

Ask whether a mock is needed at all. An integration test with real components
is often simpler than a complex mock; if the code must be mocked everywhere, it
is too coupled, and dependency injection is the fix.
