import pickle
import numpy as np

def print_structure(obj, level=0, max_level=3, max_length=5):
    """Recursively print the structure of a Python object."""
    indent = '  ' * level
    
    if level > max_level:
        print(f"{indent}... (max level reached)")
        return
    
    if isinstance(obj, dict):
        print(f"{indent}Dictionary with {len(obj)} keys:")
        for i, (k, v) in enumerate(obj.items()):
            if i >= max_length:
                print(f"{indent}  ... ({len(obj) - max_length} more items)")
                break
            print(f"{indent}- {k}:", end=' ')
            if isinstance(v, (dict, list, np.ndarray, tuple)):
                print()
                print_structure(v, level + 1, max_level, max_length)
            else:
                print(f"{type(v).__name__} = {str(v)[:100]}" + ('...' if len(str(v)) > 100 else ''))
    
    elif isinstance(obj, (list, tuple)):
        print(f"{indent}{type(obj).__name__} of length {len(obj)}:")
        for i, item in enumerate(obj):
            if i >= max_length:
                print(f"{indent}  ... ({len(obj) - max_length} more items)")
                break
            print(f"{indent}- [{i}]:", end=' ')
            if isinstance(item, (dict, list, np.ndarray, tuple)):
                print()
                print_structure(item, level + 1, max_level, max_length)
            else:
                print(f"{type(item).__name__} = {str(item)[:100]}" + ('...' if len(str(item)) > 100 else ''))
    
    elif isinstance(obj, np.ndarray):
        print(f"{indent}ndarray of shape {obj.shape}, dtype={obj.dtype}")
        if obj.size > 0 and obj.size <= 5:  # Only print small arrays
            print(f"{indent}  {obj}")
    
    else:
        print(f"{indent}{type(obj).__name__} = {str(obj)[:100]}" + ('...' if len(str(obj)) > 100 else ''))

def main():
    pkl_path = 'rsc/DM_B15ts.pkl'
    
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
    
    if data is None:
        print("Could not load pickle file with any encoding")
        return
    
    print("\nStructure of the pickle file:")
    print("-" * 80)
    print_structure(data, max_level=4)
    
    # If it's a dictionary with 'qts' and 'hts' keys, try to get their shapes
    if isinstance(data, dict):
        print("\nTime series information:")
        for key in ['qts', 'hts']:
            if key in data:
                ts = data[key]
                if hasattr(ts, 'shape'):
                    print(f"  {key}: shape = {ts.shape}, dtype = {getattr(ts, 'dtype', 'N/A')}")
                else:
                    print(f"  {key}: {type(ts)}")

if __name__ == "__main__":
    main()
