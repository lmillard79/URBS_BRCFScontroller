"""rsc package – *light* stub.

All the legacy plotting/processing scripts originally lived in this package
and import a lot of compiled extensions (``LP_Data`` etc.).  Modern helper
modules such as ``load_results.py`` only need to reside *inside* the package –
they do **not** require those heavy dependencies.

To keep backward compatibility while allowing ``import rsc.load_results`` from
machines that lack the legacy DLLs, we *soft-import* the optional modules: we
create empty placeholders when they are missing instead of raising an error.
"""
from __future__ import annotations

import importlib
import sys
import types
from types import ModuleType
from typing import List

_OPTIONAL_MODULES: List[str] = [
    "LP_Data",
    "VM_LP",
    "LP_CP_Bank",
    "LP_Bridge_Deck",
    "LP_RP",
    "get_plot_name_testing",
    "eventFinder",
    "bris_utilities",
    "process_LP_Functionised_DM",
    "process_LP_ALL_AEPs_DM",
    "plotData",
]


def _soft_import(name: str) -> ModuleType:  # pragma: no cover – import shim
    try:
        return importlib.import_module(name)
    except ImportError:
        dummy = types.ModuleType(name)
        sys.modules[name] = dummy
        return dummy


for _m in _OPTIONAL_MODULES:
    _soft_import(_m)

# Minimal public surface -------------------------------------------------------
__all__ = []

