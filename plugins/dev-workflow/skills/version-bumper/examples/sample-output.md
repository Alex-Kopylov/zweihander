# Example: version-bumper output

## Discovery

```
$ python find_versions.py .
[
  {"file": "pyproject.toml", "version": "0.4.0", "line": 5, "pattern": "project", "reference": "references/python-project-files.md"},
  {"file": "src/myapp/main.py", "version": "0.4.0", "line": 8, "pattern": "fastapi", "reference": "references/fastapi-apps.md"},
  {"file": ".agents/plugins/marketplace.json", "version": "0.4.0", "line": 3, "pattern": "codex-marketplace-manifest", "reference": "references/codex-marketplace-manifests.md"},
  {"file": ".claude-plugin/marketplace.json", "version": "0.4.0", "line": 3, "pattern": "claude-code-marketplace-manifest", "reference": "references/claude-code-marketplace-manifests.md"},
  {"file": ".claude-plugin/plugin.json", "version": "0.4.0", "line": 3, "pattern": "claude-code-plugin-manifest", "reference": "references/claude-code-plugin-manifests.md"},
  {"file": ".codex-plugin/plugin.json", "version": "0.4.0", "line": 3, "pattern": "codex-plugin-manifest", "reference": "references/codex-plugin-manifests.md"}
]
```

## References loaded

```
references/python-project-files.md
references/fastapi-apps.md
references/codex-marketplace-manifests.md
references/claude-code-marketplace-manifests.md
references/claude-code-plugin-manifests.md
references/codex-plugin-manifests.md
```

## Confirmation prompt

```
Current version: 0.4.0
Target version:  0.5.0  (minor — detected `feat:` commits)

Files to update:
  - pyproject.toml:5
  - src/myapp/main.py:8
  - .agents/plugins/marketplace.json:3
  - .claude-plugin/marketplace.json:3
  - .claude-plugin/plugin.json:3
  - .codex-plugin/plugin.json:3

Proceed? [y/N]
```

## After bump

```
$ python find_versions.py .
[
  {"file": "pyproject.toml", "version": "0.5.0", "line": 5, "pattern": "project", "reference": "references/python-project-files.md"},
  {"file": "src/myapp/main.py", "version": "0.5.0", "line": 8, "pattern": "fastapi", "reference": "references/fastapi-apps.md"},
  {"file": ".agents/plugins/marketplace.json", "version": "0.5.0", "line": 3, "pattern": "codex-marketplace-manifest", "reference": "references/codex-marketplace-manifests.md"},
  {"file": ".claude-plugin/marketplace.json", "version": "0.5.0", "line": 3, "pattern": "claude-code-marketplace-manifest", "reference": "references/claude-code-marketplace-manifests.md"},
  {"file": ".claude-plugin/plugin.json", "version": "0.5.0", "line": 3, "pattern": "claude-code-plugin-manifest", "reference": "references/claude-code-plugin-manifests.md"},
  {"file": ".codex-plugin/plugin.json", "version": "0.5.0", "line": 3, "pattern": "codex-plugin-manifest", "reference": "references/codex-plugin-manifests.md"}
]
```
