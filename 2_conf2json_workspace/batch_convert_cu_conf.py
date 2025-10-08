#!/usr/bin/env python3
"""
Batch Converter for CU Configuration Files
Converts all .conf files from error_conf directory to JSON format
"""

import os
import sys
import glob
from pathlib import Path
from simple_conf_to_json import parse_conf_to_json
import json


def batch_convert_cu_conf():
    """Convert all CU .conf files to JSON format"""
    
    # Source and target directories
    source_dir = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\cu_conf\error_conf"
    target_dir = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\2_conf2json_workspace\cu_conf2json"
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Get all .conf files from source directory
    conf_files = glob.glob(os.path.join(source_dir, "*.conf"))
    
    print(f"Found {len(conf_files)} .conf files to convert")
    print(f"Source directory: {source_dir}")
    print(f"Target directory: {target_dir}")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    error_files = []
    
    for i, conf_file in enumerate(conf_files, 1):
        try:
            # Get the filename without extension
            filename = os.path.basename(conf_file)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Create output JSON file path
            json_file = os.path.join(target_dir, f"{name_without_ext}.json")
            
            print(f"[{i:3d}/{len(conf_files)}] Converting {filename}...", end=" ")
            
            # Parse the configuration file
            config_data = parse_conf_to_json(conf_file)
            
            # Write to JSON file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print("Success")
            success_count += 1
            
        except Exception as e:
            print(f"Error: {e}")
            error_count += 1
            error_files.append((filename, str(e)))
    
    print("-" * 50)
    print(f"Conversion completed!")
    print(f"Successfully converted: {success_count} files")
    print(f"Failed conversions: {error_count} files")
    
    if error_files:
        print("\nError details:")
        for filename, error in error_files:
            print(f"  - {filename}: {error}")
    
    return success_count, error_count, error_files


def main():
    """Main function"""
    print("CU Configuration Batch Converter")
    print("=" * 50)
    
    try:
        success_count, error_count, error_files = batch_convert_cu_conf()
        
        if error_count == 0:
            print("\nAll files converted successfully!")
            return 0
        else:
            print(f"\n{error_count} files failed to convert")
            return 1
            
    except Exception as e:
        print(f"\nBatch conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
