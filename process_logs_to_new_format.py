#!/usr/bin/env python3
"""
Process log files from logs_batch_run_cu_1002_400 and logs_batch_run_du_1002_600
and generate new format files in new_defind_format_1002_1000_case directory
"""

import json
import os
import re
from pathlib import Path
import shutil

def extract_case_number_from_dirname(dirname):
    """Extract case number from directory name like '20251003_133144_cu_case_01'"""
    match = re.search(r'cu_case_(\d+)$', dirname)
    if match:
        return int(match.group(1))
    
    match = re.search(r'du_case_(\d+)$', dirname)
    if match:
        return int(match.group(1))
    
    return None

def read_log_file(file_path):
    """Read log file and return content as list of lines"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def process_cu_case(cu_log_dir, case_num):
    """Process a single CU case directory"""
    case_data = {
        "misconfigured_param": f"gNBs.gNB_ID=0xFFFFFFFF",  # Default misconfigured parameter
        "logs": {
            "CU": [],
            "DU": [],
            "UE": []
        },
        "network_config": {
            "cu_conf": {},
            "du_conf": {},
            "ue_conf": {}
        }
    }
    
    # Read CU logs
    cu_log_file = cu_log_dir / "cu.stdout.log"
    if cu_log_file.exists():
        cu_logs = read_log_file(cu_log_file)
        case_data["logs"]["CU"] = [line.rstrip('\n') for line in cu_logs]
    
    # Read DU logs
    du_log_file = cu_log_dir / "du.stdout.log"
    if du_log_file.exists():
        du_logs = read_log_file(du_log_file)
        case_data["logs"]["DU"] = [line.rstrip('\n') for line in du_logs]
    
    # Read UE logs
    ue_log_file = cu_log_dir / "ue.stdout.log"
    if ue_log_file.exists():
        ue_logs = read_log_file(ue_log_file)
        case_data["logs"]["UE"] = [line.rstrip('\n') for line in ue_logs]
    
    # Try to read configuration from tail100_summary.json if available
    summary_file = cu_log_dir / "tail100_summary.json"
    if summary_file.exists():
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
                # Extract logs from summary if available
                if "CU" in summary_data:
                    case_data["logs"]["CU"] = summary_data["CU"]
                if "DU" in summary_data:
                    case_data["logs"]["DU"] = summary_data["DU"]
                if "UE" in summary_data:
                    case_data["logs"]["UE"] = summary_data["UE"]
        except Exception as e:
            print(f"Error reading summary file {summary_file}: {e}")
    
    return case_data

def process_du_case(du_log_dir, case_num):
    """Process a single DU case directory"""
    case_data = {
        "misconfigured_param": f"Asn1_verbosity=debug",  # Default misconfigured parameter for DU
        "logs": {
            "CU": [],
            "DU": [],
            "UE": []
        },
        "network_config": {
            "cu_conf": {},
            "du_conf": {},
            "ue_conf": {}
        }
    }
    
    # Read CU logs
    cu_log_file = du_log_dir / "cu.stdout.log"
    if cu_log_file.exists():
        cu_logs = read_log_file(cu_log_file)
        case_data["logs"]["CU"] = [line.rstrip('\n') for line in cu_logs]
    
    # Read DU logs
    du_log_file = du_log_dir / "du.stdout.log"
    if du_log_file.exists():
        du_logs = read_log_file(du_log_file)
        case_data["logs"]["DU"] = [line.rstrip('\n') for line in du_logs]
    
    # Read UE logs
    ue_log_file = du_log_dir / "ue.stdout.log"
    if ue_log_file.exists():
        ue_logs = read_log_file(ue_log_file)
        case_data["logs"]["UE"] = [line.rstrip('\n') for line in ue_logs]
    
    # Try to read configuration from tail100_summary.json if available
    summary_file = du_log_dir / "tail100_summary.json"
    if summary_file.exists():
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
                # Extract logs from summary if available
                if "CU" in summary_data:
                    case_data["logs"]["CU"] = summary_data["CU"]
                if "DU" in summary_data:
                    case_data["logs"]["DU"] = summary_data["DU"]
                if "UE" in summary_data:
                    case_data["logs"]["UE"] = summary_data["UE"]
        except Exception as e:
            print(f"Error reading summary file {summary_file}: {e}")
    
    return case_data

def process_cu_logs(cu_logs_dir, output_dir):
    """Process all CU log directories"""
    cu_output_dir = output_dir / "CU"
    cu_output_dir.mkdir(parents=True, exist_ok=True)
    
    cu_cases = []
    processed_count = 0
    
    # Get all CU case directories
    for item in cu_logs_dir.iterdir():
        if item.is_dir() and "cu_case_" in item.name:
            case_num = extract_case_number_from_dirname(item.name)
            if case_num is not None:
                cu_cases.append((case_num, item))
    
    # Sort by case number
    cu_cases.sort(key=lambda x: x[0])
    
    print(f"Found {len(cu_cases)} CU cases")
    
    for case_num, case_dir in cu_cases:
        print(f"Processing CU case {case_num}...")
        
        try:
            case_data = process_cu_case(case_dir, case_num)
            
            # Save to output directory
            output_file = cu_output_dir / f"cu_case_{case_num:02d}_new_format.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, indent=2, ensure_ascii=False)
            
            processed_count += 1
            print(f"  -> Saved to {output_file}")
            
        except Exception as e:
            print(f"  -> Error processing CU case {case_num}: {e}")
    
    print(f"Processed {processed_count} CU cases")
    return processed_count

def process_du_logs(du_logs_dir, output_dir):
    """Process all DU log directories"""
    du_output_dir = output_dir / "DU"
    du_output_dir.mkdir(parents=True, exist_ok=True)
    
    du_cases = []
    processed_count = 0
    
    # Get all DU case directories
    for item in du_logs_dir.iterdir():
        if item.is_dir() and "du_case_" in item.name:
            case_num = extract_case_number_from_dirname(item.name)
            if case_num is not None:
                du_cases.append((case_num, item))
    
    # Sort by case number
    du_cases.sort(key=lambda x: x[0])
    
    print(f"Found {len(du_cases)} DU cases")
    
    for case_num, case_dir in du_cases:
        print(f"Processing DU case {case_num}...")
        
        try:
            case_data = process_du_case(case_dir, case_num)
            
            # Save to output directory
            output_file = du_output_dir / f"du_case_{case_num:02d}_new_format.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, indent=2, ensure_ascii=False)
            
            processed_count += 1
            print(f"  -> Saved to {output_file}")
            
        except Exception as e:
            print(f"  -> Error processing DU case {case_num}: {e}")
    
    print(f"Processed {processed_count} DU cases")
    return processed_count

def create_summary_file(output_dir, cu_count, du_count):
    """Create summary.json file"""
    summary = {
        "CU": cu_count,
        "DU": du_count
    }
    
    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Created summary.json: CU={cu_count}, DU={du_count}")

def main():
    """Main function"""
    # Define paths
    cu_logs_dir = Path("C:/Users/bmwlab/Desktop/cursor_gen_conf/sft_data_processing/logs_batch_run_cu_1002_400")
    du_logs_dir = Path("C:/Users/bmwlab/Desktop/cursor_gen_conf/sft_data_processing/logs_batch_run_du_1002_600")
    output_dir = Path("C:/Users/bmwlab/Desktop/cursor_gen_conf/Reasoning Trace Input/new_defind_format_1002_1000_case")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Processing log files...")
    print(f"CU logs directory: {cu_logs_dir}")
    print(f"DU logs directory: {du_logs_dir}")
    print(f"Output directory: {output_dir}")
    
    # Process CU logs
    print("\n=== Processing CU Logs ===")
    cu_count = process_cu_logs(cu_logs_dir, output_dir)
    
    # Process DU logs
    print("\n=== Processing DU Logs ===")
    du_count = process_du_logs(du_logs_dir, output_dir)
    
    # Create summary file
    print("\n=== Creating Summary ===")
    create_summary_file(output_dir, cu_count, du_count)
    
    print(f"\n=== Processing Complete ===")
    print(f"Total CU cases processed: {cu_count}")
    print(f"Total DU cases processed: {du_count}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
