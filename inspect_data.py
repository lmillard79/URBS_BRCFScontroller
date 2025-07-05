import pickle
import numpy as np
from pprint import pprint

def inspect_pickle(filepath):
    print(f"\nInspecting {filepath}:")
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f, encoding='latin1')  # Try latin1 encoding which handles all bytes
    except Exception as e:
        print(f"Error loading pickle file: {e}")
        print("Trying with different encodings...")
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f, encoding='utf-8')
        except Exception as e2:
            print(f"Error with utf-8 encoding: {e2}")
            print("Trying with no encoding specified...")
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
    return data
    
    print("\nData type:", type(data))
    
    # If it's a dictionary, show keys and shapes of values if they're numpy arrays
    if isinstance(data, dict):
        print("\nDictionary contents:")
        for key, value in data.items():
            if hasattr(value, 'shape'):
                print(f"  {key}: {type(value)} with shape {value.shape}")
            else:
                print(f"  {key}: {type(value)}")
    
    # If it's a numpy array, show its shape and some basic stats
    elif hasattr(data, 'shape'):
        print(f"Array shape: {data.shape}")
        print(f"Array dtype: {data.dtype}")
        print(f"Array min: {np.nanmin(data)}")
        print(f"Array max: {np.nanmax(data)}")
    
    return data

def inspect_npz(filepath):
    print(f"\nInspecting {filepath}:")
    data = np.load(filepath, allow_pickle=True)
    
    print("\nNPZ file contents:")
    for key in data.files:
        item = data[key]
        if hasattr(item, 'shape'):
            print(f"  {key}: {type(item)} with shape {item.shape}")
        else:
            print(f"  {key}: {type(item)}")
    
    return data

def main():
    try:
        # Inspect the pickle file
        pickle_data = inspect_pickle('rsc/DM_B15ts.pkl')
        
        # Inspect the npz file
        npz_data = inspect_npz('rsc/DM_B15.npz')
        
        # Check for 60 model results and 28 locations
        print("\nChecking for 60 model results and 28 locations:")
        
        # Check pickle file
        if isinstance(pickle_data, dict):
            for key, value in pickle_data.items():
                if hasattr(value, 'shape'):
                    print(f"\nIn {key}:")
                    if len(value.shape) >= 1:
                        print(f"  First dimension (possible models): {value.shape[0]}")
                    if len(value.shape) >= 2:
                        print(f"  Second dimension (possible locations): {value.shape[1]}")
        
        # Check npz file
        for key in npz_data.files:
            item = npz_data[key]
            if hasattr(item, 'shape'):
                print(f"\nIn {key}:")
                if len(item.shape) >= 1:
                    print(f"  First dimension (possible models): {item.shape[0]}")
                if len(item.shape) >= 2:
                    print(f"  Second dimension (possible locations): {item.shape[1]}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
