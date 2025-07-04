import streamlit as st
import pandas as pd
import pickle
import gzip
import datetime
import os
import folium
from streamlit_folium import st_folium

# --- Page Configuration (must be the first Streamlit command) ---
st.set_page_config(
    page_title="URBS Flood Model Controller",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuration ---
PACKAGED_DATA_PATH = os.path.join("data", "packaged_data.pkl.gz")

# --- High-Performance Data Loading ---
@st.cache_data
def load_data(file_path: str):
    """Loads the pre-packaged, compressed data file."""
    try:
        with gzip.open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
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

def show_design_event_ui(col1, col2):
    st.selectbox("Climate Change Scenario:", ["Pathway SSP2", "SSP3", "SSP5"])
    st.selectbox("Horizon:", [2030, 2050, 2090, 2100])
    
    st.divider()

    st.markdown(
        """<style>
        div[data-testid=\"stHorizontalBlock\"]>div:nth-child(1) .stButton>button { background-color: #FF4B4B; color: white; width: 100%; }
        div[data-testid=\"stHorizontalBlock\"]>div:nth-child(2) .stButton>button { background-color: #4CAF50; color: white; width: 100%; }
        </style>""",
        unsafe_allow_html=True
    )
    b_col1, b_col2 = st.columns(2)
    if b_col1.button("**Run URBS**"): st.toast("URBS run triggered! (Not implemented)")
    if b_col2.button("**Export flows for TUFLOW**"): st.toast("Export triggered! (Not implemented)")

    with col2:
        st.header("Event Data Analysis")
        st.info("Data analysis for Design Events is not yet implemented. Configure the scenario and click 'Run URBS'.")

def show_home_page(data):
    st.markdown("An interface to control and visualize URBS model inputs and outputs.")
    
    if data is None:
        st.error(f"Data file not found at '{PACKAGED_DATA_PATH}'.")
        st.info("Please run the `package_data.py` script from your terminal to generate the required data file.")
        st.code("python package_data.py")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("Configuration")
        event_type = st.radio("Select Event Type:", ["Historic Event", "Design Event"])
        st.divider()
        if event_type == "Historic Event":
            show_historic_event_ui(data, col1, col2)
        else:
            show_design_event_ui(col1, col2)

def show_map_page():
    st.subheader("Interactive Map of the Study Area")
    map_center = [-27.615, 152.758] # Ipswich
    m = folium.Map(location=map_center, zoom_start=9)
    #folium.Marker([-27.615, 152.758], popup="Ipswich", tooltip="Ipswich").add_to(m)
    #folium.Marker([-27.559, 151.951], popup="Toowoomba", tooltip="Toowoomba").add_to(m)
    #folium.Marker([-27.25, 153.3], popup="Moreton Bay", tooltip="Moreton Bay").add_to(m)
    st_folium(m, width=None, height=500, returned_objects=[])

def show_upload_page():
    st.info("Functionality to upload new model data files will be available here.")

def show_model_performance_page():
    st.subheader("Latest Model Run Details (Dummy Data)")
    st.markdown(f"""- **Last Model Run:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n- **Run Duration:** 0.1 seconds\n- **Status:** Success\n- **Errors:** None""")
    st.info("More detailed historical performance logs will be available here in the future.")

def show_download_page():
    st.info("Options to download model results and exported data will be available here.")

def show_settings_page():
    st.info("Application settings and user preferences will be configured here.")

def show_feedback_page():
    st.info("Provide your feedback to help us improve the application.")
    st.text_area("Your feedback:", key="feedback_text")
    if st.button("Submit Feedback"): st.toast("Thank you for your feedback!")

# --- Main Application Router ---
def main():
    page_options = {
        "Home": "🏠", "Map": "🗺️", "Upload": "📤", "Model Performance": "📈",
        "Download": "📥", "Settings": "⚙️", "User Feedback": "📧"
    }
    with st.sidebar:
        st.title("🌊 URBS Controller")
        page_labels = [f"{icon} {name}" for name, icon in page_options.items()]
        page_selection_label = st.radio("Navigation", page_labels, label_visibility="collapsed")
    
    selected_page_name = page_selection_label.split(" ", 1)[1]
    st.title(f"{page_options[selected_page_name]} {selected_page_name}")

    if selected_page_name == "Home":
        data = load_data(PACKAGED_DATA_PATH)
        show_home_page(data)
    elif selected_page_name == "Map": show_map_page()
    elif selected_page_name == "Upload": show_upload_page()
    elif selected_page_name == "Model Performance": show_model_performance_page()
    elif selected_page_name == "Download": show_download_page()
    elif selected_page_name == "Settings": show_settings_page()
    elif selected_page_name == "User Feedback": show_feedback_page()

if __name__ == "__main__":
    main()