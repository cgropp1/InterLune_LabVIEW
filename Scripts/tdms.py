import os
import re
from pathlib import Path
from datetime import datetime
from nptdms import TdmsFile, TdmsWriter
import shutil

# --- CONFIGURATION ---
# Replace this with the actual path to your main directory containing all the test folders
PARENT_DIRECTORY = r"C:\Users\Cole\Documents\GitHub\InterLune_LabVIEW\Interlune_MLSS_Testing" 
OUTPUT_FOLDER_NAME = "Combined_Output"
# ---------------------

def get_tdms_start_time(file_path):
    """
    Attempts to read the internal TDMS file properties for a recording start time.
    Falls back to parsing the timestamp from the filename if needed.
    """
    try:
        with TdmsFile.read(file_path) as tdms_file:
            for prop_name in ['DateTime', 'Start_Time', 'RecordingStartTime']:
                if prop_name in tdms_file.properties:
                    return tdms_file.properties[prop_name]
    except Exception as e:
        print(f"  Warning: Could not read internal properties for {file_path.name}: {e}")
    
    # Fallback: Extract timestamp from filename
    match = re.search(r'(\d{4}[_.-]\d{2}[_.-]\d{2})[_.-](\d{2}[_.-]\d{2}[_.-]\d{2})', file_path.name)
    if match:
        try:
            date_str, time_str = match.groups()
            clean_str = f"{date_str}_{time_str}".replace('-', '_').replace('.', '_')
            return datetime.strptime(clean_str, "%Y_%m_%d_%H_%M_%S")
        except ValueError:
            pass
            
    return os.path.getmtime(file_path)

def combine_tdms_files(file_list, output_path):
    """
    Combines a list of TDMS files into a single TDMS file sequentially.
    """
    if not file_list:
        return False
    
    print(f"    Creating: {output_path.name} ({len(file_list)} files)")
    
    string_path = str(output_path)

    with TdmsWriter(string_path, index_file = True) as tdms_writer:
        for file_path in file_list:
            try:
                with TdmsFile.read(file_path) as tdms_file:
                    for group in tdms_file.groups():
                        for channel in group.channels():
                            tdms_writer.write_segment([channel])
            except Exception as e:
                print(f"    Error processing {file_path.name}: {e}")
    return True

def process_all_tests(parent_dir):
    parent_path = Path(parent_dir)
    
    # Get immediate subdirectories (each one represents a separate test)
    # Using os.scandir to only look one level down initially
    subfolders = [Path(f.path) for f in os.scandir(parent_path) if f.is_dir()]
    
    if not subfolders:
        print(f"No subfolders found in {parent_dir}")
        return

    print(f"Found {len(subfolders)} subfolders to process.\n" + "="*50)

    for folder in subfolders:
        # Skip any existing output folders if re-running the script
        if folder.name == OUTPUT_FOLDER_NAME:
            continue
            
        print(f"\nProcessing Test Folder: {folder.name}")
        
        setup_files = []
        load_torque_files = []
        gantry_files = []
        
        # Scan inside THIS specific subfolder only
        for root, _, files in os.walk(folder):
            # Skip output folder if it already exists inside this directory
            if OUTPUT_FOLDER_NAME in root:
                continue
                
            for file in files:
                if not file.endswith('.tdms'):
                    continue
                    
                file_path = Path(root) / file
                
                if "setup_data.dat.tdms" in file:
                    setup_files.append(file_path)
                elif file.startswith("Load_and_Torque"):
                    load_torque_files.append(file_path)
                elif file.startswith("Gantry"):
                    gantry_files.append(file_path)
        
        # If the folder is empty of target files, skip it
        if not (setup_files or load_torque_files or gantry_files):
            print("  No relevant TDMS files found. Skipping.")
            continue
            
        # Target path for this specific folder's output
        output_dir = folder / OUTPUT_FOLDER_NAME
        output_dir.mkdir(exist_ok=True)
        
        # 1. Handle Setup File
        if setup_files:
            destination = output_dir / "setup_data.dat.tdms"
            shutil.copy2(setup_files[0], destination)
            print(f"    Copied: setup_data.dat.tdms")
        else:
            print("    Notice: No setup_data.dat.tdms found in this folder.")
            
        # 2. Sort and combine Load and Torque
        if load_torque_files:
            load_torque_files.sort(key=get_tdms_start_time)
            combine_tdms_files(load_torque_files, output_dir / "Combined_Load_and_Torque.tdms")
            
        # 3. Sort and combine Gantry
        if gantry_files:
            gantry_files.sort(key=get_tdms_start_time)
            combine_tdms_files(gantry_files, output_dir / "Combined_Gantry.tdms")

    print("\n" + "="*50 + "\nAll test folders processed successfully!")

if __name__ == "__main__":
    process_all_tests(PARENT_DIRECTORY)