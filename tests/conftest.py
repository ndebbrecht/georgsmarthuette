from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
import aiohttp

_ROOT = Path(__file__).parent.parent
_sources_path = _ROOT / "custom_components" / "georgsmarthuette" / "sources.py"

# Load sources.py directly, bypassing the package __init__.py which imports
# homeassistant (not available in the unit-test environment).
_spec = importlib.util.spec_from_file_location("georgsmarthuette_sources", _sources_path)
_sources_module = importlib.util.module_from_spec(_spec)
sys.modules["georgsmarthuette_sources"] = _sources_module  # needed by @dataclass(slots=True)
_spec.loader.exec_module(_sources_module)

sys.modules.setdefault("custom_components", ModuleType("custom_components"))
sys.modules.setdefault("custom_components.georgsmarthuette", ModuleType("custom_components.georgsmarthuette"))
sys.modules["custom_components.georgsmarthuette.sources"] = _sources_module


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as s:
        yield s
