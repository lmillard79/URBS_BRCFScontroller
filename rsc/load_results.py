"""Utility functions for loading and inspecting BRFS Monte-Carlo result
files (small summary .npz files and large time-series .pkl files).

The historic workflow that produced the data is quite involved and most of the
original processing / plotting code lives in the very large scripts
`process_MC_Results.py` and `plotData.py`.  They work, but are difficult to
navigate and reuse.  The helpers below provide a **much simpler public API** so
that new analysis notebooks or scripts only need a couple of lines of code to
get the raw numpy arrays / python objects.

Example
-------
>>> from load_results import ResultCollection
>>> rc = ResultCollection(r"e:/GitHub/URBS_BRCFScontroller/rsc")
>>> rc.scenarios
['DM_B15', 'DM_CC1', 'DM_CC2', 'DM_CC3', 'DM_CC4', 'DM_FF1']
>>> arr = rc["DM_B15"].npz["max_q"]        # summary peak flows [duration, location]
>>> ts_dict = rc["DM_B15"].timeseries      # dict with keys 'hts', 'qts', ...

The class lazily loads the heavy pickle file the first time you access
``.timeseries`` so the start-up cost is minimal.
"""
from __future__ import annotations

from pathlib import Path
import pickle
import re
from typing import Dict, List, Optional

import numpy as np

__all__ = [
    "ResultFiles",
    "ResultCollection",
]


class ResultFiles:
    """Wrapper around one *scenario* (e.g. ``DM_B15`` or ``DM_CC1``).

    Parameters
    ----------
    stem : str
        The filename *stem* without the extension.  Must have both a ``.npz``
        and a ``ts.pkl`` counterpart in the same directory, e.g.::

            DM_B15.npz
            DM_B15ts.pkl
    directory : Path | str
        Parent directory that contains the result files.
    """

    _SCENARIO_RE = re.compile(r"DM_(?P<code>[A-Z]+\d+)")

    def __init__(self, stem: str, directory: Path | str):
        self.stem = stem
        self.directory = Path(directory)
        self._npz: Optional[Dict[str, np.ndarray]] = None
        self._timeseries: Optional[dict] = None

        self.npz_path = self.directory / f"{stem}.npz"
        self.pkl_path = self.directory / f"{stem}ts.pkl"
        if not self.npz_path.exists():
            raise FileNotFoundError(self.npz_path)
        if not self.pkl_path.exists():
            raise FileNotFoundError(self.pkl_path)

    # ---------------------------------------------------------------------
    # Properties / lazy loaders
    # ---------------------------------------------------------------------

    @property
    def npz(self) -> Dict[str, np.ndarray]:
        """Return the *already-loaded* summary arrays.

        They are loaded once on first access and cached afterwards.
        """
        if self._npz is None:
            data = np.load(self.npz_path, allow_pickle=True)
            # ``np.load`` returns an *NpzFile* which behaves like a dict but we
            # turn it into an *actual* dict so that the underlying file can be
            # closed immediately (freeing the handle on Windows).
            self._npz = {k: data[k] for k in data.files}
        return self._npz

    # ------------------------------------------------------------------
    @property
    def timeseries(self) -> dict:
        """Return the time-series data stored in the heavy pickle file."""
        if self._timeseries is None:
            with open(self.pkl_path, "rb") as fp:
                # Pickle was produced with Python 2 → ASCII protocol.  The
                # *latin1* fallback keeps the binary blobs unchanged.
                self._timeseries = pickle.load(fp, encoding="latin1")
        return self._timeseries

    # ------------------------------------------------------------------
    @property
    def scenario(self) -> str:
        """Human-readable grouping: *Existing* vs *Future Climate*."""
        code = self._SCENARIO_RE.match(self.stem)
        if code and code.group("code").startswith("CC"):
            return "Future Climate"
        return "Existing Climate"

    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover – debug helper
        return f"<ResultFiles {self.stem!r} scenario={self.scenario}>"


class ResultCollection(dict):
    """Discover and lazily load all available scenarios in *directory*.

    ``ResultCollection`` behaves like a mapping::

        rc = ResultCollection("rsc")
        rc["DM_B15"].npz  # access scenario
    """

    def __init__(self, directory: Path | str):
        super().__init__()
        directory = Path(directory)
        stems = (
            f.stem for f in directory.glob("DM_*.npz") if (directory / f"{f.stem}ts.pkl").exists()
        )
        for stem in sorted(stems):
            self[stem] = ResultFiles(stem, directory)

    # Convenience helpers ------------------------------------------------- 
    @property
    def scenarios(self) -> List[str]:
        """Return a list of *scenario codes* found in the directory."""
        return list(self.keys())

    def by_climate(self, climate: str) -> List[ResultFiles]:
        """Filter results by *Existing Climate* or *Future Climate*."""
        valid = {"Existing Climate", "Future Climate"}
        if climate not in valid:
            raise ValueError(f"climate must be one of {valid}")
        return [rf for rf in self.values() if rf.scenario == climate]

