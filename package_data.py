import pandas as pd
import pickle
import gzip
import os
from typing import List, Dict, Any

# --- Configuration ---
# Use relative paths so this script can be run from the project root
DATA_DIR = "data"
EXCEL_FILE_PATH = os.path.join(DATA_DIR, "URBS Historical v1.4 (Calibration).xlsm")
NO_DAMS_EXCEL_FILE_PATH = os.path.join(DATA_DIR, "URBS Historical v1.4 (No Dams).xlsm")
PACKAGED_DATA_PATH = os.path.join(DATA_DIR, "packaged_data.pkl.gz")

# --- Helper Functions to Read from Excel (similar to the main app) ---
def get_event_sheets(file_path: str) -> List[str]:
    """Gets all valid event sheet names from an Excel file."""
    try:
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        return [s for s in xls.sheet_names if s not in ['Peak Levels', 'Extract pqh']]
    except FileNotFoundError:
        print(f"Warning: File not found at {file_path}. Skipping.")
        return []

def get_parameters(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Reads model parameters for a given event sheet."""
    try:
        params_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=None, skiprows=10, nrows=7, usecols='A:H')
        params_df = params_df.iloc[:, [0, 2, 3, 5, 6]]
        params_df.columns = ['Model', 'alpha', 'beta', 'Initial Loss (mm)', 'Continuing Loss (mm/hr)']
        return params_df.set_index('Model').dropna().round(3)
    except Exception:
        return pd.DataFrame()

def get_timeseries(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Reads timeseries data for a given event sheet."""
    try:
        locations_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=None, skiprows=24, nrows=1, usecols='B:AJ')
        locations = locations_df.iloc[0].dropna().tolist()
        ts_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', skiprows=25, usecols='A:AJ')
        ts_df.columns = ['datetime'] + locations
        ts_df['datetime'] = pd.to_datetime(ts_df['datetime'], unit='D', origin='1899-12-30')
        return ts_df.set_index('datetime').dropna(how='all')
    except Exception:
        return pd.DataFrame()

# --- Main Packaging Logic ---
def package_data():
    """Reads all data from Excel files and packages it into a compressed pickle file."""
    print("Starting data packaging process...")
    
    packaged_data: Dict[str, Any] = {
        'with_dams': {},
        'no_dams': {},
        'historic_events': []
    }

    # Get the list of historic events from the main calibration file
    historic_events = get_event_sheets(EXCEL_FILE_PATH)
    if not historic_events:
        print("Error: No historic events found. Aborting.")
        return
    
    packaged_data['historic_events'] = historic_events
    print(f"Found {len(historic_events)} events to process.")

    # Process each event for both scenarios
    for event in historic_events:
        print(f"  - Processing event: {event}")
        # 'With Dams' scenario (from calibration file)
        params = get_parameters(EXCEL_FILE_PATH, event)
        timeseries = get_timeseries(EXCEL_FILE_PATH, event)
        packaged_data['with_dams'][event] = {'params': params, 'timeseries': timeseries}

        # 'No Dams' scenario
        nodam_timeseries = get_timeseries(NO_DAMS_EXCEL_FILE_PATH, event)
        packaged_data['no_dams'][event] = {'timeseries': nodam_timeseries}

    # Save the packaged data to a compressed file
    print(f"\nSaving packaged data to {PACKAGED_DATA_PATH}...")
    with gzip.open(PACKAGED_DATA_PATH, 'wb') as f:
        pickle.dump(packaged_data, f)
    
    print("\nPackaging complete! You can now run the Streamlit application.")

if __name__ == "__main__":
    # Ensure the data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    package_data()
