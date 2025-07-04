import streamlit as st
import pandas as pd
import numpy as np
import time
import gzip
import pickle
import datetime
import base64
import os
import folium

import altair as alt
from streamlit_folium import st_folium
#import geopandas as gpd
import io

from package_data import PACKAGED_DATA_PATH

# --- Configuration ---
# PACKAGED_DATA_PATH = "data/packaged_data.pkl.gz"

# --- Data Loading ---
@st.cache_data
def load_data():
    """Load the packaged data file, returning None if not found."""
    try:
        with gzip.open(PACKAGED_DATA_PATH, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error(f"The data file ({PACKAGED_DATA_PATH}) was not found. Please run `package_data.py` first.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data file: {e}")
        return None

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

def show_design_event_ui(data, col1, col2):
    """Displays the UI for selecting and  visualising design flood events."""
    df = data.get('design_events')
    if df is None or df.empty:
        st.warning("No design event data found in the packaged file.")
        return

    with col1:
        st.subheader("Filter Design Events")
        
        event_ids = sorted(df['event_id'].dropna().unique())
        scenarios = sorted(df['climate_scenario'].dropna().unique())
        
        selected_event_id = st.selectbox("Select Event (AEP - Duration - Ensemble):", event_ids, key="design_event_selector")
        selected_scenario = st.selectbox("Select Climate Scenario:", scenarios, key="design_scenario_selector")

        # --- State Management & Buttons ---
        run_key = f"{selected_event_id}_{selected_scenario}"
        if 'show_design_results' not in st.session_state:
            st.session_state.show_design_results = False
        if 'design_run_complete' not in st.session_state:
            st.session_state.design_run_complete = False

        if 'design_run_key' in st.session_state and st.session_state.design_run_key != run_key:
            st.session_state.show_design_results = False
            st.session_state.design_run_complete = False

        if st.button("▶️ Run URBS", use_container_width=True, key="run_design", type="primary"):
            st.session_state.design_run_key = run_key
            st.session_state.show_design_results = True
            st.session_state.design_run_complete = False
            st.rerun()

        st.button("✅ Export to TUFLOW", use_container_width=True, key="export_design", disabled=not st.session_state.get('design_run_complete', False), type="primary")

        if st.button("🔄 Reset Model", use_container_width=True, key="reset_design"):
            st.session_state.show_design_results = False
            st.session_state.design_run_complete = False
            if 'design_run_key' in st.session_state:
                del st.session_state['design_run_key']
            st.rerun()

    with col2:
        st.header("Event Data Analysis")
        if st.session_state.get('show_design_results', False):
            if not st.session_state.get('design_run_complete', False):
                with st.spinner("Model running..."):
                    time.sleep(4)
                    st.session_state.design_run_complete = True
                    st.rerun()

            # Filter the DataFrame based on the "run" selection
            run_event_id, run_scenario = st.session_state.design_run_key.rsplit('_', 1)
            filtered_df = df[
                (df['event_id'] == run_event_id) &
                (df['climate_scenario'] == run_scenario)
            ]

            if filtered_df.empty:
                st.warning("No models match the selected filter criteria.")
                return

            st.subheader("Available Model Runs & Parameters")
            param_cols = ['model_name', 'alpha', 'm', 'beta', 'il', 'cl']
            models_to_show = filtered_df[param_cols].drop_duplicates().set_index('model_name')
            st.dataframe(models_to_show, use_container_width=True)
            
            selected_model = st.selectbox("Select Model Run to Plot:", models_to_show.index, key="design_model_selector")

            if not selected_model:
                st.info("Select a model run to see the analysis.")
                return

            st.success(f"Displaying data for Model: **{selected_model}**")
            model_data = filtered_df[filtered_df['model_name'] == selected_model]

            tab1, tab2 = st.tabs(["📈 Time Series", "📊 Peak Flows"])

            with tab1:
                st.subheader("Flow Time Series Analysis")
                
                # Get location indices and map to human-readable names
                try:
                    from rsc.location_index import lookup_name
                    all_locs = sorted(model_data['location'].dropna().unique())
                    # Convert location indices to names, falling back to index if name not found
                    loc_names = {loc: lookup_name(int(loc)) if str(loc).isdigit() else loc for loc in all_locs}
                    # Sort locations by their human-readable names
                    sorted_locs = sorted(all_locs, key=lambda x: loc_names.get(x, str(x)))
                    
                    # Create mapping for display and selection
                    display_names = [f"{loc_names.get(loc, 'Unknown')} (ID: {loc})" for loc in sorted_locs]
                    loc_to_display = dict(zip(sorted_locs, display_names))
                    
                    selected_display = st.selectbox(
                        "Select Location to Plot:",
                        options=display_names,
                        key="design_loc_selector"
                    )
                    
                    # Extract the original location ID from the selected display name
                    selected_loc = next((loc for loc, name in loc_to_display.items() if name == selected_display), None)
                    
                    if selected_loc:
                        # Get the full data for the selected location
                        plot_data = model_data[model_data['location'] == selected_loc].copy()
                        
                        if not plot_data.empty and model_data.index.name == 'datetime':
                            # Get unique ensemble members
                            available_ensembles = sorted(plot_data['ensemble'].unique())
                            
                            # Add ensemble selector with on_change to trigger rerun
                            selected_ensemble = st.selectbox(
                                "Select Ensemble Member:",
                                options=available_ensembles,
                                format_func=lambda x: f"Ensemble {x}" if pd.notna(x) else "All Ensembles",
                                key=f"ensemble_selector_{selected_loc}",
                                on_change=lambda: st.session_state.update({"force_rerun": True})
                            )
                            
                            # Force a rerun if the ensemble selection changed
                            if st.session_state.get("force_rerun", False):
                                st.session_state["force_rerun"] = False
                                st.rerun()
                            
                            # Filter data by selected ensemble if not 'All'
                            if pd.notna(selected_ensemble):
                                plot_data = plot_data[plot_data['ensemble'] == selected_ensemble]
                            
                            # Create a clean DataFrame with flow rate and other relevant columns
                            plot_df = pd.DataFrame({
                                'datetime': plot_data.index,
                                'flow_rate_m3s': plot_data['flow_rate'].clip(lower=0),
                                'climate_scenario': plot_data.get('climate_scenario', ''),
                                'ensemble': plot_data.get('ensemble', ''),
                                'event_id': plot_data.get('event_id', '')
                            }).set_index('datetime')
                            
                            # Ensure unique datetime index and drop NA values
                            if plot_df.index.duplicated().any():
                                # If there are still duplicates (e.g., from multiple runs), take the first occurrence
                                plot_df = plot_df[~plot_df.index.duplicated(keep='first')]
                            
                            # Drop any rows with NA values in the flow rate column
                            plot_df = plot_df.dropna(subset=['flow_rate_m3s'])
                            
                            # Display the data table
                            st.subheader("Flow Time Series Data")
                            st.dataframe(plot_df, use_container_width=True)
                            
                            # Add download button for CSV
                            csv = plot_df.reset_index().to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"flow_data_location_{selected_loc}_ensemble_{selected_ensemble if pd.notna(selected_ensemble) else 'all'}.csv",
                                mime="text/csv",
                                key=f"download_{selected_loc}_{selected_ensemble}"
                            )
                            
                            # Create the chart with y-axis starting at 0
                            st.subheader("Flow Rate Visualization")
                            
                            # Get all ensemble data for background, excluding Ensemble 0
                            all_ensembles_data = model_data[
                                (model_data['location'] == selected_loc) & 
                                (model_data['ensemble'] != 0)  # Exclude Ensemble 0
                            ].copy()
                            all_ensembles_data = all_ensembles_data[~all_ensembles_data.index.duplicated(keep='first')]
                            all_ensembles_data = all_ensembles_data.dropna(subset=['flow_rate'])
                            
                            # Create a combined DataFrame with ensemble info
                            all_ensembles_df = pd.DataFrame({
                                'datetime': all_ensembles_data.index,
                                'flow_rate_m3s': all_ensembles_data['flow_rate'].clip(lower=0),
                                'ensemble': all_ensembles_data.get('ensemble', ''),
                                'is_selected': all_ensembles_data['ensemble'] == selected_ensemble if pd.notna(selected_ensemble) else True
                            })
                            
                            # Use Altair for more control over the plot
                            import altair as alt
                            
                            # Create base chart for background (all ensembles in light gray)
                            background = alt.Chart(all_ensembles_df).mark_line(
                                color='lightgray',
                                opacity=0.8,
                                strokeWidth=1
                            ).encode(
                                x=alt.X('datetime:T', title='Date/Time'),
                                y=alt.Y('flow_rate_m3s:Q', title='Flow Rate (m³/s)', scale=alt.Scale(zero=True)),
                                detail='ensemble:N'
                            )
                            
                            # Create the main chart for the selected ensemble
                            main_chart = alt.Chart(plot_df.reset_index()).mark_line(
                                color='steelblue',
                                strokeWidth=2
                            ).encode(
                                x=alt.X('datetime:T', title='Date/Time'),
                                y=alt.Y('flow_rate_m3s:Q', title='Flow Rate (m³/s)'),
                                tooltip=[
                                    alt.Tooltip('datetime:T', title='Date/Time', format='%Y-%m-%d %H:%M'),
                                    alt.Tooltip('flow_rate_m3s:Q', title='Flow Rate', format='.2f'),
                                    'ensemble:N',
                                    'climate_scenario:N',
                                    'event_id:N'
                                ]
                            )
                            
                            # Combine the charts
                            chart = (background + main_chart).properties(
                                width='container',
                                height=400
                            )
                            
                            # Add points for better interactivity on the main line only
                            points = main_chart.mark_point(size=50, opacity=0.1).encode(
                                opacity=alt.value(0.01)
                            )
                            
                            st.altair_chart(chart + points, use_container_width=True)
                            
                            # Add some stats
                            max_flow = plot_df['flow_rate_m3s'].max()
                            avg_flow = plot_df['flow_rate_m3s'].mean()
                            st.caption(f"Max flow: {max_flow:.1f} m³/s | Avg flow: {avg_flow:.1f} m³/s | Ensemble: {selected_ensemble if pd.notna(selected_ensemble) else 'All'}")
                        else:
                            st.warning(f"No timeseries data available for the selected location.")
                    else:
                        st.warning("Please select a valid location.")
                        
                except Exception as e:
                    st.error(f"Error loading location names: {str(e)}")
                    # Fallback to basic functionality
                    all_locs = sorted(model_data['location'].dropna().unique())
                    selected_loc = st.selectbox("Select Location to Plot:", all_locs, key="design_loc_selector_fallback")
                    
                    if selected_loc and model_data.index.name == 'datetime':
                        plot_df = model_data[model_data['location'] == selected_loc]
                        if not plot_df.empty:
                            st.line_chart(plot_df[['flow_rate']].clip(lower=0), use_container_width=True)
                        else:
                            st.warning(f"No timeseries data available for location {selected_loc}.")

            with tab2:
                st.subheader("Peak Flows at All Locations")
                # Table of max peak per location
                peak_table = model_data.groupby('location')['flow_rate'].max().reset_index()
                peak_table.rename(columns={'flow_rate': 'Peak Flow (m³/s)'}, inplace=True)
                st.dataframe(peak_table.sort_values(by='Peak Flow (m³/s)', ascending=False).round(2), use_container_width=True, hide_index=True)

                st.markdown("### Distribution of Ensemble Peaks (Box Plot)")
                # Compute peak per ensemble per location
                box_df = (
                    model_data.groupby(['location', 'ensemble'])['flow_rate']
                              .max()
                              .reset_index()
                )
                if not box_df.empty:
                    import altair as alt
                    chart = (
                        alt.Chart(box_df)
                            .mark_boxplot(extent='min-max')
                            .encode(
                                x=alt.X('location:N', title='Location'),
                                y=alt.Y('flow_rate:Q', title='Peak Flow (m³/s)'),
                                tooltip=['location', 'flow_rate']
                            )
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No ensemble peak data available for boxplot.")
        else:
            st.info("👈 Select event criteria and click 'Run URBS' to display results.")


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
    if st.session_state.uploaded_spatial_file is not None:
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

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['zip', 'kml']
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
    st.cache_data.clear()
    if 'uploaded_spatial_file' not in st.session_state:
        st.session_state.uploaded_spatial_file = None

    st.set_page_config(page_title="URBS Flood Interface", page_icon="data/WRM_DROPLET.png", layout="wide")

    # Custom CSS to make sidebar text white and bold
    st.markdown("""
    <style>
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label {
            color: white !important;
            font-weight: bold !important;
        }
    </style>
    """, unsafe_allow_html=True)

    data = load_data()
    if data is None:
        st.error("Could not load data file.")
        return

    PAGES = {
        "Home": show_home_page,
        "Historic Event": show_historic_event_ui,
        "Design Event": show_design_event_ui,

        "Map": show_map_page,
        "Upload": show_upload_page,
        "Model Performance": show_model_performance_page,
        "Download": show_download_page,
        "Settings": show_settings_page,
        "User Feedback": show_feedback_page,
    }

    with st.sidebar:
        st.title("Navigation")
        selection = st.radio("Go to", list(PAGES.keys()))

    page_func = PAGES[selection]

    # Call the selected page function with the correct arguments
    if selection in ["Historic Event", "Design Event"]:
        col1, col2 = st.columns([1, 2])
        page_func(data, col1, col2)
    elif selection == "Home":
        page_func(data)
    else:
        page_func()

    add_logo_to_page()

if __name__ == "__main__":
    main()