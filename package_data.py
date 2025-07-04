import os
import pandas as pd
import pickle
import gzip
from typing import List, Dict, Any
from pathlib import Path
from io import StringIO
import re

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
    """Reads timeseries data for a given event sheet, coercing data types."""
    try:
        locations_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=None, skiprows=24, nrows=1, usecols='B:AJ')
        locations = locations_df.iloc[0].dropna().tolist()
        ts_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', skiprows=25, usecols='A:AJ')
        ts_df.columns = ['datetime'] + locations

        # Coerce datetime column, turning errors into NaT (Not a Time)
        ts_df['datetime'] = pd.to_datetime(ts_df['datetime'], errors='coerce', unit='D', origin='1899-12-30')

        # Coerce all data columns to numeric, turning non-numeric values into NaN
        for col in locations:
            if col in ts_df.columns:
                ts_df[col] = pd.to_numeric(ts_df[col], errors='coerce')
        
        # Drop rows where the datetime is invalid or all data points are missing
        ts_df.dropna(subset=['datetime'], inplace=True)
        ts_df.dropna(subset=locations, how='all', inplace=True)
        
        return ts_df.set_index('datetime')
    except Exception as e:
        print(f"Warning: Could not process timeseries for sheet '{sheet_name}' in {os.path.basename(file_path)}. Error: {e}")
        return pd.DataFrame()

# --- Main Packaging Logic ---
DESIGN_EVENT_ROOT_PATH = r"J:\2078-01 Brisbane Valley Highway\Analysis\URBS\_Models\_ New"

def process_design_events(root_path: str, sample_size: int = None) -> pd.DataFrame:
    """
    Walks a directory structure to find and process post-processed URBS run CSVs.
    Extracts timeseries data, metadata from the folder structure, and model parameters.
    """
    print("\nStarting design event processing...")
    all_event_data = []
    
    csv_pattern = "**/9_postprocess/*.csv"
    
    root = Path(root_path)
    if not root.exists():
        print(f"Warning: Design event root path not found: {root_path}")
        return pd.DataFrame()

    found_files = list(root.glob(csv_pattern))
    if not found_files:
        print(f"Warning: No design event CSV files found in {root_path} using pattern {csv_pattern}")
        return pd.DataFrame()
        
    print(f"Found {len(found_files)} design event CSV files to process.")

    if sample_size:
        found_files = found_files[:sample_size]
        print(f"Processing a sample of {len(found_files)} files...")

    for csv_file in found_files:
        print(f"  - Processing file: {csv_file.name}")
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            start_index, end_index = -1, -1
            for i, line in enumerate(lines):
                if "Flow Rates" in line:
                    start_index = i
                elif "PARAMETER data" in line:
                    end_index = i
                    break
            
            if start_index == -1 or end_index == -1:
                print(f"    Warning: Could not find 'Flow Rates' or 'PARAMETER data' markers in {csv_file.name}. Skipping.")
                continue

            data_block_lines = lines[start_index : end_index]
            if not data_block_lines:
                print(f"    Warning: Data block is empty in {csv_file.name}. Skipping.")
                continue
            
            data_io = StringIO("".join(data_block_lines))
            # The first line of the block is the header, and the first column is the index
            ts_df = pd.read_csv(data_io, index_col=0)
            
            # Convert the Excel date index to datetime objects
            ts_df.index = pd.to_datetime(ts_df.index, errors='coerce', unit='D', origin='1899-12-30')
            ts_df.index.name = 'datetime'
            
            # Clean up column names (remove extra spaces, quotes, and suffixes)
            ts_df.columns = [col.strip().replace('"', '').replace('(C)', '').strip() for col in ts_df.columns]
            
            variable_name = csv_file.parts[-3]
            # Updated regex to capture AEP as a number and handle potential parsing errors
            match = re.search(r'(\d+h)_(\d+)_(\d+)Y_(.+)', variable_name)
            if not match:
                print(f"    Warning: Could not parse metadata from folder '{variable_name}'. Skipping.")
                continue
            
            duration, ensembleId, aep_str, climate_scenario = match.groups()
            try:
                aep = int(aep_str)
            except ValueError:
                print(f"    Warning: Could not convert AEP '{aep_str}' to integer. Skipping.")
                continue

            params_line = lines[-1].strip()
            param_pattern = re.compile(
                r"alpha=\s*([\d.]+)\s*"
                r"m=\s*([\d.]+)\s*"
                r"beta=\s*([\d.]+)\s*"
                r"IL=\s*([\d.]+)\s*"
                r"CL=\s*([\d.]+)"
            )
            param_match = param_pattern.search(params_line)

            if param_match:
                alpha, m, beta, il, cl = map(float, param_match.groups())
            else:
                print(f"    Warning: Could not parse parameters from line: {params_line}")
                alpha, m, beta, il, cl = [None] * 5

            melted_df = ts_df.melt(ignore_index=False, var_name='location', value_name='flow_rate')
            
            melted_df['model_name'] = csv_file.name
            melted_df['duration'] = duration
            melted_df['ensemble'] = ensembleId
            melted_df['aep'] = aep
            melted_df['climate_scenario_code'] = climate_scenario

            # Create a unique ID for the event type for easier selection in the UI
            melted_df['event_id'] = melted_df.apply(
                lambda row: f"{row['aep']} - {row['duration']} - {row['ensemble']}", axis=1
            )

            # Map climate scenarios to user-friendly names
            scenario_map = {
                'E': 'SSP2 2030',
                'CC2': 'SSP3 2070',
                'CC4': 'SSP5 2090'
            }
            melted_df['climate_scenario'] = melted_df['climate_scenario_code'].map(scenario_map).fillna(melted_df['climate_scenario_code'])
            melted_df['alpha'] = alpha
            melted_df['m'] = m
            melted_df['beta'] = beta
            melted_df['il'] = il
            melted_df['cl'] = cl
            
            all_event_data.append(melted_df)

        except Exception as e:
            print(f"    Error processing file {csv_file.name}: {e}")

    if not all_event_data:
        print("No design event data was successfully processed.")
        return pd.DataFrame()

    print("Consolidating all design event data...")
    final_df = pd.concat(all_event_data)
    print("Design event processing complete.")
    return final_df

def package_data():
    """Reads all data from Excel and CSV files and packages it into a compressed pickle file."""
    print("Starting data packaging process...")
    
    packaged_data: Dict[str, Any] = {
        'with_dams': {},
        'no_dams': {},
        'historic_events': [],
        'design_events': pd.DataFrame()
    }

    # --- 1. Process Historic Events ---
    print("\nProcessing historic events from Excel files...")
    historic_events = get_event_sheets(EXCEL_FILE_PATH)
    if not historic_events:
        print("Warning: No historic events found.")
    else:
        packaged_data['historic_events'] = historic_events
        print(f"Found {len(historic_events)} historic events to process.")
        for event in historic_events:
            print(f"  - Processing event: {event}")
            params = get_parameters(EXCEL_FILE_PATH, event)
            timeseries = get_timeseries(EXCEL_FILE_PATH, event)
            packaged_data['with_dams'][event] = {'params': params, 'timeseries': timeseries}
            nodam_timeseries = get_timeseries(NO_DAMS_EXCEL_FILE_PATH, event)
            packaged_data['no_dams'][event] = {'timeseries': nodam_timeseries}

    # --- 2. Process Design Events ---
    design_events_df = process_design_events(DESIGN_EVENT_ROOT_PATH)
    if not design_events_df.empty:
        packaged_data['design_events'] = design_events_df
        print(f"Successfully processed and added {len(design_events_df.index.unique())} rows of design event data.")

    # --- 3. Save Packaged Data ---
    print(f"\nSaving all packaged data to {PACKAGED_DATA_PATH}...")
    with gzip.open(PACKAGED_DATA_PATH, 'wb') as f:
        pickle.dump(packaged_data, f)
    
    print("\nPackaging complete! You can now run the Streamlit application.")

if __name__ == "__main__":
    # --- For full data packaging, uncomment the line below and comment out the test block ---
    package_data()

    # # --- For testing the design event parser on a small sample ---
    # print("--- Running in Test Mode: Processing a sample of design events ---")
    # sample_df = process_design_events(DESIGN_EVENT_ROOT_PATH, sample_size=2)
    # if not sample_df.empty:
    #     output_path = "test.csv"
    #     sample_df.index.name = 'datetime'
    #     sample_df.to_csv(output_path)
    #     print(f"\n--- Sample DataFrame has been saved to {output_path} ---")
    # else:
    #     print("\n--- No data was processed in the sample run. ---")
