# Example: version-bumper output

## Discovery

```
$ python find_versions.py .
[
  {"file": "pyproject.toml", "version": "0.4.0", "line": 5, "pattern": "project"},
  {"file": "src/myapp/main.py", "version": "0.4.0", "line": 8, "pattern": "fastapi"},
  {"file": ".claude-plugin/plugin.json", "version": "0.4.0", "line": 3, "pattern": "plugin"}
]
```

## Confirmation prompt

```
Current version: 0.4.0
Target version:  0.5.0  (minor — detected `feat:` commits)

Files to update:
  - pyproject.toml:5
  - src/myapp/main.py:8
  - .claude-plugin/plugin.json:3

Proceed? [y/N]
```

## After bump

```
$ python find_versions.py .
[
  {"file": "pyproject.toml", "version": "0.5.0", "line": 5, "pattern": "project"},
  {"file": "src/myapp/main.py", "version": "0.5.0", "line": 8, "pattern": "fastapi"},
  {"file": ".claude-plugin/plugin.json", "version": "0.5.0", "line": 3, "pattern": "plugin"}
]
```
