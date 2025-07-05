import pickle
import sys
import pandas as pd
import gzip
from io import StringIO

def inspect(data, indent=0):
    prefix = ' ' * indent
    if isinstance(data, dict):
        print(f'{prefix}Dictionary with {len(data)} keys:')
        for key, value in data.items():
            print(f'{prefix}  - {key}: {type(value).__name__}')
            inspect(value, indent + 4)
    elif isinstance(data, list):
        print(f'{prefix}List with {len(data)} items:')
        if data:
            print(f'{prefix}  - Item 0: {type(data[0]).__name__}')
            inspect(data[0], indent + 4)
    elif isinstance(data, pd.DataFrame):
        print(f'{prefix}DataFrame with shape {data.shape}')
        print(f'{prefix}Columns and Data Types:')
        buffer = StringIO()
        data.info(buf=buffer)
        info_str = buffer.getvalue()
        print(f'{prefix}{info_str}')
        print(f'{prefix}First 5 rows:')
        print(data.head().to_string())

    else:
        print(f'{prefix}Object of type: {type(data).__name__}')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_pickle.py <path_to_pickle_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        opener = gzip.open if file_path.endswith('.gz') else open
        with opener(file_path, 'rb') as f:
            data = pickle.load(f)
        
        inspect(data)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
