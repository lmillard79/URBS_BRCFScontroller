import streamlit as st
import pandas as pd
import numpy as np
import time
import gzip
import pickle
import datetime
import base64
import folium
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
        selected_event = st.selectbox("Select a Historic Calibration Event:", historic_events, key="historic_event_selector")
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
    """Displays the UI for selecting and visualizing design flood events."""
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
                all_locs = sorted(model_data['location'].dropna().unique())
                selected_loc = st.selectbox("Select Location to Plot:", all_locs, key="design_loc_selector")

                if selected_loc:
                    # Defensive check for the 'datetime' column
                    # The data should be indexed by datetime from the packaging script
                    if model_data.index.name == 'datetime':
                        plot_df = model_data[model_data['location'] == selected_loc]
                        if not plot_df.empty:
                            # Create the chart, Streamlit will use the index for the x-axis
                            st.line_chart(plot_df[['flow_rate']], use_container_width=True)
                        else:
                            st.warning(f"No timeseries data available for '{selected_loc}'.")
                    else:
                        # This case indicates a problem with how the data was packaged or loaded.
                        st.error("Critical Error: Data is not indexed by 'datetime' as expected.")

            with tab2:
                st.subheader("Peak Flows at All Locations")
                peak_flows = model_data.groupby('location')['flow_rate'].max().reset_index()
                peak_flows.rename(columns={'flow_rate': 'Peak Flow (m³/s)'}, inplace=True)
                st.dataframe(peak_flows.sort_values(by='Peak Flow (m³/s)', ascending=False).round(2), use_container_width=True, hide_index=True)
        else:
            st.info("👈 Select event criteria and click 'Run URBS' to display results.")


def show_home_page(data):
    st.markdown("## An interface to control and visualize URBS model inputs and outputs.")
    
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
        - **Design Event Analysis**: Filter and visualize results from various design storms based on AEP, duration, and climate change scenarios.
        - **Interactive Visualizations**: Plot time series data and view peak flow summaries.
        - **Model Control**: Simulate model runs and export results for further analysis in tools like TUFLOW.
        """)

def show_map_page():
    st.header("Map")
    m = folium.Map(location=[-27.4705, 153.0260], zoom_start=10)

    if st.session_state.uploaded_spatial_file is not None:
        try:
            file_bytes = io.BytesIO(st.session_state.uploaded_spatial_file.getvalue())
            gdf = gpd.read_file(file_bytes)

            if gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            folium.GeoJson(
                gdf,
                name='Uploaded Layer'
            ).add_to(m)

        except Exception as e:
            st.error(f"Could not read or display the uploaded file: {e}")

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
    st.subheader("Latest Model Run Details (Dummy Data)")
    st.markdown(f"""- **Last Model Run:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n- **Run Duration:** 0.1 seconds\n- **Status:** Success\n- **Errors:** None""")
    st.info("More detailed historical performance logs will be available here in the future.")

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

    st.set_page_config(page_title="URBS BRCFS Interface", page_icon="data/WRM_DROPLET.png", layout="wide")

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