import pickle
import numpy as np
import pandas as pd
from pathlib import Path

def load_location_names(loc_names_path):
    """Load location names from the text file."""
    with open(loc_names_path, 'r') as f:
        # Remove quotes and whitespace from each line
        locations = [line.strip().strip('"') for line in f if line.strip()]
    return locations

def extract_timeseries(pkl_path, loc_names_path):
    """
    Extract time series data from pickle file and return a labeled DataFrame.
    
    Args:
        pkl_path (str): Path to the pickle file
        loc_names_path (str): Path to the location names text file
        
    Returns:
        dict: Dictionary of DataFrames for each time series type (qts, hts, etc.)
    """
    # Try different encodings to load the pickle file
    encodings = ['latin1', 'utf-8', 'iso-8859-1', None]
    data = None
    
    for encoding in encodings:
        try:
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f, encoding=encoding)
            print(f"Successfully loaded pickle file with encoding: {encoding}")
            break
        except Exception as e:
            print(f"Failed to load with encoding {encoding}: {e}")
            continue
    
    if data is None:
        raise ValueError("Could not load pickle file with any encoding")
    
    print("\nAvailable keys in the pickle file:", list(data.keys()))
    
    # Try to load location names
    try:
        location_names = load_location_names(loc_names_path)
        print(f"\nLoaded {len(location_names)} location names")
    except Exception as e:
        print(f"Warning: Could not load location names: {e}")
        location_names = None
    
    # Process each time series in the data
    result = {}
    
    for ts_key, ts_data in data.items():
        if not isinstance(ts_data, np.ndarray):
            print(f"\nSkipping {ts_key}: Not a numpy array")
            continue
            
        print(f"\nProcessing {ts_key} with shape {ts_data.shape}")
        
        # Determine the structure of the data
        if ts_data.ndim == 3:  # [time, location, ?]
            print(f"3D array detected - shape: {ts_data.shape}")
            print("Assuming dimensions: [time, location, variable]")
            
            # Create a MultiIndex for the columns
            if location_names and len(location_names) == ts_data.shape[1]:
                locs = location_names
            else:
                locs = [f'Location_{i+1}' for i in range(ts_data.shape[1])]
            
            # Create a DataFrame for each variable in the 3rd dimension
            for var_idx in range(ts_data.shape[2]):
                var_name = f"{ts_key}_var{var_idx}"
                df = pd.DataFrame(
                    data=ts_data[:, :, var_idx],
                    columns=locs
                )
                result[var_name] = df
                print(f"  Created DataFrame '{var_name}' with shape {df.shape}")
        
        elif ts_data.ndim == 2:  # [time, location]
            print(f"2D array detected - shape: {ts_data.shape}")
            print("Assuming dimensions: [time, location]")
            
            if location_names and len(location_names) == ts_data.shape[1]:
                locs = location_names
            else:
                locs = [f'Location_{i+1}' for i in range(ts_data.shape[1])]
            
            df = pd.DataFrame(
                data=ts_data,
                columns=locs
            )
            result[ts_key] = df
            print(f"  Created DataFrame '{ts_key}' with shape {df.shape}")
        
        else:
            print(f"Unhandled array shape {ts_data.shape} for {ts_key}")
    
    return result

def save_to_excel(data_dict, output_path):
    """Save multiple DataFrames to different sheets in an Excel file."""
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for name, df in data_dict.items():
            # Truncate sheet name to Excel's limit of 31 characters
            sheet_name = name[:31]
            df.to_excel(writer, sheet_name=sheet_name)
    print(f"\nSaved results to {output_path}")

def main():
    try:
        # Paths to the data files
        pkl_path = 'rsc/DM_B15ts.pkl'
        loc_names_path = 'rsc/LocNames.txt'
        output_path = 'timeseries_data.xlsx'
        
        print(f"Extracting time series data from {pkl_path}")
        
        # Extract the time series data
        ts_data = extract_timeseries(pkl_path, loc_names_path)
        
        if not ts_data:
            print("No time series data was extracted.")
            return
        
        # Display information about the extracted data
        print("\nExtracted the following time series:")
        for name, df in ts_data.items():
            print(f"- {name}: {df.shape[0]} time steps x {df.shape[1]} locations")
            print(f"  Time range: {df.index[0]} to {df.index[-1]}" if hasattr(df.index[0], 'strftime') else "  No datetime index")
        
        # Save to Excel
        save_to_excel(ts_data, output_path)
        
        print("\nDone!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
