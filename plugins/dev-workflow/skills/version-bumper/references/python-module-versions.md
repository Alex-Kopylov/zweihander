# Python Module Version Constants

Use only when discovery reports `dunder`.

## Files

- `**/__init__.py`: update `__version__ = "X.Y.Z"`.

## Edit Rules

- Preserve quote style and surrounding module exports.
- Change only the `__version__` assignment.
- If package metadata also exists, keep the module constant aligned with the selected project version unless the user narrows the scope.
