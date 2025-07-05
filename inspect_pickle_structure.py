import pickle
import numpy as np

def inspect_pickle_structure(filepath):
    """Inspect the structure of a pickle file."""
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f, encoding='latin1')
            
        print("\n=== Pickle File Structure ===")
        print(f"Type: {type(data)}")
        
        if isinstance(data, dict):
            print("\nDictionary keys:", list(data.keys()))
            for key, value in data.items():
                print(f"\nKey: {key}")
                print(f"  Type: {type(value)}")
                if hasattr(value, 'shape'):
                    print(f"  Shape: {value.shape}")
                elif isinstance(value, (list, tuple)):
                    print(f"  Length: {len(value)}")
                    if len(value) > 0:
                        print(f"  First element type: {type(value[0])}")
                        if hasattr(value[0], 'shape'):
                            print(f"  First element shape: {value[0].shape}")
        
        elif isinstance(data, (list, tuple, np.ndarray)):
            print(f"\nLength: {len(data)}")
            if len(data) > 0:
                print(f"First element type: {type(data[0])}")
                if hasattr(data[0], 'shape'):
                    print(f"First element shape: {data[0].shape}")
        
        return data
        
    except Exception as e:
        print(f"Error inspecting pickle file: {e}")
        return None

if __name__ == "__main__":
    filepath = "rsc/DM_B15ts.pkl"
    print(f"Inspecting pickle file: {filepath}")
    data = inspect_pickle_structure(filepath)
