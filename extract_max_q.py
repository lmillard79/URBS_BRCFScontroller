import numpy as np
import pandas as pd

def load_location_names(loc_names_path):
    """Load location names from the text file."""
    with open(loc_names_path, 'r') as f:
        # Remove quotes and whitespace from each line
        locations = [line.strip().strip('"') for line in f if line.strip()]
    return locations

def extract_max_q_data(npz_path, loc_names_path, aeps):
    """
    Extract max_q data from NPZ file and return a labeled DataFrame.
    
    Args:
        npz_path (str): Path to the NPZ file
        loc_names_path (str): Path to the location names text file
        aeps (np.array): Array of AEP (Annual Exceedance Probability) values
        
    Returns:
        pd.DataFrame: DataFrame with max_q values, AEPs as index, and named Locations as columns
    """
    # Load the NPZ file
    with np.load(npz_path, allow_pickle=True) as data:
        if 'max_q' not in data:
            raise ValueError("'max_q' array not found in the NPZ file")
        max_q_array = data['max_q']
    
    # Validate AEPs match data
    if len(aeps) != max_q_array.shape[0]:
        raise ValueError(f"Number of AEP values ({len(aeps)}) does not match data rows ({max_q_array.shape[0]})")
    
    # Get location names
    try:
        location_names = load_location_names(loc_names_path)
        # If we have fewer names than locations, pad with default names
        if len(location_names) < max_q_array.shape[1]:
            print(f"Info: Found {len(location_names)} location names for {max_q_array.shape[1]} locations. Using provided names and default names for the rest.")
            location_names.extend([f'Location_{i+1}' for i in range(len(location_names), max_q_array.shape[1])])
        # If we have more names than locations, truncate the list
        elif len(location_names) > max_q_array.shape[1]:
            print(f"Info: Truncating {len(location_names)} location names to match {max_q_array.shape[1]} locations in data.")
            location_names = location_names[:max_q_array.shape[1]]
    except Exception as e:
        print(f"Warning: Could not load location names: {e}. Using default names.")
        location_names = [f'Location_{i+1}' for i in range(max_q_array.shape[1])]
    
    # Ensure we have exactly the right number of location names
    location_names = location_names[:max_q_array.shape[1]]
    
    # Create DataFrame with location names as column headers
    df = pd.DataFrame(
        data=max_q_array,
        index=[f"1-in-{int(1/aep):,} AEP ({aep:.6f})" for aep in aeps],
        columns=location_names
    )
    
    # Add a column for the AEP values (numeric)
    df['AEP'] = aeps
    
    return df

def main():
    try:
        # Paths to the data files
        npz_path = 'rsc/DM_B15.npz'
        loc_names_path = 'rsc/LocNames.txt'
        
        # Define AEP values
        aep_years = [2, 5, 10, 20, 50, 100, 200, 500, 2000, 10000, 100000]
        aeps = np.array([1.0/year for year in aep_years])
        
        # Extract the data with location names
        df = extract_max_q_data(npz_path, loc_names_path, aeps)
        
        # Display information about the DataFrame
        print("DataFrame shape:", df.shape)
        print("\nAEP values used:")
        for year, aep in zip(aep_years, aeps):
            print(f"  1-in-{year:,} years: AEP = {aep:.6f}")
        
        print("\nFirst few rows:")
        print(df.head())
        
        # Save to CSV for inspection
        output_path = 'max_q_data.csv'
        df.to_csv(output_path)
        print(f"\nData saved to {output_path}")
        
        return df
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    df = main()
