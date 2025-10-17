import os

def summarize_directory_counts(root_dir):
    """
    Traverses the specified root directory, counts the number of files in 
    'CU', 'DU', and 'UE' subfolders, and calculates the grand total.

    Args:
        root_dir (str): The path to the root directory you want to analyze.
    """
    # Check if the root directory exists
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found. Please check the path.")
        return

    # Dictionary to store the total counts
    total_counts = {'CU': 0, 'DU': 0, 'UE': 0}
    
    print("--- Detailed Counts by Folder ---")

    # Iterate through all items in the root directory
    # Using sorted() to ensure a consistent order
    for folder_name in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, folder_name)

        # Process only directories
        if os.path.isdir(folder_path):
            print(f"\n📁 Folder: {folder_name}")
            
            # Check for 'CU', 'DU', 'UE' subdirectories
            for component in ['CU', 'DU', 'UE']:
                component_path = os.path.join(folder_path, component)

                if os.path.isdir(component_path):
                    try:
                        # Count the number of files in this directory (filtering out subdirectories)
                        num_files = len([name for name in os.listdir(component_path) 
                                         if os.path.isfile(os.path.join(component_path, name))])
                        
                        if num_files > 0:
                            print(f"  - {component}: {num_files} cases")
                            # Add to the total count
                            total_counts[component] += num_files
                    
                    except OSError as e:
                        print(f"    Could not read {component_path}: {e}")

    # --- Print Summary ---
    print("\n" + "="*25)
    print("📊 Summary")
    print("="*25)
    print(f"Total CU cases: {total_counts['CU']}")
    print(f"Total DU cases: {total_counts['DU']}")
    print(f"Total UE cases: {total_counts['UE']}")

# --- How to Use ---
# 1. Change 'your_target_directory' below to the path of your root folder.
#    For example: '4_filter_out_the_error_log'
# 2. Run this Python script.

target_directory = '4_filter_out_the_error_log' 
summarize_directory_counts(target_directory)