from load_results import ResultCollection
from location_index import build_location_index
from plot_results import summary_by_duration, plot_timeseries

# Inspect available data
rc = ResultCollection(r"e:/GitHub/URBS_BRCFScontroller/rsc")
print(rc.scenarios)                 # → ['DM_B15', 'DM_CC1', ...]

rf = rc["DM_B15"]

idx_map = build_location_index(rf)
unique_map = {
    i: (name if list(idx_map.values()).count(name) == 1 else f"{name}_{i}")
    for i, name in idx_map.items()
}
print(unique_map)

# High-level summaries
summary_by_duration(rc, var="max_q", save="q_summary.png")           # interactive
summary_by_duration(rc, var="max_h", save="h_summary.png")

# Detailed time-series
plot_timeseries(rc,
                scenario="DM_B15",
                duration=3,
                event=3,
                location=2,
                save="timeseries.png")