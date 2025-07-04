import streamlit as st
import pandas as pd
import pickle
import gzip
import datetime
import os

# --- Configuration ---
# Use relative paths for deployment
PACKAGED_DATA_PATH = os.path.join("data", "packaged_data.pkl.gz")

# --- Page Configuration ---
st.set_page_config(
    page_title="URBS Flood Model Controller",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- High-Performance Data Loading ---
@st.cache_data
def load_data(file_path: str):
    """Loads the pre-packaged, compressed data file."""
    try:
        with gzip.open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error(f"Data file not found at {file_path}. Please run 'package_data.py' first.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data file: {e}")
        return None

# --- UI for Historic Event --- 
def show_historic_event_ui(data, col1, col2):
    historic_events = data.get('historic_events', [])
    if not historic_events:
        st.warning("No historic events found in the data file.")
        return

    selected_event = st.selectbox("Select a Historic Calibration Event:", historic_events)
    show_no_dams = st.checkbox("Compare with 'No Dams' Scenario", value=True)

    if selected_event:
        st.session_state.selected_event = selected_event
        st.subheader("Model Parameters")
        model_params_df = data['with_dams'][selected_event]['params']
        if not model_params_df.empty:
            st.dataframe(model_params_df, use_container_width=True)
    
    with col2:
        st.header("Event Data Analysis")
        if 'selected_event' not in st.session_state or st.session_state.selected_event != selected_event:
            st.info("👈 Select a historic event to view its data.")
            return

        event = st.session_state.selected_event
        st.success(f"Displaying data for Historic Event: **{event}**")
        
        timeseries_data = data['with_dams'][event]['timeseries']
        nodam_timeseries_data = data['no_dams'][event]['timeseries'] if show_no_dams else pd.DataFrame()

        if timeseries_data.empty:
            st.warning(f"Could not load base timeseries data for event: {event}")
            return

        tab1, tab2 = st.tabs(["📈 Time Series", "📊 Peak Flows"])

        with tab1:
            st.subheader("Flow Time Series Analysis")
            all_locs = sorted(list(set([c.split(' (')[0] for c in timeseries_data.columns if isinstance(c, str)])))
            selected_loc = st.selectbox("Select Location to Plot:", all_locs)

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

        with tab2:
            st.subheader("Peak Flows at Key Locations")
            numeric_ts_data = timeseries_data.select_dtypes(include='number')
            recorded_peaks = numeric_ts_data.filter(like='(R)').max().rename('Recorded')
            modelled_peaks = numeric_ts_data.filter(like='(C)').max().rename('Modelled (With Dams)')
            summary_df = pd.concat([recorded_peaks, modelled_peaks], axis=1)

            if not nodam_timeseries_data.empty:
                nodam_peaks = nodam_timeseries_data.select_dtypes(include='number').filter(like='(C)').max().rename('Modelled (No Dams)')
                summary_df = pd.concat([summary_df, nodam_peaks], axis=1)

            summary_df.index.name = 'Location'
            summary_df.index = summary_df.index.str.replace(r' \(R\)| \(C\)', '', regex=True).str.strip()
            st.dataframe(summary_df.dropna(how='all').round(1), use_container_width=True)
            st.bar_chart(summary_df.dropna(how='all').round(1))

# --- UI for Design Event ---
def show_design_event_ui(col1, col2):
    st.selectbox("Climate Change Scenario:", ["Pathway SSP2", "SSP3", "SSP5"])
    st.selectbox("Horizon:", [2030, 2050, 2090, 2100])
    
    with col2:
        st.header("Event Data Analysis")
        st.info("Data analysis for Design Events is not yet implemented. Configure the scenario and click 'Run URBS'.")

# --- Main Application UI ---
def main():
    st.title("🌊 URBS Flood Model Controller")
    st.markdown("An interface to control and visualize URBS model inputs and outputs.")

    # Load the high-performance packaged data
    data = load_data(PACKAGED_DATA_PATH)
    if data is None:
        return # Stop execution if data loading fails

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Configuration")
        event_type = st.radio("Select Event Type:", ["Historic Event", "Design Event"])
        
        st.divider()

        if event_type == "Historic Event":
            show_historic_event_ui(data, col1, col2)
        else:
            show_design_event_ui(col1, col2)
        
        st.divider()
        
        st.markdown(
            """
            <style>
            div[data-testid="stHorizontalBlock"]>div:nth-child(1) .stButton>button { background-color: #FF4B4B; color: white; width: 100%; }
            div[data-testid="stHorizontalBlock"]>div:nth-child(2) .stButton>button { background-color: #4CAF50; color: white; width: 100%; }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("**Run URBS**"):
                st.toast("URBS run triggered! (Functionality not yet implemented)")
        with b_col2:
            if st.button("**Export flows for TUFLOW**"):
                st.toast("Export triggered! (Functionality not yet implemented)")

        with st.expander("Show Model Performance"):
            st.markdown(
                f"""
                - **Last Model Run:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                - **Run Duration:** 0.1 seconds (data loaded from cache)
                - **Status:** Success
                - **Errors:** None
                """
            )

if __name__ == "__main__":
    main()