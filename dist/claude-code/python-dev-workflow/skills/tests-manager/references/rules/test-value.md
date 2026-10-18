# Test Value

A test earns its maintenance cost only by protecting behavior, a credible
regression, or an independently meaningful contract. This file is the bar every
write, review, and audit step applies to each test.

## Value bar

Judge a test by its assertions, not its name. Before judging, read the complete
test, the production owner it exercises, that owner's entry point, callers,
callees, sibling implementations, overlapping tests, and relevant history. When
a test claims dependency-backed behavior, read the dependency's source or types.

Each contract has one primary test owner at the strongest boundary that can
observe it. Another layer earns its own test only for a distinct risk the owner
cannot reach, such as a transport, serialization, or lifecycle failure.

A test that breaks under behavior-preserving refactoring asserts implementation,
not behavior. A new one is rewritten at the owning boundary before it lands; an
existing one is suspect, not automatically deletable.

## Junk patterns

A match fails the authoring gate and is what review and audit hunt for, unless
the [retention bar](#retention-bar) names the contract the test independently
guards. Each heading is the pattern's stable id.

### assertion-free

The test calls code and asserts nothing, so it fails only on an exception.

```python
def test_build_report():
    build_report(orders)
```

### self-comparison

The expected value is the actual value, or a copy made by the same code path.

```python
assert model.model_dump() == model.model_dump()
```

### copied-inventory

The test hard-codes a list the code already declares, such as `__all__`,
registered routes, or a plugin registry, so it changes with every addition and
catches nothing.

```python
assert set(api.__all__) == {"create_user", "delete_user", "get_user"}
```

### source-grep

The test inspects source text, imports, or string literals instead of running
the behavior.

```python
assert "retry" in inspect.getsource(sync_orders)
```

### private-duplicate

The test pins a private predicate or call shape already proven through the
public boundary.

```python
assert order._is_valid() is True  # create_order() rejects invalid orders in its own test
```

### duplicate-contract

Two tests, or two `parametrize` rows, prove the same branch with the same kind
of input.

```python
@pytest.mark.parametrize("amount", [1, 2])  # both hit the same positive branch
def test_charge_positive_amount_succeeds(amount): ...
```

### shared-helper-replay

Each caller of a shared helper re-tests the helper's own behavior instead of
trusting its owner test.

```python
def test_stripe_adapter_formats_money(): assert format_money(Decimal("1")) == "1.00"
def test_paypal_adapter_formats_money(): assert format_money(Decimal("1")) == "1.00"
```

### test-only-seam

The test exists to keep a production hook alive that only tests need: an
export, flag, reset function, or injection parameter. See
[test-only methods in production](mocking.md#anti-pattern-2-test-only-methods-in-production).

```python
def test_reset_cache_clears_entries():
    cache.reset_cache_for_tests()
```

### test-only-production-code

Production code whose only callers are tests, kept alive by those tests.

```python
def test_legacy_parser_parses_v1(): assert legacy_parse_v1(raw) == expected  # no production caller
```

### oracle-from-subject

The expected value is produced by the code under test.

```python
assert render(invoice) == render(invoice_copy)
assert slugify(title) == slugify(title.strip())
```

### mock-implements-behavior

A mock's `side_effect` re-implements the logic the test claims to check, or one
identical mock stands in for different APIs.

```python
repo.get.side_effect = lambda user_id: users[user_id] if user_id in users else None
```

### mock-only-pass

The test asserts only that a mock returned its configured value or was called.
See [testing mock behavior](mocking.md#anti-pattern-1-testing-mock-behavior).

```python
repo.save.return_value = True
service.register(user)
repo.save.assert_called_once()
```

### fixture-supplies-outcome

A fixture pre-creates the state the code under test must produce, or the test
asserts persistence against a store the path never writes.

```python
def test_signup_creates_profile(db, profile):  # the fixture already inserted the profile
    signup(user)
    assert db.get(Profile, user.id)
```

### restated-flag

The test restates a declared setting instead of exercising the behavior the
setting promises.

```python
assert settings.retry_enabled is True
```

### unrelated-negative-control

A negative test passes for a reason other than the one it names, such as a
different guard raising first or a path production never reaches.

```python
with pytest.raises(ValueError):
    transfer(amount=-1, account=None)  # rejected by the account guard, not the amount guard
```

### overpromising-name

The name or fixture promises more than the assertions check.

```python
def test_close_session_clears_state():
    close_session(session)
    assert session.closed  # never checks the state
```

## Retention bar

Keep a test that independently enforces a public API, protocol, configuration,
migration, storage, security, platform, default-value, serialized-byte, package,
or architecture contract. Also keep:

- call ordering when the order is observable behavior;
- a regression test with a credible failure mode;
- source inspection when it is the cheapest independent guard: it fails when
  the contract changes (a user-facing key, byte, or path) and survives an
  identifier-only refactor;
- a test that fails on the baseline: treat it as a product-bug lead, reproduce
  it, and repair the owner instead of deleting the test.

Static or slow is not a reason to delete. A test that resembles implementation
may still be the only proof of a contract; show otherwise before removing it.

## Ledger marks

Review and audit record one mark per test declaration. A `parametrize` table is
one declaration unless its rows need different marks; then mark each row.

- `R` — retain: name the contract and the regression it catches. A test that
  only moves to a better file stays `R`, with the move noted.
- `F` — retain the contract but repair the test, such as a vacuous negative or
  an overpromising name; name the repair.
- `C` — consolidate: name the keeper that absorbs the assertion first, such as
  a sibling `parametrize` row or a stronger boundary suite.
- `D` — delete: name the proof that remains, or why no contract exists.
