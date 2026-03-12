"""
Macro settings that can be imported and toggled. Internally, specific parts of the codebase rely on these settings
for determining core functionality.

To make sure global reference is maintained, should import these settings as:

`import robocasa.macros as macros`
"""

import os
from pathlib import Path

SHOW_SITES = False

# whether to print debugging information
VERBOSE = False

# Spacemouse settings. Used by SpaceMouse class in robosuite/devices/spacemouse.py
SPACEMOUSE_VENDOR_ID = 9583
SPACEMOUSE_PRODUCT_ID = 50741


def _load_dataset_base_path_from_pyproject():
    import tomllib

    for parent in Path(__file__).resolve().parents:
        pyproject_path = parent / "pyproject.toml"
        if not pyproject_path.exists():
            continue

        try:
            with pyproject_path.open("rb") as f:
                pyproject = tomllib.load(f)
        except Exception:
            continue

        tool_cfg = pyproject.get("tool", {})
        project_cfg = tool_cfg.get("robofab_robocasa", {})
        dataset_base_path = project_cfg.get("dataset_base_path")
        if isinstance(dataset_base_path, str) and dataset_base_path.strip():
            return dataset_base_path.strip()

    return None


_pyproject_dataset_base_path = _load_dataset_base_path_from_pyproject()
DATASET_BASE_PATH = _pyproject_dataset_base_path

try:
    from robocasa.macros_private import *
except ImportError:
    from robosuite.utils.log_utils import ROBOSUITE_DEFAULT_LOGGER

    import robocasa

    if DATASET_BASE_PATH is None:
        ROBOSUITE_DEFAULT_LOGGER.warn("No private macro file found!")
        ROBOSUITE_DEFAULT_LOGGER.warn("It is recommended to use a private macro file")
        ROBOSUITE_DEFAULT_LOGGER.warn(
            "To setup, run: python {}/scripts/setup_macros.py".format(robocasa.__path__[0])
        )
        ROBOSUITE_DEFAULT_LOGGER.warn(
            "Alternative: set ROBOCASA_DATASET_BASE_PATH or [tool.robofab_robocasa].dataset_base_path in pyproject.toml."
        )

if _pyproject_dataset_base_path:
    DATASET_BASE_PATH = _pyproject_dataset_base_path

_env_dataset_base_path = os.environ.get("ROBOCASA_DATASET_BASE_PATH")
if _env_dataset_base_path:
    DATASET_BASE_PATH = _env_dataset_base_path
