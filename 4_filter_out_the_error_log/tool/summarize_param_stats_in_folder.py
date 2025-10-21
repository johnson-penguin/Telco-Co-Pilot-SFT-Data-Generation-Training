import os
import datetime
from pathlib import Path
def summarize_and_update_readme(root_dir, readme_path):
    """
    Traverses the specified root directory, counts the number of files in 'CU', 'DU', and 'UE'
    subfolders, and then updates the specified Readme.md file with a detailed report and summary.

    Args:
        root_dir (str): The path of the root directory to analyze.
        readme_path (str): The full path of the Readme.md file to update.
    """
    # Check if the root directory exists
    if not os.path.isdir(root_dir):
        print(f"❌ Error: Directory not found '{root_dir}'. Please check the path.")
        return

    # Dictionary to store the total counts
    total_counts = {'CU': 0, 'DU': 0, 'UE': 0}
    
    # List to build the Markdown file content
    markdown_output = []

    # --- 1. Generate Detailed Counts ---
    print("--- Detailed Counts by Folder ---")
    markdown_output.append("# File Count Report")
    markdown_output.append(f"> Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_output.append("\n---\n")
    markdown_output.append("## 📁 Detailed Counts by Folder")

    # Iterate through all items in the root directory, sorted for consistent order
    for folder_name in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, folder_name)

        # Process only directories
        if os.path.isdir(folder_path):
            print(f"\n📁 Folder: {folder_name}")
            
            folder_content = [] # Temporary list for this folder's content
            
            # Check for 'CU', 'DU', 'UE' subfolders
            for component in ['CU', 'DU', 'UE']:
                component_path = os.path.join(folder_path, component)

                if os.path.isdir(component_path):
                    try:
                        # Count the number of files in this directory (filtering out subdirectories)
                        num_files = len([name for name in os.listdir(component_path)
                                         if os.path.isfile(os.path.join(component_path, name))])
                        
                        if num_files > 0:
                            line = f"  - {component}: {num_files} cases"
                            print(line)
                            folder_content.append(f"- **{component}**: `{num_files}` cases")
                            # Add to the total count
                            total_counts[component] += num_files
                    
                    except OSError as e:
                        print(f"    Could not read {component_path}: {e}")

            # If any cases were found in this folder, add its title and content to the report
            if folder_content:
                markdown_output.append(f"\n### {folder_name}")
                markdown_output.extend(folder_content)

    # --- 2. Generate Summary ---
    summary_title = "\n" + "="*25 + "\n📊 Summary\n" + "="*25
    print(summary_title)
    print(f"Total CU cases: {total_counts['CU']}")
    print(f"Total DU cases: {total_counts['DU']}")
    print(f"Total UE cases: {total_counts['UE']}")

    markdown_output.append("\n<br>\n\n---\n")
    markdown_output.append("## 📊 Summary")
    markdown_output.append(f"- **Total CU cases**: `{total_counts['CU']}`")
    markdown_output.append(f"- **Total DU cases**: `{total_counts['DU']}`")
    markdown_output.append(f"- **Total UE cases**: `{total_counts['UE']}`")

    # --- 3. Write the results to Readme.md ---
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(markdown_output))
        print(f"\n✅ Report successfully updated to: {readme_path}")
    except IOError as e:
        print(f"\n❌ Error writing to file: {e}")

# --- How to Use ---
# 1. Set the target directory and the output file path below.
# 2. Simply run this Python script.

# The target directory to analyze
BASE_DIR = Path(__file__).resolve()
PARENT_DIRECTORY = BASE_DIR.parent.parent
# print("--------------------------------")
# print(f"BASE_DIR: {BASE_DIR}")
# print("--------------------------------")
# print(f"PARENT_DIRECTORY: {PARENT_DIRECTORY}")

target_directory = PARENT_DIRECTORY
# The path for the output Readme.md file
readme_file_path = PARENT_DIRECTORY / "Readme.md"

# Execute the main function
summarize_and_update_readme(target_directory, readme_file_path)