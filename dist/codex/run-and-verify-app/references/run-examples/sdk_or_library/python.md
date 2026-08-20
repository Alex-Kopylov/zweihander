# Example: Python SDK / Library

Python libraries don't have a "run" step in the process sense. There is no
server to start and usually no CLI to invoke. For Python libraries, the run
skill is about:

1. **Building** the library from source
2. **Running the test suite**
3. **A minimal working example** that imports the package and proves it is
   installed correctly

Keep it brief. The template's Build and Test sections do most of the work.

## The smoke-test example

The main Python-specific addition is a tiny program or REPL snippet that
imports the library and does one real thing. This is how an agent confirms
"yes, the library is usable":

> ## Verify
>
> ```bash
> uv run python -c '
> from mylib import Client
> c = Client()
> print(c.ping())
> '
> # -> pong
> ```

## Example snippet

> ---
> name: run-mylib
> description: Build, install, and test mylib from source. Use when asked to verify mylib works, run its tests, or build a distribution.
> ---
>
> `mylib` is a Python library. "Running" it means building from source,
> executing the test suite, and importing it through the package boundary.
>
> ## Setup
>
> ```bash
> uv sync --extra dev
> ```
>
> ## Verify
>
> ```bash
> uv run python -c 'import mylib; print(mylib.__version__)'
> # -> 2.1.0
> ```
>
> ## Test
>
> ```bash
> uv run pytest
> ```
>
> Subset of tests: `uv run pytest tests/unit/`. With coverage:
> `uv run pytest --cov=mylib`.
>
> ## Build (distribution)
>
> ```bash
> uv run --with build python -m build
> # -> dist/mylib-2.1.0-py3-none-any.whl
> ```

## Things to consider documenting

- **Development mode vs installed mode.** `uv sync --extra dev` vs
  `uv pip install .` - if behavior differs, say which to use for what.
- **Optional dependencies.** `[dev]`, `[test]`, `[docs]` extras and when
  each is needed.
- **Generated code.** If there's a codegen step (protobuf, OpenAPI clients),
  document it. It is almost always missing from READMEs.
