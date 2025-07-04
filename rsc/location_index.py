"""Utilities for mapping Monte-Carlo *location indices* to human-readable
names.

Historically the BRFS project reused the same numeric indices for many scripts.
The mapping was hard-coded in a few legacy helpers (see ``getMeta.py``).
Here we provide a single, modern source of truth so that new analysis code can
look up a gauge/area name from the plain integer index stored in the NumPy
arrays.

Usage
-----
>>> from load_results import ResultCollection
>>> from location_index import build_location_index, lookup_name
>>> rc = ResultCollection("rsc")
>>> rf = rc["DM_B15"]               # ResultFiles helper
>>> idx_map = build_location_index(rf)  # {0: 'Wivenhoe', 1: 'Glenore Grove', ...}
>>> lookup_name(0)  # 'Wivenhoe'
"""
from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# Canonical mapping extracted from the legacy *getMeta.py* helper.
# Several gauges share the same group/name – we store all possible indices.
# NOTE: The original script used *1-based* indices.  We convert them to *0-based*
#       here so they match the arrays in ``ResultFiles`` (Python/Numpy default).
# ---------------------------------------------------------------------------

_CANONICAL_MAPPING_LIST: List[tuple[str, List[int]]] = [
    ("Wivenhoe", [2]),
    ("Glenore Grove", [1, 3]),
    ("Savages", [4, 5]),
    ("Mount Crosby", [6, 7]),
    ("Walloon", [19, 20]),
    ("Amberley", [17]),
    ("Loamside", [18]),
    ("Ipswich", [24, 21, 23, 22, 25, 26]),
    ("Moggill", [8, 27]),
    ("Centenary", [9, 10, 28, 29]),
    ("Brisbane", [14, 12, 15, 16, 13, 11]),
]

# Build *0-based* dict → subtract 1 from each original index
_CANONICAL_MAPPING: Dict[int, str] = {
    idx - 1: name for name, group in _CANONICAL_MAPPING_LIST for idx in group
}

# ---------------------------------------------------------------------------

def lookup_name(index: int) -> str:
    """Return the human-readable gauge name for *index*.

    If the index is unknown, returns f"Loc{index}".
    """
    return _CANONICAL_MAPPING.get(index, f"Loc{index}")


def build_location_index(result_files) -> Dict[int, str]:
    """Return a mapping ``{index: name}`` for the *available* locations.

    *result_files* can be either a ``ResultFiles`` instance or a plain numpy
    array with shape ``[..., locations]``.  Only the indices that are actually
    present in the data are returned, so the dict is safe even for subsets.
    """
    # Try to infer the number of locations from the helper object or array.
    if hasattr(result_files, "npz"):
        sample = next(iter(result_files.npz.values()))  # any summary array
        n_locations = sample.shape[1]
    else:  # assume numpy array
        n_locations = result_files.shape[1]

    return {i: lookup_name(i) for i in range(n_locations)}
