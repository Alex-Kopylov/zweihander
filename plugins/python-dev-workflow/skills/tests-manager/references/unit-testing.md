# Unit Testing

## Scope

Write unit tests for local behavior: branches, guard clauses, validation,
exceptions, edge values, and service or handler decisions.

For endpoints, cover validation, auth/permission branches, service calls, error
mapping, and edge cases.

Place unit tests under the mirrored `tests/unit/...` path:

- `src/services/users/user.py` -> `tests/unit/services/users/test_user.py`
- `src/api/routes/users/user.py` -> `tests/unit/api/routes/users/test_user.py`
- Pydantic schemas -> mirrored `tests/unit/api/schemas/...`
- Persistence repositories and models -> mirrored `tests/unit/persistence/...`

## Boundaries

- Mock I/O boundaries, not pure functions.
- Mock database/cache clients, HTTP clients, filesystem, subprocesses, clocks,
  and third-party APIs at the client-factory or injected dependency level.
- Do not mock individual query strings or cache commands unless that operation
  is the behavior under test.
- Prefer dependency injection or patching the name used by the module under
  test.
- Do not create integration tests unless the caller explicitly requests both
  scopes; use `integration-test-writer` for that work.

## Assertions

- Verify output and observable behavior first.
- Assert calls only when the interaction itself is the contract.
- Use `pytest.raises(ExpectedError, match="...")` for exceptions.
- Use `unittest.mock` or `pytest-mock`; prefer `create_autospec()` when
  signatures matter.
- Freeze wall-clock time with `freezegun` or a narrow datetime patch.
- Avoid `time.sleep()` and `asyncio.sleep()` in tests.
