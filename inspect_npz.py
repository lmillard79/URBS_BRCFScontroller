import numpy as np

def inspect_npz(filepath):
    print(f"\nInspecting {filepath}:")
    
    # Load the npz file
    with np.load(filepath, allow_pickle=True) as data:
        print("\nNPZ file contents:")
        for key in data.files:
            item = data[key]
            print(f"\nArray: {key}")
            print(f"  Type: {type(item)}")
            print(f"  Shape: {item.shape}")
            print(f"  Data type: {item.dtype}")
            
            # Show some sample data
            print("  First few values:")
            if len(item.shape) == 1:
                print(f"    {item[:5]}...")
            elif len(item.shape) == 2:
                print(f"    First row: {item[0, :5]}...")
                print(f"    Second row: {item[1, :5]}...")
            
            # Basic statistics
            print(f"  Min: {np.nanmin(item)}")
            print(f"  Max: {np.nanmax(item)}")
            print(f"  Mean: {np.nanmean(item):.4f}")
            print(f"  Std: {np.nanstd(item):.4f}")

if __name__ == "__main__":
    inspect_npz('rsc/DM_B15.npz')
