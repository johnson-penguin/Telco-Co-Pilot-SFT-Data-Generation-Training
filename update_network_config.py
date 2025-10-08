#!/usr/bin/env python3
"""
Update network_config in existing JSON files with baseline configuration
"""

import json
import os
from pathlib import Path

def load_baseline_configs():
    """Load baseline configuration files"""
    baseline_dir = Path("0_required_inputs/baseline_conf_json")
    
    cu_conf = {}
    du_conf = {}
    ue_conf = {}
    
    # Load CU configuration
    cu_file = baseline_dir / "cu_gnb.json"
    if cu_file.exists():
        with open(cu_file, 'r', encoding='utf-8') as f:
            cu_conf = json.load(f)
    
    # Load DU configuration
    du_file = baseline_dir / "du_gnb.json"
    if du_file.exists():
        with open(du_file, 'r', encoding='utf-8') as f:
            du_conf = json.load(f)
    
    # Load UE configuration
    ue_file = baseline_dir / "ue.json"
    if ue_file.exists():
        with open(ue_file, 'r', encoding='utf-8') as f:
            ue_conf = json.load(f)
    
    return cu_conf, du_conf, ue_conf

def update_json_file(file_path, cu_conf, du_conf, ue_conf):
    """Update a single JSON file with network configuration"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update network_config
        data["network_config"] = {
            "cu_conf": cu_conf,
            "du_conf": du_conf,
            "ue_conf": ue_conf
        }
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all JSON files"""
    # Load baseline configurations
    print("Loading baseline configurations...")
    cu_conf, du_conf, ue_conf = load_baseline_configs()
    
    # Define target directory
    target_dir = Path("Reasoning Trace Input/new_defind_format_1002_1000_case")
    
    # Update CU files
    cu_dir = target_dir / "CU"
    if cu_dir.exists():
        print(f"Updating CU files in {cu_dir}...")
        cu_count = 0
        for file_path in cu_dir.glob("*.json"):
            if update_json_file(file_path, cu_conf, du_conf, ue_conf):
                cu_count += 1
        print(f"Updated {cu_count} CU files")
    
    # Update DU files
    du_dir = target_dir / "DU"
    if du_dir.exists():
        print(f"Updating DU files in {du_dir}...")
        du_count = 0
        for file_path in du_dir.glob("*.json"):
            if update_json_file(file_path, cu_conf, du_conf, ue_conf):
                du_count += 1
        print(f"Updated {du_count} DU files")
    
    print("Network configuration update complete!")

if __name__ == "__main__":
    main()
