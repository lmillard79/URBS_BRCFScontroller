import pickle
import re
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path

def load_location_names(loc_names_path):
    """Load location names from the text file."""
    with open(loc_names_path, 'r') as f:
        # Remove quotes and whitespace from each line
        locations = [line.strip().strip('"') for line in f if line.strip()]
    return locations

def extract_flow_timeseries(pkl_path, loc_names_path, output_pkl_path):
    """
    Extract flow time series data from pickle file and save as a packaged pickle file.
    
    Structure:
    - 11 AEPs (2, 5, 10, 20, 50, 100, 200, 500, 2000, 10000, 100000 years)
    - 29 locations
    - 961 timesteps per AEP
    - Multiple time series per AEP (4-7) identified by timestep resets
    
    Args:
        pkl_path (str): Path to the input pickle file
        loc_names_path (str): Path to the location names text file
        output_pkl_path (str): Path where to save the output pickle file
        
    Returns:
        pandas.DataFrame: Combined DataFrame with all flow time series data
    """
    # Load location names
    try:
        location_names = load_location_names(loc_names_path)
        print(f"Loaded {len(location_names)} location names from {loc_names_path}")
    except Exception as e:
        print(f"Error: Could not load location names: {e}")
        return None
    
    # AEP values (years)
    aep_years = [2, 5, 10, 20, 50, 100, 200, 500, 2000, 10000, 100000]
    
    # Load the pickle file with proper encoding
    try:
        with open(pkl_path, 'rb') as f:
            # Load the data (it's a dict with 'qts' key containing our data)
            data = pickle.load(f, encoding='latin1')
            qts_data = data['qts']  # Extract the flow time series data
            print(f"Loaded data with {len(qts_data)} AEPs")
            
            # Print shapes of all AEPs for debugging
            for i, arr in enumerate(qts_data):
                if hasattr(arr, 'shape'):
                    print(f"  AEP {aep_years[i]}: {arr.shape}")
                else:
                    print(f"  AEP {aep_years[i]}: Not a numpy array")
            
    except Exception as e:
        print(f"Error loading pickle file: {e}")
        return None
    
    # List to store all DataFrames
    all_dfs = []
    
    # Process each AEP
    for aep_idx, (aep_year, aep_array) in enumerate(zip(aep_years, qts_data)):
        if not isinstance(aep_array, np.ndarray):
            print(f"Skipping AEP {aep_year}: Not a numpy array")
            continue
            
        print(f"\nProcessing AEP {aep_year} years - Shape: {aep_array.shape}")
        
        # The shape should be (ensemble_members, locations, timesteps)
        # Based on the inspection: (30, 7, 961)
        if len(aep_array.shape) != 3:
            print(f"  Warning: Expected 3 dimensions, got {len(aep_array.shape)}")
            continue
            
        # Reorder dimensions to (timesteps, ensemble_members, locations)
        aep_array = np.transpose(aep_array, (2, 0, 1))
        timesteps, ensemble_size, locations = aep_array.shape
        
        print(f"  Reordered shape: {aep_array.shape} (timesteps: {timesteps}, "
              f"ensemble: {ensemble_size}, locations: {locations})")
        
        # Now the shape is (timesteps, ensemble_members, locations)
        # timesteps should be 961, ensemble_members varies, locations should match location_names
        if locations != len(location_names):
            print(f"  Warning: Number of locations ({locations}) doesn't match location names ({len(location_names)})")
            print("  Will proceed with the data as is...")
        
        print(f"  Processing: {timesteps} timesteps, {locations} locations, {ensemble_size} ensemble members")
        
        # Now process each ensemble member
        for ens_idx in range(ensemble_size):
            # Extract data for this ensemble member (all locations, all timesteps)
            ens_data = aep_array[:, ens_idx, :]  # Shape: (timesteps, locations)
            
            # Create column names, using the provided location names and adding generic names for any extra locations
            if locations > len(location_names):
                # Create generic column names for any missing location names
                all_cols = location_names + [f'Location_{i+1+len(location_names)}' for i in range(locations - len(location_names))]
            else:
                all_cols = location_names[:locations]
            
            # Create the DataFrame with all columns
            df = pd.DataFrame(ens_data, columns=all_cols)
            
            # Add metadata columns
            df['AEP_Years'] = aep_year
            df['AEP_Value'] = f"1 in {aep_year}"
            df['Ensemble_ID'] = ens_idx + 1
            
            # Add Index, TimeStep, and TimeStep_hrs columns
            df.insert(0, 'Index', range(len(df)))
            df.insert(4, 'TimeStep', np.arange(1, len(df) + 1))
            df['TimeStep_hrs'] = df['TimeStep'] - 1  # 0-based hours
            
            # Add model information
            df['Model'] = '2030 SSP2'
            
            # Reorder columns to have metadata first, then location data
            cols = ['Index', 'Model', 'AEP_Years', 'AEP_Value', 'Ensemble_ID', 'TimeStep', 'TimeStep_hrs'] + \
                  [col for col in all_cols if col in df.columns and col not in ['TimeStep', 'TimeStep_hrs']]
            df = df[cols]
            
            # Add to list of all DataFrames
            all_dfs.append(df)
    
    # Combine all DataFrames if we have any
    if all_dfs:
        all_data = pd.concat(all_dfs, ignore_index=True)
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_pkl_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the combined data as a pickle file
        all_data.to_pickle(output_pkl_path)
        print(f"\nSaved packaged data to {output_pkl_path} - Shape: {all_data.shape}")
        
        return all_data
    
    return None

def main():
    # Paths
    pkl_path = 'rsc/DM_B15ts.pkl'
    loc_names_path = 'rsc/LocNames.txt'
    output_pkl_path = 'packaged_data/flow_timeseries_2030_SSP2.pkl'
    
    print(f"Extracting flow time series from {pkl_path}")
    print("-" * 60)
    
    # Extract the data and save as packaged pickle file
    flow_data = extract_flow_timeseries(pkl_path, loc_names_path, output_pkl_path)
    
    if flow_data is not None:
        print("\nExtraction complete!")
        print(f"Packaged data saved to: {output_pkl_path}")
        print(f"Total rows: {len(flow_data):,}")
        print("\nColumns:", ", ".join(flow_data.columns[:10]) + ', ...')
    else:
        print("\nFailed to extract flow time series data.")

if __name__ == "__main__":
    main()
