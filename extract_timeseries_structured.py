import pickle
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

def load_pickle_file(pkl_path):
    """Load the pickle file with different encodings."""
    encodings = ['latin1', 'utf-8', 'iso-8859-1', None]
    
    for encoding in encodings:
        try:
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f, encoding=encoding)
            print(f"Successfully loaded pickle file with encoding: {encoding}")
            return data
        except Exception as e:
            print(f"Failed to load with encoding {encoding}: {e}")
    
    raise ValueError("Could not load pickle file with any encoding")

def create_time_series_dataframes(ts_data, aep_years, output_dir, prefix=''):
    """
    Create DataFrames from time series data and save to CSV.
    
    Args:
        ts_data: List of numpy arrays containing time series data
        aep_years: List of AEP years corresponding to each array in ts_data
        output_dir: Directory to save output files
        prefix: Prefix for output filenames (e.g., 'qts_' or 'hts_')
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    all_dfs = []
    
    for i, (aep_year, ts_array) in enumerate(zip(aep_years, ts_data)):
        print(f"\nProcessing {prefix}AEP {aep_year} years - Shape: {ts_array.shape}")
        
        # Determine dimensions
        if ts_array.ndim == 3:
            time_steps, locations, nodes = ts_array.shape
            
            # Create a DataFrame for each location
            for loc in range(locations):
                # Create time index (assuming 1-hour intervals, adjust as needed)
                start_time = datetime(2000, 1, 1)  # Arbitrary start time
                time_index = [start_time + timedelta(hours=t) for t in range(time_steps)]
                
                # Create DataFrame
                df = pd.DataFrame(
                    data=ts_array[:, loc, :],
                    index=time_index,
                    columns=[f'Node_{n+1}' for n in range(nodes)]
                )
                
                # Add metadata columns
                df['AEP_Years'] = aep_year
                df['AEP_Value'] = 1.0 / aep_year
                df['Location'] = f'Loc_{loc+1}'
                
                all_dfs.append(df)
                
                # Save individual location file
                filename = os.path.join(output_dir, f"{prefix}aep_{aep_year}_loc_{loc+1}.csv")
                df.to_csv(filename)
                print(f"  Saved {df.shape} to {filename}")
            
            # Save combined data for this AEP
            combined_filename = os.path.join(output_dir, f"{prefix}aep_{aep_year}_combined.csv")
            pd.concat([df for df in all_dfs if df['AEP_Years'].iloc[0] == aep_year]).to_csv(combined_filename)
            
        else:
            print(f"  Warning: Unhandled array shape {ts_array.shape}")
    
    # Save all data to a single file
    if all_dfs:
        combined_all_filename = os.path.join(output_dir, f"{prefix}all_aeps_combined.csv")
        pd.concat(all_dfs).to_csv(combined_all_filename)
        print(f"\nSaved all {len(all_dfs)} time series to {combined_all_filename}")

def main():
    try:
        # Configuration
        pkl_path = 'rsc/DM_B15ts.pkl'
        output_dir = 'timeseries_output'
        
        # AEP years (from 2 to 100,000 years)
        aep_years = [2, 5, 10, 20, 50, 100, 200, 500, 2000, 10000, 100000]
        
        # Load the pickle file
        print(f"Loading {pkl_path}...")
        data = load_pickle_file(pkl_path)
        
        # Process qts (flow rate time series)
        if 'qts' in data and isinstance(data['qts'], list):
            print("\nProcessing qts (flow rate time series)...")
            create_time_series_dataframes(
                data['qts'], 
                aep_years, 
                os.path.join(output_dir, 'flow_rates'),
                'qts_'
            )
        
        # Process hts (water level time series)
        if 'hts' in data and isinstance(data['hts'], list):
            print("\nProcessing hts (water level time series)...")
            create_time_series_dataframes(
                data['hts'], 
                aep_years, 
                os.path.join(output_dir, 'water_levels'),
                'hts_'
            )
        
        print("\nProcessing complete!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
