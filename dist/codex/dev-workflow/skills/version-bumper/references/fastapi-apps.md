# FastAPI App Versions

Use only when discovery reports `fastapi`.

## Files

- `**/app.py` or `**/main.py`: update the `version="X.Y.Z"` keyword in `FastAPI(...)` or the local app constructor.

## Example

```python
from fastapi import FastAPI

app = FastAPI(
    title="Example Service",
    version="1.2.3",
)
```

If the app is built from a shared config object, update that object's `version`
field instead of introducing a second version constant. FastAPI treats this as
the application version, not the OpenAPI spec version.

## Edit Rules

- Preserve quote style and spacing around the keyword argument.
- Change only the application metadata version.
- Do not change API route prefixes, OpenAPI URLs, dependency pins, or generated client versions.
- If the app version mirrors project metadata, keep it aligned with the selected project version unless the user narrows the scope.
