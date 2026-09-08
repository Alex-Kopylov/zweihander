"""Stage-1 runner: execute every plugin generator under `generators/`."""

import importlib
import pkgutil

from plugin_maintenance import generators


def run_generators() -> list[str]:
    ran = []
    for module_info in sorted(
        pkgutil.iter_modules(generators.__path__), key=lambda info: info.name
    ):
        module = importlib.import_module(f"{generators.__name__}.{module_info.name}")
        module.generate()
        ran.append(module_info.name)
    return ran


def main() -> None:
    for name in run_generators():
        print(f"generated: {name}")


if __name__ == "__main__":
    main()
