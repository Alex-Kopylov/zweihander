# FastAPI App Versions

Use only when discovery reports `fastapi`.

## Files

- `**/app.py` or `**/main.py`: update the `version="X.Y.Z"` keyword passed to `FastAPI(...)` or the local app constructor.

## Edit Rules

- Preserve quote style and spacing around the keyword argument.
- Change only the application metadata version.
- Do not change API route prefixes, OpenAPI URLs, dependency pins, or generated client versions.
- If the app version mirrors project metadata, keep it aligned with the selected project version unless the user narrows the scope.
