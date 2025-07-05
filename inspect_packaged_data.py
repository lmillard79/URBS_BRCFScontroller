import gzip
import pickle
import pandas as pd
from pathlib import Path

def inspect_packaged_data(filepath):
    """Inspect the structure of a packaged data file."""
    try:
        with gzip.open(filepath, 'rb') as f:
            data = pickle.load(f)
            
        print(f"\n=== File: {Path(filepath).name} ===")
        print(f"Type: {type(data)}")
        
        if isinstance(data, dict):
            print("\nDictionary keys:", list(data.keys()))
            for key, value in data.items():
                print(f"\nKey: {key}")
                print(f"  Type: {type(value)}")
                if isinstance(value, pd.DataFrame):
                    print(f"  Shape: {value.shape}")
                    print("  Columns:", list(value.columns))
                    print("  First few rows:")
                    print(value.head(2).to_string())
                elif hasattr(value, 'shape'):
                    print(f"  Shape: {value.shape}")
                elif isinstance(value, (list, tuple)):
                    print(f"  Length: {len(value)}")
                    if len(value) > 0:
                        print(f"  First element type: {type(value[0])}")
        
        return data
        
    except Exception as e:
        print(f"Error inspecting packaged data: {e}")
        return None

if __name__ == "__main__":
    # Inspect both packaged data files
    data_dir = Path("packaged_data")
    for pkl_file in data_dir.glob("*.pkl.gz"):
        inspect_packaged_data(pkl_file)
