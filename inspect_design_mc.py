import pandas as pd
import gzip
import pickle

# Path to the design MC data file
design_path = "packaged_data/DESIGN_URBS_packaged_j_drive_data.pkl.gz"

try:
    # Load the design MC data
    with gzip.open(design_path, 'rb') as f:
        data = pickle.load(f)
    
    print("=== design_MC Data Structure ===")
    
    # Check if data is a dictionary or DataFrame
    if isinstance(data, dict):
        print("\nTop-level keys in design_MC:", list(data.keys()))
        
        # If it has design_events, show its structure
        if 'design_events' in data and hasattr(data['design_events'], 'columns'):
            df = data['design_events']
            print("\n=== design_events DataFrame ===")
            print("Shape:", df.shape)
            print("\nColumns:")
            for col in df.columns:
                print(f"- {col} (dtype: {df[col].dtype})")
                
            # Show unique values for categorical columns
            print("\nUnique values in key columns:")
            for col in ['aep', 'location']:
                if col in df.columns:
                    print(f"\n{col} (total unique: {df[col].nunique()}):")
                    print(df[col].unique()[:20])  # Show first 20 unique values if many
                    if df[col].nunique() > 20:
                        print("... and", df[col].nunique() - 20, "more")
    
    elif hasattr(data, 'columns'):  # If it's a DataFrame directly
        print("\n=== design_MC DataFrame ===")
        print("Shape:", data.shape)
        print("\nColumns:")
        for col in data.columns:
            print(f"- {col} (dtype: {data[col].dtype})")
    
    else:
        print("\nUnexpected data type:", type(data))
        
except Exception as e:
    print(f"Error loading or processing design_MC data: {str(e)}")
    import traceback
    traceback.print_exc()
