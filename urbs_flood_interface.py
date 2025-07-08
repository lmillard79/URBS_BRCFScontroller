import streamlit as st
import pandas as pd
import numpy as np
import time
import gzip
import pickle
import re
import datetime
import base64
import os
import requests
from pathlib import Path
import folium
import altair as alt
from streamlit_folium import st_folium
from typing import Dict, Any, Optional, List, Tuple

# --- Configuration ---
# Directory containing legacy pickled "packaged_data" files (kept for backwards-compatibility)
PACKAGED_DATA_DIR = Path("packaged_data")
# Directory containing modern parquet versions of the same datasets
PARQUET_DATA_DIR = Path("data_parquet")

# --- Data Loading ---
@st.cache_data(show_spinner="Loading packaged data (parquet/pickle)...")
def load_packaged_data() -> Dict[str, Any]:
    """Load model datasets from either **data_parquet** (preferred) or legacy
    **packaged_data** pickles so that the rest of the interface continues to
    work unchanged.

    The function builds a nested dict with the expected keys/structure:
        data = {
            'historical': {
                'historic_events': List[str],
                'with_dams': {event_id: {'params': DataFrame, 'timeseries': DataFrame}},
                'no_dams' :  { ... same structure ... }
            },
            'design_MC':  {'design_events': DataFrame},
            'design_B15': {'design_events': DataFrame}
        }
    Only the pieces that can be found are populated; missing parts are kept as
    ``None`` so that calling code can degrade gracefully.
    """
    data: Dict[str, Any] = {
        'historical': None,
        'design_MC': None,
        'design_B15': None,
    }

    # ------------------------------------------------------------------
    # 1️⃣  Prefer modern parquet files ----------------------------------
    # ------------------------------------------------------------------
    try:
        if PARQUET_DATA_DIR.exists():
            # ---- Monte-Carlo design events ---------------------------------
            mc_path = PARQUET_DATA_DIR / "design_mc.parquet"
            if mc_path.exists():
                df_mc = pd.read_parquet(mc_path)
                # Ensure categorical/text columns keep small memory footprint
                cat_cols = [c for c in df_mc.select_dtypes(include="object").columns if c not in ["datetime"]]
                for c in cat_cols:
                    df_mc[c] = df_mc[c].astype("category")
                data['design_MC'] = {'design_events': df_mc}

            # ---- B15 design events ----------------------------------------
            b15_path = PARQUET_DATA_DIR / "design_b15.parquet"
            if b15_path.exists():
                df_b15 = pd.read_parquet(b15_path)
                # Replace sentinel -99999 with NaN across all numeric cols
                num_cols = df_b15.select_dtypes(include=['number']).columns
                df_b15[num_cols] = df_b15[num_cols].replace(-99999, np.nan)
                # Harmonise column names with the rest of the app
                rename_map = {
                    'Location': 'location',
                    'flow': 'flow_rate',
                }
                df_b15 = df_b15.rename(columns=rename_map)
                if 'AEP_Value' in df_b15.columns:
                     # Convert probability (e.g., 0.01) to return-period years (e.g., 100)
                     df_b15['AEP_Years'] = (1.0 / df_b15['AEP_Value']).round(0).astype('Int64')
                data['design_B15'] = {'design_events': df_b15}

            # ---- Historical runs -----------------------------------------
            hist_events_p = PARQUET_DATA_DIR / "HISTORICAL_packaged_data_historic_events.parquet"
            if hist_events_p.exists():
                hist_events_df = pd.read_parquet(hist_events_p)
                # The parquet is just a single unnamed column – grab the values
                historic_events_list = hist_events_df.iloc[:, 0].astype(str).tolist()
            else:
                historic_events_list = []

            # Build nested dictionaries for each historic event using the new per-event parquet files
            if historic_events_list:
                with_dams_dict = {}
                no_dams_dict = {}
                for evt in historic_events_list:
                    evt = str(evt).strip()
                    # --- with dams ---
                    p_params = PARQUET_DATA_DIR / f"historic_with_dams_{evt}_params.parquet"
                    p_ts     = PARQUET_DATA_DIR / f"historic_with_dams_{evt}_timeseries.parquet"
                    evt_dict: Dict[str, Any] = {}
                    if p_params.exists():
                        evt_dict['params'] = pd.read_parquet(p_params)
                    if p_ts.exists():
                        evt_dict['timeseries'] = pd.read_parquet(p_ts)
                    if evt_dict:
                        with_dams_dict[evt] = evt_dict
                    # --- no dams ---
                    p_params_nd = PARQUET_DATA_DIR / f"historic_no_dams_{evt}_params.parquet"
                    p_ts_nd     = PARQUET_DATA_DIR / f"historic_no_dams_{evt}_timeseries.parquet"
                    evt_nd_dict: Dict[str, Any] = {}
                    if p_params_nd.exists():
                        evt_nd_dict['params'] = pd.read_parquet(p_params_nd)
                    if p_ts_nd.exists():
                        evt_nd_dict['timeseries'] = pd.read_parquet(p_ts_nd)
                    if evt_nd_dict:
                        no_dams_dict[evt] = evt_nd_dict
                data['historical'] = {
                    'historic_events': historic_events_list,
                    'with_dams': with_dams_dict,
                    'no_dams': no_dams_dict,
                }
            else:
                # Ensure 'historical' key exists to prevent NoneType errors downstream
                data['historical'] = {
                    'historic_events': [],
                    'with_dams': {},
                    'no_dams': {},
                }


    except Exception as e:
        st.warning(f"Parquet loading failed – falling back to pickles.\n{e}")

    # ------------------------------------------------------------------
    # 2️⃣  Fallback to legacy pickles ------------------------------------
    # ------------------------------------------------------------------
    # Only attempt the expensive pickle load if the above keys are still None
    try:
        if data['design_MC'] is None or data['design_B15'] is None or data['historical'] is None:
            PACKAGED_DATA_DIR.mkdir(exist_ok=True)

        # -- Monte-Carlo ---------------------------------------------------
        if data['design_MC'] is None:
            pkl_mc = PACKAGED_DATA_DIR / "DESIGN_URBS_packaged_j_drive_data.pkl.gz"
            if pkl_mc.exists():
                with gzip.open(pkl_mc, 'rb') as f:
                    data['design_MC'] = pickle.load(f)
                    if isinstance(data['design_MC'], pd.DataFrame):
                        data['design_MC'] = {'design_events': data['design_MC']}

        # -- B15 -----------------------------------------------------------
        if data['design_B15'] is None:
            pkl_b15 = PACKAGED_DATA_DIR / "DESIGN_B15_flow_timeseries_2030_SSP2.pkl"
            if pkl_b15.exists():
                with open(pkl_b15, 'rb') as f:
                    loaded_b15 = pickle.load(f)
                if isinstance(loaded_b15, pd.DataFrame):
                    data['design_B15'] = {'design_events': loaded_b15}
                else:
                    data['design_B15'] = loaded_b15  # assume already nested

        # -- Historical ----------------------------------------------------
        if data['historical'] is None:
            pkl_hist = PACKAGED_DATA_DIR / "HISTORICAL_packaged_data.pkl.gz"
            if pkl_hist.exists():
                with gzip.open(pkl_hist, 'rb') as f:
                    data['historical'] = pickle.load(f)

    except Exception as e:
        st.error(f"Error while loading legacy packaged data: {e}")

    return data

def get_available_models(data: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Get list of available models from the loaded data, ensuring they have valid data."""
    models = []
    
    # Check for URBS Monte Carlo Design Runs
    design_mc_data = data.get('design_MC', {})
    if isinstance(design_mc_data, dict):
        df_mc = design_mc_data.get('design_events')
        if isinstance(df_mc, pd.DataFrame) and not df_mc.empty:
            models.append(('URBS Monte Carlo Design Runs', 'design_MC'))
            
    # Check for B15 design events
    design_b15_data = data.get('design_B15')
    if design_b15_data:
        df_b15 = None
        if isinstance(design_b15_data, dict):
            df_b15 = design_b15_data.get('design_events')
        elif isinstance(design_b15_data, pd.DataFrame):
            df_b15 = design_b15_data
            # Ensure data is stored in the consistent dict structure
            data['design_B15'] = {'design_events': df_b15}
        
        if isinstance(df_b15, pd.DataFrame) and not df_b15.empty:
            # Avoid adding duplicates
            if not any(m[1] == 'design_B15' for m in models):
                 models.append(('URBS B15 Design Events', 'design_B15'))
            
    return models

def get_available_aeps(data: Dict[str, Any], model_type: str) -> List[float]:
    """Get available AEPs for the selected model type."""
    if model_type == 'design_MC':
        df = data.get('design_MC', {}).get('design_events')
        aep_col = 'aep'
    elif model_type == 'design_B15':
        df = data.get('design_B15', {}).get('design_events')
        # Prefer the years column if it exists, else use probability
        aep_col = 'AEP_Years' if df is not None and 'AEP_Years' in df.columns else 'AEP_Value'
    else:
        return []

    if df is None or aep_col not in df.columns:
        return []

    try:
        raw_aeps = df[aep_col].dropna().unique()
        aeps = set()
        for val in raw_aeps:
            if isinstance(val, str):
                # Extract numbers from strings like '1 in 100'
                numbers = re.findall(r'\d+\.?\d*', val)
                if numbers:
                    aeps.add(float(numbers[-1]))
            elif isinstance(val, (int, float, np.number)):
                aeps.add(float(val))
        
        return sorted(list(aeps))
    except Exception as e:
        st.error(f"An error occurred while processing AEP values: {e}")
        return []

def load_location_mappings(filepath: str = 'rsc/LocNames.txt') -> Dict[str, str]:
    """Loads location mappings from a file."""
    mappings = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip().strip('"')
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    key = parts[0]
                    value = parts[1]
                    mappings[value] = key # Map display name to original ID
    except FileNotFoundError:
        st.error(f"Location mapping file not found at: {filepath}")
    return mappings

def get_available_locations(data: Dict[str, Any], model_type: str, selected_aep: Optional[float] = None) -> List[Tuple[str, str]]:
    """Get available location names for a given model."""
    location_mappings = load_location_mappings()
    reverse_mappings = {v: k for k, v in location_mappings.items()}
    locations = set()
    
    df = None
    if model_type == 'design_MC':
        df = data.get('design_MC', {}).get('design_events')
    elif model_type == 'design_B15':
        df = data.get('design_B15', {}).get('design_events')
    
    if df is not None and 'location' in df.columns:
        locations.update(df['location'].dropna().unique())
        
    # Map to display names
    display_locations = []
    for loc_id in sorted(list(locations)):
        display_name = reverse_mappings.get(loc_id, loc_id.replace('_', ' ').title())
        display_locations.append((display_name, loc_id))
        
    return [("Select a location", "")] + display_locations

def get_available_climate_scenarios(data):
    """Extracts available climate scenarios from the MC design data."""
    df = data.get('design_MC', {}).get('design_events')
    if df is not None and 'climate_scenario_code' in df.columns:
        # Add a default option
        scenarios = ["Select a scenario"] + sorted(df['climate_scenario_code'].unique().tolist())
        return scenarios
    return []

def get_available_durations(data, aep, location):
    """Return sorted list of available storm durations (hours) for B15 model given AEP and location."""
    df = data.get('design_B15', {}).get('design_events')
    if df is None:
        return []

    # Identify duration column
    duration_col = next((c for c in df.columns if 'duration' in c.lower()), None)
    if duration_col is None:
        return []

    try:
        aep_int = int(aep)
    except (ValueError, TypeError):
        return []

    subset = df[(df.get('AEP_Years', df['AEP_Value']) == aep_int) & (df['location'] == location)]
    if subset.empty:
        return []

    return sorted(subset[duration_col].dropna().unique())


def get_available_storm_ids(data, aep, location, duration):
    """Return list of available Storm_IDs for given AEP, location and duration."""
    df = data.get('design_B15', {}).get('design_events')
    if df is None:
        return []

    duration_col = next((c for c in df.columns if 'duration' in c.lower()), None)
    storm_col = next((c for c in df.columns if 'storm' in c.lower() and 'id' in c.lower()), None)
    if duration_col is None or storm_col is None:
        return []

    try:
        aep_int = int(aep)
    except (ValueError, TypeError):
        return []

    subset = df[(df.get('AEP_Years', df['AEP_Value']) == aep_int) & (df['location'] == location) & (df[duration_col] == duration)]
    if subset.empty:
        return []

    return sorted(subset[storm_col].dropna().unique())


def get_available_ensembles(data, aep, location):
    """Extracts available ensemble IDs from the B15 design data for a given AEP and location."""
    if not all([aep, location, aep != "Select an AEP"]):
        return []
        
    df = data.get('design_B15', {}).get('design_events')
    if df is None or 'Ensemble_ID' not in df.columns or 'AEP_Years' not in df.columns or 'location' not in df.columns:
        return []
        
    try:
        aep_int = int(aep)
    except (ValueError, TypeError):
        return []

    filtered_df = df[(df['AEP_Years'] == aep_int) & (df['location'] == location)]
    
    if not filtered_df.empty:
        return sorted([int(e) for e in filtered_df['Ensemble_ID'].unique()])
    return []


def show_historic_event_ui(data, col1, col2):
    """UI and results display for historic calibration events."""
    # Sidebar debug toggle
    debug_mode_hist = st.sidebar.checkbox("🛠 Show Historic Data Debug", value=False)
    #LAM# st.subheader("🔍 Debug – Raw historical dictionary")
    #LAM# st.json(st.session_state.packaged_data.get('historical', {}))

    historic_events = data.get('historic_events', [])
    if not historic_events:
        st.warning("No historic events found in the data file.")
        return
    
    with col1:
        st.subheader("Historic Event")
        selected_event = st.selectbox(
            "Select a Historic Calibration Event: (YYYYMMDD)",
            sorted(historic_events, reverse=True),
            key="historic_event_selector",
        )
        show_no_dams = st.checkbox("Compare with 'No Dams' Scenario", value=True)

        # --- State Management & Buttons ---
        if 'show_historic_results' not in st.session_state:
            st.session_state.show_historic_results = False
        if 'historic_run_complete' not in st.session_state:
            st.session_state.historic_run_complete = False

        # Reset state if selection changes
        if st.session_state.get('historic_run_key') not in (None, selected_event):
            st.session_state.show_historic_results = False
            st.session_state.historic_run_complete = False

        # Run button -> simulate model run
        if st.button("▶️ Run URBS", use_container_width=True, key="run_historic", type="primary"):
            st.session_state.historic_run_key = selected_event
            st.session_state.show_historic_results = True
            st.session_state.historic_run_complete = False
            st.rerun()

        # Export button (enabled once run complete)
        st.button(
            "✅ Export to TUFLOW",
            use_container_width=True,
            key="export_historic",
            disabled=not st.session_state.get('historic_run_complete', False),
            type="primary",
        )
        
        # Reset button
        #if st.button("🔄 Reset Model", use_container_width=True, key="reset_historic"):
        #    st.session_state.show_historic_results = False
        #    st.session_state.historic_run_complete = False
        #    st.session_state.pop('historic_run_key', None)
        #    st.rerun()
        

    with col2:
        st.header("Event Data Analysis")
        if st.session_state.get('show_historic_results', False):
            # Simulate running time only once per run
            if not st.session_state.get('historic_run_complete', False):
                with st.spinner("Model running..."):
                    time.sleep(4)
                    st.session_state.historic_run_complete = True
                    st.rerun()

            event = st.session_state.historic_run_key
            st.success(f"Displaying data for Historic Event: **{event}**")

            st.subheader("Model Parameters")
            # Safely fetch params and timeseries for the selected event
            with_dams_dict = data.get('with_dams', {})
            event_data = with_dams_dict.get(event, {})
            model_params_df = event_data.get('params', pd.DataFrame())
            if not model_params_df.empty:
                st.dataframe(model_params_df, use_container_width=True)

            timeseries_data = event_data.get('timeseries', pd.DataFrame())
            nodam_timeseries_data = pd.DataFrame()
            if show_no_dams:
                nodam_timeseries_data = (
                    data.get('no_dams', {}).get(event, {}).get('timeseries', pd.DataFrame())
                )

            if timeseries_data.empty:
                st.warning(f"Could not load base timeseries data for event: {event}")
                if debug_mode_hist:
                    st.subheader("Debug – Available Data Objects (All Events)")
                    st.write("with_dams keys:", list(with_dams_dict.keys()))
                    st.write("no_dams keys:", list(data.get('no_dams', {}).keys()))

                    # Build a quick summary table of each event
                    summary_rows = []
                    for evt_key, evt_val in with_dams_dict.items():
                        params_shape = evt_val.get('params', pd.DataFrame()).shape
                        ts_shape = evt_val.get('timeseries', pd.DataFrame()).shape
                        summary_rows.append({
                            'Event': evt_key,
                            'Params rows': params_shape[0],
                            'Params cols': params_shape[1],
                            'TS rows': ts_shape[0],
                            'TS cols': ts_shape[1],
                        })
                    if summary_rows:
                        st.dataframe(pd.DataFrame(summary_rows))
                    else:
                        st.info("No with_dams event data found.")
                return

            tab1, tab2 = st.tabs(["📈 Time Series", "📊 Peak Flows"])

            # --- Time-series tab ---
            with tab1:
                st.subheader("Flow Time Series Analysis")
                all_locs = sorted({c.split(' (')[0] for c in timeseries_data.columns if isinstance(c, str)})
                selected_loc = st.selectbox("Select Location to Plot:", all_locs, key="historic_loc_selector")

                if selected_loc:
                    plot_df = pd.DataFrame(index=timeseries_data.index)
                    if f"{selected_loc} (R)" in timeseries_data:
                        plot_df['Recorded'] = timeseries_data[f"{selected_loc} (R)"]
                    if f"{selected_loc} (C)" in timeseries_data:
                        plot_df['Modelled (With Dams)'] = timeseries_data[f"{selected_loc} (C)"]
                    if not nodam_timeseries_data.empty and f"{selected_loc} (C)" in nodam_timeseries_data:
                        plot_df['Modelled (No Dams)'] = nodam_timeseries_data[f"{selected_loc} (C)"]
                    if not plot_df.empty:
                        st.line_chart(plot_df)

            # --- Peak-flows tab ---
            with tab2:
                st.subheader("Peak Flows at Key Locations")
                numeric_ts_data = timeseries_data.select_dtypes(include='number')
                summary_df = pd.concat(
                    [
                        numeric_ts_data.filter(like='(R)').max().rename('Recorded'),
                        numeric_ts_data.filter(like='(C)').max().rename('Modelled (With Dams)'),
                    ],
                    axis=1,
                )

                if not nodam_timeseries_data.empty:
                    nodam_peaks = (
                        nodam_timeseries_data.select_dtypes(include='number')
                        .filter(like='(C)')
                        .max()
                        .rename('Modelled (No Dams)')
                    )
                    summary_df = pd.concat([summary_df, nodam_peaks], axis=1)

                summary_df.index.name = 'Location'
                summary_df.index = summary_df.index.str.replace(r' \(R\)| \(C\)', '', regex=True).str.strip()
                st.dataframe(summary_df.dropna(how='all').round(1), use_container_width=True)
        else:
            st.info("👈 Select a historic event and click 'Run URBS' to display results.")

        # Optional debug panel when data available
        if debug_mode_hist and st.session_state.get('show_historic_results', False) and not timeseries_data.empty:
            with st.expander("🔍 Raw Historic Event Data (All Events)"):
                # Summary of all event data
                summary_rows = []
                for evt_key, evt_val in with_dams_dict.items():
                    params_shape = evt_val.get('params', pd.DataFrame()).shape
                    ts_shape = evt_val.get('timeseries', pd.DataFrame()).shape
                    summary_rows.append({
                        'Event': evt_key,
                        'Params rows': params_shape[0],
                        'Params cols': params_shape[1],
                        'TS rows': ts_shape[0],
                        'TS cols': ts_shape[1],
                    })
                if summary_rows:
                    st.subheader("Event Data Summary")
                    st.dataframe(pd.DataFrame(summary_rows))
                else:
                    st.info("No historic event data loaded in with_dams dict.")

                # Detailed view for selected event
                st.subheader(f"Selected Event – {event}")
                st.write("Model Parameters")
                st.dataframe(model_params_df.head(20))
                st.write("Timeseries sample")
                st.dataframe(timeseries_data.head(20))


def show_design_event_ui():
    """Displays the UI for selecting and visualizing design flood events."""
    col1, col2 = st.columns([1, 2])
    # Sidebar toggle to show raw data for debugging purposes
    debug_mode = st.sidebar.checkbox("🛠 Show Design Data Debug", value=False)

    if 'packaged_data' not in st.session_state:
        with st.spinner("Loading data..."):
            st.session_state.packaged_data = load_packaged_data()
    data = st.session_state.packaged_data

    with col1:
        st.subheader("Design Event Selection")

        available_models = get_available_models(data)
        if not available_models:
            st.warning("No model data available. Please upload data first.")
            return

        model_display_names = [m[0] for m in available_models]
        
        try:
            default_model_index = model_display_names.index(st.session_state.get('selected_model_display'))
        except (ValueError, TypeError):
            default_model_index = 0

        selected_model_display = st.selectbox(
            "Select Model Type:",
            options=model_display_names,
            index=default_model_index,
            key='model_selector'
        )
        st.session_state.selected_model_display = selected_model_display
        model_key = next((key for name, key in available_models if name == selected_model_display), None)

        available_aeps = get_available_aeps(data, model_key)
        if not available_aeps:
            st.warning(f"No AEP data available for {selected_model_display}.")
            selected_aep = None
        else:
            try:
                default_aep_index = available_aeps.index(st.session_state.get('selected_aep'))
            except (ValueError, TypeError):
                default_aep_index = 0
            selected_aep = st.selectbox(
                "Select AEP:",
                options=available_aeps,
                index=default_aep_index,
                format_func=lambda x: f"1 in {int(x)} AEP" if x else "",
                key='aep_selector'
            )
            st.session_state.selected_aep = selected_aep

        available_locations = get_available_locations(data, model_key, selected_aep)
        if not available_locations or len(available_locations) <= 1:
            st.warning(f"No location data available for {selected_model_display} with AEP {selected_aep}.")
            selected_location = None
        else:
            try:
                # Find index for default value
                loc_ids = [loc[1] for loc in available_locations]
                default_loc_index = loc_ids.index(st.session_state.get('selected_location_id'))
            except (ValueError, TypeError):
                default_loc_index = 0
            
            selected_location_display, selected_location_id = st.selectbox(
                "Select Location:",
                options=available_locations,
                index=default_loc_index,
                format_func=lambda x: x[0],
                key='location_selector'
            )
            st.session_state.selected_location_display = selected_location_display
            st.session_state.selected_location_id = selected_location_id

        # --- Duration selection for B15 ---
        selected_duration = None
        if model_key == 'design_B15' and selected_aep and selected_location_id:
            durations = get_available_durations(data, selected_aep, selected_location_id)
            if durations:
                selected_duration = st.selectbox("Select Storm Duration (hrs):", options=durations, key='duration_selector')

        # --- Storm ID selection for B15 ---
        selected_storm_id = None
        if model_key == 'design_B15' and selected_aep and selected_location_id and selected_duration is not None:
            storm_ids = get_available_storm_ids(data, selected_aep, selected_location_id, selected_duration)
            if storm_ids:
                selected_storm_id = st.selectbox("Select Storm ID:", options=storm_ids, key='stormid_selector')

        # --- Ensemble selection for B15 model ---
        selected_ensemble = None
        if model_key == 'design_B15' and selected_aep and selected_location_id:
            available_ensembles = get_available_ensembles(data, selected_aep, selected_location_id)
            #if available_ensembles:
            #    selected_ensemble = st.selectbox("Select Ensemble Member:", options=available_ensembles, key='ensemble_selector')

                # --- Duration & Ensemble for Monte Carlo model ---
        mc_selected_duration = None
        mc_selected_ensemble = None
        if model_key == 'design_MC' and selected_aep and selected_location_id:
            mc_durations = get_available_durations_mc(data, selected_aep, selected_location_id)
            if mc_durations:
                mc_selected_duration = st.selectbox("Select Storm Duration (hrs):", options=mc_durations, key='mc_duration_selector')
                mc_ensembles = get_available_ensembles_mc(data, selected_aep, selected_location_id, mc_selected_duration)
                if mc_ensembles:
                    mc_selected_ensemble = st.selectbox("Select Ensemble Member:", options=mc_ensembles, key='mc_ensemble_selector')
            
        # --- Climate scenario for MC model ---
        selected_climate_scenario = None
        if model_key == 'design_MC':
            available_scenarios = get_available_climate_scenarios(data)
            if available_scenarios:
                selected_climate_scenario = st.selectbox("Select Climate Pathway:", options=available_scenarios, key='climate_selector')

        # --- Determine current selection signature for change detection ---
        if model_key == 'design_MC':
            current_sig = (model_key, selected_aep, selected_location_id, mc_selected_duration, mc_selected_ensemble, selected_climate_scenario)
        else:  # design_B15
            current_sig = (model_key, selected_aep, selected_location_id, selected_duration, selected_storm_id, selected_ensemble)
        # Auto-reset results if any selector changed after a run
        if st.session_state.get('show_results') and current_sig != st.session_state.get('last_run_sig'):
            st.session_state.show_results = False

        # --- Buttons ---
        if st.button("▶️ Run URBS", use_container_width=True, key="run_design", type="primary"):
            # Simulate model run time
            with st.spinner("Running URBS model … please wait"):
                time.sleep(4)
            st.session_state.show_results = True
            st.session_state.last_run_sig = current_sig
            st.rerun()

        st.button("✅ Export to TUFLOW", use_container_width=True, key="export_design", disabled=not st.session_state.get('show_results', False), type="primary")
        
        
        #if st.button("🔄 Reset Model", use_container_width=True, key="reset_design"):
        #    st.session_state.show_results = False
        #    st.rerun()
        

    with col2:
        st.header("Design Event Analysis")
        if debug_mode and model_key in data and data[model_key]:
            st.info(f"Debug — raw dataframe for {model_key}")
            st.dataframe(data[model_key]['design_events'].head(200))
            st.write("Unique AEP values:", data[model_key]['design_events'].get('AEP_Value', data[model_key]['design_events'].get('aep')).unique() if 'design_events' in data[model_key] else None)

       
        if st.session_state.get('show_results', False):
            # Determine which duration/ensemble to pass based on model type
            dur_arg = mc_selected_duration if model_key == 'design_MC' else selected_duration
            ens_arg = mc_selected_ensemble if model_key == 'design_MC' else selected_ensemble
            display_design_results(
                 data=data,
                 model_key=model_key,
                 aep=selected_aep,
                 location_id=selected_location_id,
                 ensemble=ens_arg,
                 duration=dur_arg,
                storm_id=selected_storm_id,
                climate_scenario=selected_climate_scenario
            )
        else:
            st.info("👈 Select a design event and click 'Run URBS' to display results.")


def display_design_results(
    data: Dict[str, Any],
    model_key: str,
    aep: Optional[float],
    location_id: Optional[str],
    ensemble: Optional[int] = None,
    duration: Optional[float] = None,
    storm_id: Optional[int] = None,
    climate_scenario: Optional[str] = None
):
    """Display the design event results based on user selection."""
    if not all([model_key, aep, location_id]):
        st.warning("Please ensure Model, AEP, and Location are selected.")
        return

    df = data.get(model_key, {}).get('design_events')
    if df is None or df.empty:
        st.error(f"No data found for model: {model_key}")
        return

    st.subheader(f"Results for {st.session_state.selected_model_display}")
    st.markdown(f"**AEP:** `1 in {int(aep)}` | **Location:** `{st.session_state.selected_location_display}`")
    if ensemble:
        st.markdown(f"**Ensemble:** `{ensemble}`")
    if climate_scenario and climate_scenario != "Select a scenario":
        st.markdown(f"**Climate Scenario:** `{climate_scenario}`")

    # --- Filtering Logic ---
    def parse_aep_value(val):
        if isinstance(val, str):
            numbers = re.findall(r'\d+', val)
            return int(numbers[-1]) if numbers else None
        return val

    try:
        if model_key == 'design_MC':
            mask = (df['aep'].apply(parse_aep_value) == int(aep)) & (df['location'] == location_id)
            # duration filter
            dur_col = next((c for c in df.columns if 'duration' in c.lower()), None)
            if dur_col and duration is not None:
                mask &= (df[dur_col] == duration)
            # ensemble filter
            ens_col = next((c for c in df.columns if 'ensemble' in c.lower()), None)
            if ens_col and ensemble is not None:
                mask &= (df[ens_col] == ensemble)
            if climate_scenario and climate_scenario != "Select a scenario":
                mask &= (df['climate_scenario_code'] == climate_scenario)
        elif model_key == 'design_B15':
            mask = (df['AEP_Years'] == int(aep)) & (df['location'] == location_id)
            # add duration filter if column present and provided
            duration_col = next((c for c in df.columns if 'duration' in c.lower()), None)
            if duration_col and duration is not None:
                mask &= (df[duration_col] == duration)
            # add storm id filter
            storm_col = next((c for c in df.columns if 'storm' in c.lower() and 'id' in c.lower()), None)
            if storm_col and storm_id is not None:
                mask &= (df[storm_col] == storm_id)
            if ensemble:
                mask &= (df['Ensemble_ID'] == ensemble)
        else:
            st.error("Invalid model type selected.")
            return
    except Exception as e:
        st.error(f"Error during filtering: {e}")
        return

    event_df = df[mask]

    if event_df.empty:
        st.warning("No data found for the current selection.")
        st.write("Debug Info:")
        st.json({
            'model_key': model_key,
            'aep': aep,
            'location_id': location_id,
            'ensemble': ensemble,
            'climate_scenario': climate_scenario,
            'mask_sum': mask.sum() if 'mask' in locals() else 'N/A'
        })
        return

    # --- Create Plots ---
    st.markdown("### Hydrographs")
    
    # Use tabs for a cleaner layout
    tab2, tab1 = st.tabs(["Flow", "Water Level"])

    with tab2:
        if model_key == 'design_B15' and 'flow_rate' in event_df.columns:
            flow_df = event_df[['time_hours', 'flow_rate']].rename(columns={'flow_rate': 'Flow (m³/s)', 'time_hours': 'Time (hours)'})
            st.line_chart(flow_df.set_index('Time (hours)'))
        elif 'qts' in event_df.columns:
            qts_df = event_df[['time_hours', 'qts']].rename(columns={'qts': 'Flow (m³/s)', 'time_hours': 'Time (hours)'})
            st.line_chart(qts_df.set_index('Time (hours)'))
        elif 'flow_rate' in event_df.columns:
            fr_df = event_df[['time_hours', 'flow_rate']].rename(columns={'flow_rate': 'Flow (m³/s)', 'time_hours': 'Time (hours)'})
            st.line_chart(fr_df.set_index('Time (hours)'))
        else:
            st.info("No flow data available for this selection.")

    with tab1:
        if 'hts' in event_df.columns:
            hts_df = event_df[['time_hours', 'hts']].rename(columns={'hts': 'Water Level (m)', 'time_hours': 'Time (hours)'})
            st.line_chart(hts_df.set_index('Time (hours)'))
        else:
            st.info("Feature not yet implemented.")
    


    # --- Display Raw Data Table ---
    with st.expander("View Raw Data for Selection"):
        st.dataframe(event_df)



# --- Utility and Page Setup Functions ---

def get_available_durations_mc(data, aep, location):
    """Return sorted list of available storm durations for Monte Carlo model."""
    df = data.get('design_MC', {}).get('design_events')
    if df is None:
        return []

    duration_col = next((c for c in df.columns if 'duration' in c.lower()), None)
    if duration_col is None:
        return []

    try:
        aep_val = float(aep) if aep else None
    except (ValueError, TypeError):
        return []

    subset = df[(df['aep'] == aep_val) & (df['location'] == location)] if aep_val else df[df['location'] == location]
    if subset.empty:
        return []

    return sorted(subset[duration_col].dropna().unique())

def get_available_ensembles_mc(data, aep, location, duration=None):
    """Return list of available ensemble members for Monte Carlo model given filters."""
    df = data.get('design_MC', {}).get('design_events')
    if df is None:
        return []

    ensemble_col = next((c for c in df.columns if 'ensemble' in c.lower()), None)
    if ensemble_col is None:
        return []

    filtered = df.copy()
    if aep:
        try:
            aep_val = float(aep)
            filtered = filtered[filtered['aep'] == aep_val]
        except (ValueError, TypeError):
            pass
    if location:
        filtered = filtered[filtered['location'] == location]
    if duration is not None:
        dur_col = next((c for c in df.columns if 'duration' in c.lower()), None)
        if dur_col:
            filtered = filtered[filtered[dur_col] == duration]

    if filtered.empty:
        return []

    return sorted(filtered[ensemble_col].dropna().unique())

def show_home_page(data):
    st.title("Welcome")
    st.subheader("A light-weight interface to the URBS model results")
    st.markdown("""
    This application provides a light-weight interface to run and analyse URBS flood models.
    
    **Getting Started:**
    1.  Use the **Navigation** sidebar to select a page.
    2.  **Historic Events:** View and compare with past flood events (with or without dams).
    3.  **Design Events:** Examine ensemble design event scenarios at any location for any configuration.
    4.  **Monte Carlo Events:** View any of the previously run Monte Carlo design event scenarios.
    5.  **Map:** View geospatial data related to the models.
    6.  **Upload Data:** Upload GIS or rainfall to include in bespoke analysis and compare with other models.
    7.  **Export URBS to TUFLOW:** Select and send URBS model run to TUFLOW
    
    *This application is currently under development and more features are being added.*
    """)
    
    ## st.header("Available Data")
    
        # Example: Display a log file
    file_path = "data/frontpage.md"
    st.subheader("An Introduction to this Web Application")

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            st.markdown(content)
        except Exception as e:
            st.error(f"An error occurred while reading the Front Page file: {e}")
    else:
        st.warning(f"Quick Start guide file not found at: {file_path}")
    
    
    
    


def add_geospatial_to_map(m, file_path, layer_name=None):
    """Add a KMZ, KML, or Shapefile to a folium map."""
    if not layer_name:
        layer_name = Path(file_path).stem
    
    try:
        folium.GeoJson(file_path, name=layer_name).add_to(m)
        return True
    except Exception as e:
        st.warning(f"Could not load {file_path}: {e}")
        return False

import json

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_gauge_layer(layer: int, bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict[str, Any]:
    """Fetch gauge layer (river=5, rain=4) as GeoJSON from BoM service.
    If *bbox* is provided it should be (min_lon, min_lat, max_lon, max_lat).
    """
    base = (
        "https://hosting-stg.wsapi-stg.cloud.bom.gov.au/arcgis/rest/services/"
        "flood/National_Flood_Gauge_Network/MapServer/{}/query".format(layer)
    )
    params = {
        "where": "1=1",
        "outFields": "*",
        "outSR": 4326,
        "f": "geojson",
    }
    if bbox:
        xmin, ymin, xmax, ymax = bbox
        params.update(
            {
                "geometry": f"{xmin},{ymin},{xmax},{ymax}",
                "geometryType": "esriGeometryEnvelope",
                "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    return requests.get(base, params=params, timeout=60).json()

def show_map_page():
    st.header("Geospatial Map")
    st.info("This page displays river gauge locations (rain gauges hidden).")
    
    # SE QLD bbox including Toowoomba (lon/lat)
    brisbane_bbox = (151.5, -28.5, 153.4, -26.8)

    # Create map centred on Ipswich (approx) and still show wider SE QLD
    ipswich_center = [-27.62, 152.76]
    m = folium.Map(location=ipswich_center, zoom_start=9)
    # Optionally show full bbox for context – comment out if not desired
    # m.fit_bounds([[brisbane_bbox[1], brisbane_bbox[0]], [brisbane_bbox[3], brisbane_bbox[2]]])

    # --- Load all GeoJSON files from the geo folder ---
    geo_dir = "geo"
    if os.path.exists(geo_dir) and os.path.isdir(geo_dir):
        # Find all .geojson files in the geo directory
        geojson_files = [f for f in os.listdir(geo_dir) if f.lower().endswith('.geojson')]
        
        if not geojson_files:
            st.info("No GeoJSON files found in the 'geo' folder.")
        else:
            for geojson_file in geojson_files:
                file_path = os.path.join(geo_dir, geojson_file)
                layer_name = os.path.splitext(geojson_file)[0]  # Use filename without extension as layer name
                if not add_geospatial_to_map(m, file_path, layer_name):
                    st.warning(f"Could not load {geojson_file}")
    
    folium.LayerControl().add_to(m)

    # Fetch river and rain gauges within Brisbane bbox
    river_geo = fetch_gauge_layer(5, brisbane_bbox)
    # rain gauges disabled

    # Debug output
    river_count = len(river_geo.get("features", [])) if isinstance(river_geo, dict) else 0
    st.info(f"River gauges returned: {river_count}")

    # Using simple CircleMarker for ~<500 points for clarity
    for feat in river_geo.get("features", []):
        lon, lat = feat["geometry"]["coordinates"]
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.8,
            popup=feat["properties"].get("name", ""),
            tooltip=feat["properties"].get("name", "")
        ).add_to(m)

    # Display the map (explicit centre so Streamlit doesn’t override)
    st_folium(m, width=1200, height=600, center=[-27.62, 152.76], zoom=9)


def show_upload_page():
    st.header("Upload Data")
    st.info("Upload your own data for analysis.")
    
    uploaded_file = st.file_uploader("Choose a file")
    
    if uploaded_file is not None:
        st.success("File uploaded successfully!")
        # Add file processing logic here

def show_model_performance_page():
    st.header("Model Performance")
    st.info("This page will display model performance metrics when available.")
    
    # Example: Display a log file
    log_file_path = "data/urbsout.log"
    st.subheader("Model Run Log")
    
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r') as f:
                log_content = f.read()
            st.markdown(log_content)
        except Exception as e:
            st.error(f"An error occurred while reading the log file: {e}")
    else:
        st.warning(f"Log file not found at: {log_file_path}")
        
def show_quickstart_page():
    st.header("QuickStart guide")
    st.info("This page summarises the key concepts and usage cases.")
    
    # Example: Display a log file
    qst_file_path = "data/quickstart.md"
    st.subheader("A Guide to Using this Web Application Guide")
    
    if os.path.exists(qst_file_path):
        try:
            with open(qst_file_path, 'r') as f:
                qst_content = f.read()
            st.markdown(qst_content)
        except Exception as e:
            st.error(f"An error occurred while reading the Quick Start guide file: {e}")
    else:
        st.warning(f"Quick Start guide file not found at: {qst_file_path}")

def show_download_page():
    st.info("Options to download model results and exported data will be available here.")

def show_settings_page():
    st.header("URBS Model Settings")
    st.write("Update URBS switches here.") 
    genre = st.radio(
    "Enable URBS switches",
    ["URBS TFLW", "URBS ATKN", "URBS MATCH", "URBS BASEFLOW"],
    captions=[
        "Output TUFLOW csv.",
        "Use RAFTS settings in URBS.",
        "Match Gauge station flows.",
        "Enable Baseflow model."]
    
)
    st.info("Application settings and user preferences will be configured here.")

## LAM - added
import json
feedback_file = "feedback.json"

# Function to save feedback to a JSON file
def save_feedback(feedback_data):
    try:
        with open(feedback_file, "a") as f:
            json.dump(feedback_data, f)
            f.write(os.linesep)  # Add a newline for each entry
        st.success("Feedback saved successfully!")
    except Exception as e:
        st.error(f"Error saving feedback: {e}")

## LAM - end 

def show_feedback_page():
    """Simple feedback form collecting an email and message and storing in session state."""
    st.header("User Feedback")
    st.write("We value your feedback! Please let us know your thoughts below.")

    email = st.text_input("Your email address (optional):")
    feedback_text = st.text_area("Your feedback:")

    if st.button("Submit Feedback", use_container_width=True):
        if not feedback_text.strip():
            st.warning("Please enter some feedback before submitting.")
        else:
            entry = {
                "timestamp": datetime.datetime.now().isoformat(timespec='seconds'),
                "email": email.strip(),
                "feedback": feedback_text.strip(),
            }
            save_feedback(entry)
            # Store feedback locally in session state for this run; could be replaced with persisting to DB/email.
            st.session_state.setdefault("submitted_feedback", []).append(entry)
            st.success("Thank you for your feedback! 🙌")



def add_logo_to_page():
    with open("data/WRM_TAGLINE_POS.svg", "rb") as f:
        logo_svg = f.read()
    logo_b64 = base64.b64encode(logo_svg).decode()
    logo_html = f'''
    <style>
        .logo {{
            position: fixed;
            bottom: 10px;
            left: 320px;
            z-index: 1000;
        }}
    </style>
    <div class="logo">
        <img src="data:image/svg+xml;base64,{logo_b64}" width="450">
    </div>
    '''
    st.markdown(logo_html, unsafe_allow_html=True)

# --- Main Application Router ---
def main():
    # Clear any cached data
    st.cache_data.clear()
    
    # Set page config with WRM favicon
    st.set_page_config(
        page_title="WRM URBS Flood Model Interface",
        page_icon="./data/WRM_DROPLET.png",  # Path to your WRM favicon file
        layout="centered",  # Can be "centered" or "wide"
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for favicon in case the above doesn't work
    st.markdown(
        '''
        <link rel="icon" type="image/x-icon" href="./rsc/favicon.ico">
        <link rel="shortcut icon" type="image/x-icon" href="./rsc/favicon.ico">
        ''',
        unsafe_allow_html=True
    )
    
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = {}
    
    # Add logo to page
    add_logo_to_page()
    st.logo("./data/WRM_POS.png", size = "large", link = "https://www.wrmwater.com.au")
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Historic Events", "Design Events", "Map", "Model Performance", "QuickStart Guide", "Settings", "Feedback"]
    )
    
    # Page routing
    if page == "Home":
        show_home_page(st.session_state.data)
    elif page == "Historic Events":
        # Create columns for historic events
        col1, col2 = st.columns([1, 2])
        if 'historical' in st.session_state.get('packaged_data', {}):
            show_historic_event_ui(st.session_state.packaged_data['historical'], col1, col2)
        else:
            #st.warning("Historical data loading... Please wait.")
            #if 'packaged_data' not in st.session_state:
            with st.spinner("Loading data..."):
                st.session_state.packaged_data = load_packaged_data()
                show_historic_event_ui(st.session_state.packaged_data['historical'], col1, col2)

    elif page == "Design Events":
        show_design_event_ui()
    elif page == "Map":
        show_map_page()
    #elif page == "Upload Data":
    #    show_upload_page()
    elif page == "Model Performance":
        show_model_performance_page()
    elif page == "QuickStart Guide":
        show_quickstart_page()
    elif page == "Settings":
        show_settings_page()
    elif page == "Feedback":
        show_feedback_page()

if __name__ == "__main__":
    # Initialize session state for the design event UI
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None
    if 'selected_aep' not in st.session_state:
        st.session_state.selected_aep = None
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = None
    
    # Run the main app
    main()


