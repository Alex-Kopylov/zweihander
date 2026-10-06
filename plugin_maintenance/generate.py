"""Stage-1 runner: execute every plugin generator under `generators/`."""

import importlib
import pkgutil

from plugin_maintenance import generators


def run_generators() -> list[str]:
    """Run each package's `generate()` under `generators/` in name order; return their names."""
    ran = []
    for module_info in sorted(pkgutil.iter_modules(generators.__path__), key=lambda info: info.name):
        module = importlib.import_module(f"{generators.__name__}.{module_info.name}")
        module.generate()
        ran.append(module_info.name)
    return ran


def main() -> None:
    """Run every generator and print the name of each one that ran."""
    for name in run_generators():
        print(f"generated: {name}")


if __name__ == "__main__":
    main()
