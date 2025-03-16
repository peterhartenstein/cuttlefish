import numpy as np
import json
import os
import glob

def npy_to_json(dir):
    data = np.load(dir, allow_pickle=True)

    base_filename = os.path.splitext(os.path.basename(dir))[0] #remove ".npy"
    output_filename = os.path.join(os.path.dirname(dir), f"{base_filename}.json")

    json_data = data.tolist()

    with open(output_filename, 'w') as f:
        json.dump(json_data, f, indent=4)

    print(f"Saved {output_filename}")

if __name__ == "__main__":
    npy_files = glob.glob("npy_data/*.npy")

    if not npy_files:
        print("No .npy files found in the npy_data directory.")
    else:
        for npy_file in npy_files:
            npy_to_json(npy_file)