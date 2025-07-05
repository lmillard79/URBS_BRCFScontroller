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
from pathlib import Path
import folium
import altair as alt
from streamlit_folium import st_folium
from typing import Dict, Any, Optional, List, Tuple

# --- Configuration ---
PACKAGED_DATA_DIR = Path("packaged_data")

# --- Data Loading ---
@st.cache_data(show_spinner="Loading packaged data...")
def load_packaged_data() -> Dict[str, Any]:
    """
    Load all available packaged data files from the packaged_data directory.
    
    Returns:
        Dict containing loaded data with keys:
        - 'historical': Historical data if available
        - 'design': Design event data if available
        - 'models': Dict of additional model data
    """
    data = {
        'historical': None,
        'design_MC': None,
        'design_B15': None,
    }
    
    try:
        # Create packaged_data directory if it doesn't exist
        PACKAGED_DATA_DIR.mkdir(exist_ok=True)
        
        # Load historical data if exists
        hist_path = PACKAGED_DATA_DIR / "HISTORICAL_packaged_data.pkl.gz"
        if hist_path.exists():
            with gzip.open(hist_path, 'rb') as f:
                loaded = pickle.load(f)
                print(f"Loaded historical data type: {type(loaded)}")
                data['historical'] = loaded

        # Load design data if exists
        design_path = PACKAGED_DATA_DIR / "DESIGN_URBS_packaged_j_drive_data.pkl.gz"
        if design_path.exists():
            with gzip.open(design_path, 'rb') as f:
                loaded = pickle.load(f)
                print(f"Loaded design_MC data type: {type(loaded)}")
                data['design_MC'] = loaded
                
                # Debug: Print structure of design_MC
                if hasattr(loaded, 'keys'):
                    print(f"design_MC keys: {loaded.keys()}")
                if hasattr(loaded, 'shape'):  # If it's a DataFrame
                    print(f"design_MC columns: {loaded.columns.tolist() if hasattr(loaded, 'columns') else 'N/A'}")

        # Load B15 design data if exists
        design_b15_path = PACKAGED_DATA_DIR / "DESIGN_B15_flow_timeseries_2030_SSP2.pkl"
        if design_b15_path.exists():
            try:
                with open(design_b15_path, 'rb') as f:
                    loaded_df = pickle.load(f)
                
                print(f"Loaded design_B15 data type: {type(loaded_df)}")

                if isinstance(loaded_df, pd.DataFrame):
                    location_cols = [col for col in loaded_df.columns if str(col).startswith('RL_')]
                    if location_cols:
                        st.info("B15 data is in wide format. Restructuring...")
                        try:
                            id_vars = [col for col in loaded_df.columns if not str(col).startswith('RL_')]
                            long_df = pd.melt(loaded_df, id_vars=id_vars, value_vars=location_cols, var_name='location', value_name='flow_rate')
                            long_df['location'] = long_df['location'].str.split(' ').str[0]

                            # Replace -99999 with NaN
                            long_df['flow_rate'] = long_df['flow_rate'].replace(-99999, np.nan)
                            st.success("Replaced -99999 with NaN values.")

                            # Filter out Ensemble_ID == 1
                            if 'Ensemble_ID' in long_df.columns:
                                original_rows = len(long_df)
                                long_df = long_df[long_df['Ensemble_ID'] != 1].copy()
                                rows_removed = original_rows - len(long_df)
                                st.success(f"Filtered out Ensemble_ID 1, removing {rows_removed} rows.")
                            else:
                                st.warning("'Ensemble_ID' column not found for filtering.")

                            if 'TimeStep' in long_df.columns:
                                long_df['time_hours'] = (long_df['TimeStep'] - 1) * 0.25
                                st.success("Calculated 'time_hours' from 'TimeStep' with 0.25hr step.")
                            else:
                                st.warning("Could not find 'TimeStep' column to calculate time axis.")


                            data['design_B15'] = {'design_events': long_df}
                        except Exception as e:
                            st.error(f"Failed to restructure B15 data: {e}")
                            data['design_B15'] = {'design_events': loaded_df}
                    else:
                        st.info("B15 data appears to be in long format.")
                        data['design_B15'] = {'design_events': loaded_df}

                elif isinstance(loaded_df, dict):
                    data['design_B15'] = loaded_df
                else:
                    st.warning(f"Loaded B15 data is of an unexpected type: {type(loaded_df)}")

            except Exception as e:
                st.error(f"Error loading or processing design_B15 data: {str(e)}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        st.error(f"Error loading packaged data: {str(e)}")    
              
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
        aep_col = 'AEP_Value'
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

def map_location_name(location: str, model_type: str) -> str:
    """Map location names between different model types if needed."""
    return location

# --- Page Implementations ---
def show_historic_event_ui(data, col1, col2):
    historic_events = data.get('historic_events', [])
    if not historic_events:
        st.warning("No historic events found in the data file.")
        return

    with col1:
        st.subheader("Historic Event")
        selected_event = st.selectbox("Select a Historic Calibration Event: (YYYYMMDD)", sorted(historic_events, reverse=True), key="historic_event_selector")
        show_no_dams = st.checkbox("Compare with 'No Dams' Scenario", value=True)

        # --- State Management & Buttons ---
        # Initialize state
        if 'show_historic_results' not in st.session_state:
            st.session_state.show_historic_results = False
        if 'historic_run_complete' not in st.session_state:
            st.session_state.historic_run_complete = False

        # If selection changes, reset state
        if 'historic_run_key' in st.session_state and st.session_state.historic_run_key != selected_event:
            st.session_state.show_historic_results = False
            st.session_state.historic_run_complete = False

        # --- Buttons ---
        if st.button("▶️ Run URBS", use_container_width=True, key="run_historic", type="primary"):
            st.session_state.historic_run_key = selected_event
            st.session_state.show_historic_results = True
            st.session_state.historic_run_complete = False  # Reset completion state on new run
            st.rerun()

        st.button("✅ Export to TUFLOW", use_container_width=True, key="export_historic", disabled=not st.session_state.get('historic_run_complete', False), type="primary")
        
        if st.button("🔄 Reset Model", use_container_width=True, key="reset_historic"):
            st.session_state.show_historic_results = False
            st.session_state.historic_run_complete = False
            if 'historic_run_key' in st.session_state:
                del st.session_state['historic_run_key']
            st.rerun()

    with col2:
        st.header("Event Data Analysis")
        if st.session_state.get('show_historic_results', False):
            # If run isn't complete yet, show spinner and simulate
            if not st.session_state.get('historic_run_complete', False):
                with st.spinner("Model running..."):
                    time.sleep(4)
                    st.session_state.historic_run_complete = True
                    st.rerun() # Rerun to show results and enable button

            # Display results now that run is complete
            event = st.session_state.historic_run_key
            st.success(f"Displaying data for Historic Event: **{event}**")
            
            st.subheader("Model Parameters")
            model_params_df = data['with_dams'][event]['params']
            if not model_params_df.empty:
                st.dataframe(model_params_df, use_container_width=True)

            timeseries_data = data['with_dams'][event]['timeseries']
            nodam_timeseries_data = data['no_dams'][event]['timeseries'] if show_no_dams else pd.DataFrame()

            if timeseries_data.empty:
                st.warning(f"Could not load base timeseries data for event: {event}")
                return

            tab1, tab2 = st.tabs(["📈 Time Series", "📊 Peak Flows"])

            with tab1:
                st.subheader("Flow Time Series Analysis")
                all_locs = sorted(list(set([c.split(' (')[0] for c in timeseries_data.columns if isinstance(c, str)])))
                selected_loc = st.selectbox("Select Location to Plot:", all_locs, key="historic_loc_selector")

                if selected_loc:
                    plot_df = pd.DataFrame(index=timeseries_data.index)
                    if f"{selected_loc} (R)" in timeseries_data: plot_df['Recorded'] = timeseries_data[f"{selected_loc} (R)"]
                    if f"{selected_loc} (C)" in timeseries_data: plot_df['Modelled (With Dams)'] = timeseries_data[f"{selected_loc} (C)"]
                    if not nodam_timeseries_data.empty and f"{selected_loc} (C)" in nodam_timeseries_data: plot_df['Modelled (No Dams)'] = nodam_timeseries_data[f"{selected_loc} (C)"]
                    if not plot_df.empty: st.line_chart(plot_df)

            with tab2:
                st.subheader("Peak Flows at Key Locations")
                numeric_ts_data = timeseries_data.select_dtypes(include='number')
                summary_df = pd.concat([
                    numeric_ts_data.filter(like='(R)').max().rename('Recorded'),
                    numeric_ts_data.filter(like='(C)').max().rename('Modelled (With Dams)')
                ], axis=1)

                if not nodam_timeseries_data.empty:
                    nodam_peaks = nodam_timeseries_data.select_dtypes(include='number').filter(like='(C)').max().rename('Modelled (No Dams)')
                    summary_df = pd.concat([summary_df, nodam_peaks], axis=1)

                summary_df.index.name = 'Location'
                summary_df.index = summary_df.index.str.replace(r' \(R\)| \(C\)', '', regex=True).str.strip()
                st.dataframe(summary_df.dropna(how='all').round(1), use_container_width=True)
        else:
            st.info("👈 Select a historic event and click 'Run URBS' to display results.")

def show_design_event_ui():
    """Displays the UI for selecting and visualizing design flood events."""
    col1, col2 = st.columns([1, 2])

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
                "Select Annual Exceedance Probability (AEP):",
                options=available_aeps,
                index=default_aep_index,
                format_func=lambda x: f"1 in {int(x)} AEP" if x else "",
                key='aep_selector'
            )
            st.session_state.selected_aep = selected_aep

        available_locations = get_available_locations(data, model_key, selected_aep)
        if not available_locations or len(available_locations) <= 1:
            st.warning("No locations found for the selected criteria.")
            display_name = None
            original_location = None
        else:
            try:
                default_loc_index = available_locations.index(st.session_state.get('selected_location_tuple', available_locations[0]))
            except (ValueError, TypeError):
                default_loc_index = 0

            selected_location_tuple = st.selectbox(
                "Select Location:",
                options=available_locations,
                index=default_loc_index,
                key='selected_location_tuple',
                format_func=lambda x: x[0]
            )

            if selected_location_tuple and len(selected_location_tuple) == 2 and selected_location_tuple[1]:
                display_name = selected_location_tuple[0]
                original_location = selected_location_tuple[1]
            else:
                display_name = None
                original_location = None

        if model_key == 'design_MC':
            climate_scenarios = get_available_climate_scenarios(data)
            if climate_scenarios:
                st.selectbox(
                    "Select Climate Scenario:",
                    options=climate_scenarios,
                    key='selected_climate_scenario'
                )
        
        elif model_key == 'design_B15':
            # Get current selections to filter the ensemble list dynamically
            selected_aep = st.session_state.get('selected_aep')
            selected_loc_tuple = st.session_state.get('selected_location_tuple')
            original_location = selected_loc_tuple[1] if selected_loc_tuple and len(selected_loc_tuple) > 1 else None

            ensembles = get_available_ensembles(data, selected_aep, original_location)
            
            if ensembles:
                st.selectbox(
                    "Select Ensemble ID:",
                    options=ensembles,
                    key='selected_ensemble_id'
                )
            else:
                st.info("Select an AEP and Location to see available ensembles.")

        if st.button("Run Analysis", key='run_analysis_button'):
            if model_key and selected_aep and original_location and selected_aep != "Select an AEP":
                st.session_state.design_run_key = (model_key, selected_aep, display_name)
                st.session_state.original_location_name = original_location
                st.session_state.show_results = True
                st.rerun()
            else:
                st.warning("Please ensure all selections are made before running the analysis.")
                st.session_state.show_results = False

    with col2:
        if st.session_state.get('show_results', False):
            display_design_results()
        else:
            st.info("👈 Select a model, AEP, and location, then click 'Run Analysis' to display results.")
            st.markdown("---")
            with st.expander("About Model Types"):
                st.markdown("""
                - **URBS Monte Carlo Design Runs**: Contains probabilistic design events from the URBS model
                - **Design Events**: Contains traditional design storm events
                
                Note: Location names may vary between model types. Each model type maintains its own location naming convention.
                """)

def display_design_results():
    """Display the design event results based on user selection."""
    if 'design_run_key' not in st.session_state or not st.session_state.design_run_key:
        return

    model_key, aep, location = st.session_state.design_run_key

    if not all([model_key, aep, location]):
        st.warning("Please complete your selection (Model, AEP, and Location).")
        return

    original_location = st.session_state.get('original_location_name', location)
    model_name_map = {key: name for name, key in get_available_models(st.session_state.packaged_data)}
    model_name = model_name_map.get(model_key, "Unknown Model")
    data = st.session_state.packaged_data
    
    selected_scenario = st.session_state.get('selected_climate_scenario')
    subheader_text = f"{model_name} - {location} (1 in {int(aep)} AEP)"
    if model_key == 'design_MC' and selected_scenario and selected_scenario != "Select a scenario":
        subheader_text += f" - Scenario: {selected_scenario}"
    st.subheader(subheader_text)
    
    if model_key == 'design_MC':
        df = data.get('design_MC', {}).get('design_events')
        aep_col = 'aep'
    elif model_key == 'design_B15':
        df = data.get('design_B15', {}).get('design_events')
        aep_col = 'AEP_Value'  # Corrected column name
    else:
        st.error("Invalid model type selected.")
        return

    if df is None:
        st.error("No data available for the selected model.")
        return



    df_copy = df.copy()
    numeric_aep_col = 'numeric_aep_for_filter'

    def parse_aep_value(val):
        if isinstance(val, str):
            numbers = re.findall(r'\d+\.?\d*', val)
            if numbers:
                return float(numbers[-1])
        elif isinstance(val, (int, float, np.number)):
            return float(val)
        return np.nan

    if aep_col in df_copy.columns:
        df_copy[numeric_aep_col] = df_copy[aep_col].apply(parse_aep_value)
        filtered_data = df_copy[(df_copy[numeric_aep_col] == aep) & (df_copy['location'] == original_location)]

        # Also filter by climate scenario if applicable for Monte Carlo
        if model_key == 'design_MC':
            selected_scenario = st.session_state.get('selected_climate_scenario')
            if selected_scenario and selected_scenario != "Select a scenario":
                if 'climate_scenario_code' in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data['climate_scenario_code'] == selected_scenario]
                else:
                    st.warning("'climate_scenario_code' column not found for scenario filtering.")
    else:
        st.error(f"AEP column '{aep_col}' not found in the data for {model_name}.")
        return
    
    if filtered_data.empty:
        warning_message = f"No data found for AEP={aep} and Location='{original_location}'"
        if model_key == 'design_MC':
            selected_scenario = st.session_state.get('selected_climate_scenario')
            if selected_scenario and selected_scenario != "Select a scenario":
                warning_message += f" and Scenario='{selected_scenario}'"
        warning_message += "."
        st.warning(warning_message)
        return



    st.session_state.filtered_data = filtered_data
    
    if filtered_data.empty:
        st.warning("No data available for the selected criteria.")
        return

    tab1, tab2 = st.tabs(["📈 Time Series", "📄 Data Table"])

    with tab1:
        plot_data = filtered_data.copy()
        time_col_found = False
        
        # Case 1: Time information is in the index
        if plot_data.index.name in ['datetime', 'TimeStep', 'date', 'time', 'TimeStep_hrs'] and pd.api.types.is_datetime64_any_dtype(plot_data.index):
            time_col_found = True
            time_col = plot_data.index.name
            plot_data.index = pd.to_datetime(plot_data.index, errors='coerce')
            
        # Case 2: Time information is in a column
        else:
            time_col = next((col for col in ['datetime', 'time_hours', 'TimeStep', 'date', 'time'] if col in plot_data.columns), None)
            if time_col:
                time_col_found = True
                if time_col == 'time_hours':
                    # The 'time_hours' column is already numeric and represents hours.
                    # We can set it as index directly.
                    plot_data = plot_data.set_index(time_col)
                else:
                    plot_data[time_col] = pd.to_datetime(plot_data[time_col], errors='coerce')
                    plot_data = plot_data.set_index(time_col)

        flow_col = next((col for col in ['flow_rate', 'flow', 'value'] if col in plot_data.columns), None)

        if time_col_found and flow_col:
            plot_data.dropna(subset=[flow_col], inplace=True)
            plot_data[flow_col] = pd.to_numeric(plot_data[flow_col], errors='coerce')
            plot_data.dropna(subset=[flow_col], inplace=True)

            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("#### Peak Flow Distribution")
                if model_key == 'design_B15' and 'Ensemble_ID' in filtered_data.columns:
                    peak_flows = filtered_data.groupby('Ensemble_ID')[flow_col].max().reset_index()
                    
                    if not peak_flows.empty:
                        # Base chart for layering
                        base = alt.Chart(peak_flows)

                        # Box plot layer
                        boxplot = base.mark_boxplot(
                            extent='min-max',
                            size=50
                        ).encode(
                            y=alt.Y(f'{flow_col}:Q', title='Peak Flow (m³/s)')
                        )

                        # Jittered scatter plot layer for individual data points
                        points = base.mark_circle(
                            color='black',
                            size=20
                        ).encode(
                            x=alt.X('jitter:Q', title=None, axis=alt.Axis(grid=False, ticks=False, labels=False)),
                            y=alt.Y(f'{flow_col}:Q')
                        ).transform_calculate(
                            # Generate a random number between -1 and 1 for jitter
                            jitter='2 * random() - 1'
                        ).properties(
                            # Define the width of the jitter area
                            width=30
                        )

                        # Layer the charts
                        chart = (boxplot + points).properties(
                            title='Distribution of Peak Flows'
                        )
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.warning("No peak flow data to display in box plot.")
                else:
                    st.info("Box plot of peaks is available for B15 ensembles.")

            with col2:
                st.markdown("#### Flow Time Series")
                
                # Use a different variable for the line chart data to avoid modifying the original filtered data
                line_chart_data = plot_data
                if model_key == 'design_B15':
                    selected_ensemble = st.session_state.get('selected_ensemble_id')
                    if selected_ensemble:
                        # Filter the data for the line chart to the selected ensemble
                        line_chart_data = plot_data[plot_data['Ensemble_ID'] == selected_ensemble]
                        st.info(f"Showing time series for Ensemble {selected_ensemble}")
                    else:
                        st.warning("Select an ensemble to view its time series.")
                        line_chart_data = pd.DataFrame() # Clear the chart if no ensemble is selected

                if not line_chart_data.empty:
                    st.line_chart(line_chart_data[flow_col])
                elif model_key == 'design_B15':
                    st.info("Time series for the selected ensemble will be displayed here.")

        elif not time_col_found:
            st.warning("Could not find a suitable time column for plotting.")
        elif not flow_col:
            st.warning("Could not find a suitable flow/value column for plotting.")

    with tab2:
        # Exclude confusing columns from the data table view
        cols_to_drop = ['TimeStep', 'TimeStep_hrs', 'AEP_Years']
        display_df = filtered_data.drop(columns=[col for col in cols_to_drop if col in filtered_data.columns])
        st.dataframe(display_df, use_container_width=True)



def show_home_page(data):
    st.markdown("## An interface to run BRCFS URBS model and visualise model inputs and outputs.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Select a page from the sidebar to begin.")

    with col2:
        st.header("Project Overview")
        st.markdown("""
        This application provides a comprehensive interface for the URBS flood model.
        It allows for the analysis of both historic calibration events and synthetic design events.
        
        **Features:**
        - **Historic Event Analysis**: Compare recorded flow data against 'With Dams' and 'No Dams' scenarios.
        - **Design Event Analysis**: Filter and  visualise results from various design storms based on AEP, duration, and climate change scenarios.
        - **Interactive  visualisations**: Plot time series data and view peak flow summaries.
        - **Model Control**: Simulate model runs and export results for further analysis in tools like TUFLOW.
        """)

def add_geospatial_to_map(m, file_path, layer_name=None):
    """Add a KMZ, KML, or Shapefile to a folium map."""
    try:                       
        # Add to map
        folium.GeoJson(file_path,               
            name=layer_name or os.path.basename(file_path),            
        ).add_to(m)
        return True
            
    except Exception as e:
        st.error(f"Error loading {file_path}: {str(e)}")
        return False

def show_map_page():
    st.header("Map")
    m = folium.Map(location=[-27.4705, 153.0260], zoom_start=10)

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
    else:
        st.warning(f"The '{geo_dir}' directory does not exist.")

    # --- Uploaded file ---
    if 'uploaded_spatial_file' in st.session_state and st.session_state.uploaded_spatial_file is not None:
        file_ext = os.path.splitext(st.session_state.uploaded_spatial_file.name)[1].lower()
        if file_ext in ('.kmz', '.kml', '.shp', '.geojson'):
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                tmp.write(st.session_state.uploaded_spatial_file.getvalue())
                tmp_path = tmp.name
            
            success = add_geospatial_to_map(m, tmp_path, "Uploaded Layer")
            os.unlink(tmp_path)  # Clean up temp file
            
            if not success:
                st.error("Failed to process uploaded file. Ensure it's a valid spatial file.")
        else:
            st.error("Unsupported file format. Please upload a KMZ, KML, or Shapefile.")

    folium.LayerControl().add_to(m)
    st_folium(m, width=1500, height=700)

def show_upload_page():
    st.header("Upload Spatial Data")
    st.write("Upload a zipped shapefile (.zip) or a KML file (.kml) to display on the map.")

    # Initialize uploaded_spatial_file in session state if it doesn't exist
    if 'uploaded_spatial_file' not in st.session_state:
        st.session_state.uploaded_spatial_file = None

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['zip', 'kml', 'kmz', 'shp', 'geojson']
    )

    if uploaded_file is not None:
        st.session_state.uploaded_spatial_file = uploaded_file
        st.success(f"File '{uploaded_file.name}' uploaded successfully! Go to the 'Map' page to see it.")

def show_model_performance_page():
    import os
    st.header("Model Performance")
    log_file_path = "data/urbsout.log"

    st.subheader("Latest Model Run Details (Dummy Data)")
    st.markdown(f"""- **Last Model Run:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n- **Run Duration:** 23.1 seconds\n- **Status:** Success\n- **Errors:** None""")

    with st.expander("View Raw URBS Output Log (`urbsout.log`)"):
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                st.code(log_content, language='log')
            except Exception as e:
                st.error(f"An error occurred while reading the log file: {e}")
        else:
            st.warning(f"Log file not found at: {log_file_path}")

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

def show_feedback_page():
    st.header("User Feedback")
    st.write("We value your feedback! Please let us know your thoughts.")



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
        layout="wide",  # Can be "centered" or "wide"
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
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Historic Events", "Design Events", "Map", "Upload Data", "Model Performance", "Settings", "Feedback"]
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
            st.warning("No historical data available. Please check your packaged data files.")
    elif page == "Design Events":
        show_design_event_ui()
    elif page == "Map":
        show_map_page()
    elif page == "Upload Data":
        show_upload_page()
    elif page == "Model Performance":
        show_model_performance_page()
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