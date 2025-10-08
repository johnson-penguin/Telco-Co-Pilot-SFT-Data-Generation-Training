#!/usr/bin/env python3
"""
New merging tool to generate JSON files in the specified format:
- misconfigured_param: The wrong parameter value causing the issue
- logs: Object with "CU", "DU", "UE" arrays of log lines
- network_config: Embed full conf2json outputs per case type
- For cu_case: cu_conf = full 2_conf2json_workspace/cu_conf2json/cu_case_XX.json;
                du_conf = baseline du_gnb.json; ue_conf from baseline ue.json
  - For du_case: du_conf = full 2_conf2json_workspace/du_conf2json/du_case_XX.json;
                cu_conf = baseline cu_gnb.json; ue_conf from baseline ue.json
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any

def extract_network_config_from_logs(logs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract network configuration parameters from logs
    """
    gnb_conf = {}
    ue_conf = {}
    
    # Extract gNB configuration from CU logs
    for log_line in logs.get("CU", []):
        # Extract gNB ID
        if "gNB_CU_id" in log_line:
            match = re.search(r'gNB_CU_id\[0\]\s+(\w+)', log_line)
            if match:
                gnb_conf["gNB_CU_id"] = match.group(1)
        
        # Extract gNB name
        if "gNB_CU_name" in log_line:
            match = re.search(r'gNB_CU_name\[0\]\s+(\S+)', log_line)
            if match:
                gnb_conf["gNB_CU_name"] = match.group(1)
        
        # Extract macro gNB ID
        if "macro gNB id" in log_line:
            match = re.search(r'macro gNB id\s+(\w+)', log_line)
            if match:
                gnb_conf["macro_gNB_id"] = match.group(1)
        
        # Extract cell information
        if "cell PLMN" in log_line:
            match = re.search(r'cell PLMN\s+(\d+\.\d+)\s+Cell ID\s+(\d+)', log_line)
            if match:
                gnb_conf["plmn"] = match.group(1)
                gnb_conf["cell_id"] = match.group(2)
        
        # Extract AMF information
        if "Parsed IPv4 address for NG AMF" in log_line:
            match = re.search(r'Parsed IPv4 address for NG AMF:\s+(\S+)', log_line)
            if match:
                gnb_conf["amf_address"] = match.group(1)
    
    # Extract UE configuration from UE logs
    for log_line in logs.get("UE", []):
        # Extract IMSI
        if "imsi" in log_line.lower():
            match = re.search(r'imsi\s*=\s*["\']?(\d+)["\']?', log_line)
            if match:
                ue_conf["imsi"] = match.group(1)
        
        # Extract frequency information
        if "frequency" in log_line.lower():
            match = re.search(r'frequency[:\s]+(\d+)', log_line)
            if match:
                ue_conf["frequency"] = match.group(1)
        
        # Extract UE IP address
        if "UE IPv4" in log_line:
            match = re.search(r'UE IPv4:\s+(\S+)', log_line)
            if match:
                ue_conf["ipv4"] = match.group(1)
        
        # Extract 5G-GUTI
        if "5G-GUTI" in log_line:
            match = re.search(r'5G-GUTI:\s+AMF pointer\s+(\d+),\s+AMF Set ID\s+(\d+),\s+5G-TMSI\s+(\d+)', log_line)
            if match:
                ue_conf["amf_pointer"] = match.group(1)
                ue_conf["amf_set_id"] = match.group(2)
                ue_conf["tmsi"] = match.group(3)
    
    return {
        "ue_conf": ue_conf,
        "gnb_conf": gnb_conf  # kept for backward compatibility, not used in final embed
    }

def create_misconfigured_param(modified_key: str, error_value: str) -> str:
    """
    Create the misconfigured parameter string
    """
    return f"{modified_key}={error_value}"

def safe_read_json(file_path: Path) -> Any:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_case_number(case_data: Dict[str, Any], fallback_path: Path) -> str:
    # Prefer embedded filename like "cu_case_01.json" → 01
    filename = case_data.get("filename") or fallback_path.name
    m = re.search(r'(?:cu|du)_case_(\d{2})', filename)
    if m:
        return m.group(1)
    # Try non-padded
    m = re.search(r'(?:cu|du)_case_(\d+)', filename)
    if m:
        return f"{int(m.group(1)):02d}"
    return "01"


def process_case_file(case_file_path: Path, case_type: str,
                      baseline_cu_json: Dict[str, Any], baseline_du_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single case file and convert to new format
    """
    with open(case_file_path, 'r', encoding='utf-8') as f:
        case_data = json.load(f)
    
    # Extract the required fields
    misconfigured_param = create_misconfigured_param(
        case_data.get("modified_key", ""),
        case_data.get("error_value", "")
    )
    
    logs = case_data.get("error_log", {})
    
    # Determine case number
    case_num = get_case_number(case_data, case_file_path)

    # Build network_config per rule
    # Use baseline UE json (requested), fallback to logs if missing
    baseline_ue_path = Path("0_required_inputs/baseline_conf_json/ue.json")
    try:
        baseline_ue_json = safe_read_json(baseline_ue_path)
        # Keep as-is under ue_conf
        ue_section = baseline_ue_json
    except Exception:
        ue_section = extract_network_config_from_logs(logs).get("ue_conf", {})

    cu_conf: Dict[str, Any]
    du_conf: Dict[str, Any]

    if case_type == "CU":
        cu_conf_path = Path("2_conf2json_workspace") / "cu_conf2json" / f"cu_case_{case_num}.json"
        cu_conf = safe_read_json(cu_conf_path) if cu_conf_path.exists() else {}
        du_conf = baseline_du_json
    else:  # DU case
        du_conf_path = Path("2_conf2json_workspace") / "du_conf2json" / f"du_case_{case_num}.json"
        du_conf = safe_read_json(du_conf_path) if du_conf_path.exists() else {}
        cu_conf = baseline_cu_json

    network_config = {
        "cu_conf": cu_conf,
        "du_conf": du_conf,
        "ue_conf": ue_section
    }
    
    # Create the new format
    new_format = {
        "misconfigured_param": misconfigured_param,
        "logs": logs,
        "network_config": network_config
    }
    
    return new_format

def process_all_cases() -> None:
    """
    Process all CU and DU cases and save to new_defind_format directory
    """
    # Create output directories
    output_root = Path("new_defind_format")
    output_root.mkdir(exist_ok=True)
    cu_out_dir = output_root / "CU"
    du_out_dir = output_root / "DU"
    cu_out_dir.mkdir(exist_ok=True)
    du_out_dir.mkdir(exist_ok=True)
    # Load baselines once
    baseline_cu_json = safe_read_json(Path("0_required_inputs/baseline_conf_json/cu_gnb.json"))
    baseline_du_json = safe_read_json(Path("0_required_inputs/baseline_conf_json/du_gnb.json"))
    
    # Process CU cases
    cu_cases_dir = Path("sft_data_processing/merged_cu_cases")
    for i in range(1, 26):  # Cases 1-25
        case_file = cu_cases_dir / f"cu_case_{i:02d}_merged.json"
        if case_file.exists():
            print(f"Processing {case_file}")
            new_data = process_case_file(case_file, "CU", baseline_cu_json, baseline_du_json)
            
            # Save to new format
            output_file = cu_out_dir / f"cu_case_{i:02d}_new_format.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            print(f"Saved to {output_file}")
    
    # Process DU cases
    du_cases_dir = Path("sft_data_processing/merged_du_cases")
    for i in range(1, 26):  # Cases 1-25
        case_file = du_cases_dir / f"du_case_{i:02d}_merged.json"
        if case_file.exists():
            print(f"Processing {case_file}")
            new_data = process_case_file(case_file, "DU", baseline_cu_json, baseline_du_json)
            
            # Save to new format
            output_file = du_out_dir / f"du_case_{i:02d}_new_format.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            print(f"Saved to {output_file}")
    
    print(f"\nAll cases processed and saved to {output_root}")

def create_summary():
    """
    Create a summary of all processed cases
    """
    output_root = Path("new_defind_format")
    cu_out_dir = output_root / "CU"
    du_out_dir = output_root / "DU"
    summary = {
        "total_cases": 0,
        "cu_cases": 0,
        "du_cases": 0,
        "cases": []
    }
    
    # Count CU cases
    for i in range(1, 26):
        case_file = cu_out_dir / f"cu_case_{i:02d}_new_format.json"
        if case_file.exists():
            summary["cu_cases"] += 1
            summary["total_cases"] += 1
            summary["cases"].append(str(case_file.relative_to(output_root)))
    
    # Count DU cases
    for i in range(1, 26):
        case_file = du_out_dir / f"du_case_{i:02d}_new_format.json"
        if case_file.exists():
            summary["du_cases"] += 1
            summary["total_cases"] += 1
            summary["cases"].append(str(case_file.relative_to(output_root)))
    
    # Save summary
    summary_file = output_root / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Summary saved to {summary_file}")
    print(f"Total cases processed: {summary['total_cases']}")
    print(f"CU cases: {summary['cu_cases']}")
    print(f"DU cases: {summary['du_cases']}")

if __name__ == "__main__":
    print("Starting new merge tool...")
    process_all_cases()
    create_summary()
    print("Merge tool completed!")
