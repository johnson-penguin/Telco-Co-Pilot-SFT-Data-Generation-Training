#!/usr/bin/env python3
"""
Aggregate run logs and config deltas to produce the defined input format.

This version scans both:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\1_confgen_workspace
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\2_runlog_workspace

and emits results into:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\3_defined_input_format\\new_defind_format_50_case

Rules:
  - Any directory under 2_runlog_workspace that contains a tail100_summary.json is considered a case directory
  - Case type and number are inferred from directory name patterns like "cu_case_XX" or "du_case_XXX"
  - misconfigured_param is assembled using any cases_delta.json found under 1_confgen_workspace
  - Up to 50 total cases are produced (balanced across CU/DU when possible)
"""

import json
import os
import re
from pathlib import Path
import shutil
from typing import Dict, Tuple, Optional, List

def extract_case_number_from_dirname(dirname):
    """Extract case number from directory name like '20251003_133144_cu_case_01'"""
    match = re.search(r'cu_case_(\d+)$', dirname)
    if match:
        return int(match.group(1))
    
    match = re.search(r'du_case_(\d+)$', dirname)
    if match:
        return int(match.group(1))
    
    return None


def extract_case_type_and_number(dirname: str) -> Tuple[Optional[str], Optional[int]]:
    """Infer case type ("CU" or "DU") and number from dirname.

    Examples:
      20251003_133144_cu_case_01 -> ("CU", 1)
      20251014_024446_du_case_001 -> ("DU", 1)
    """
    # CU
    m = re.search(r"cu_case_(\d+)", dirname, re.IGNORECASE)
    if m:
        try:
            return "CU", int(m.group(1))
        except ValueError:
            pass
    # DU
    m = re.search(r"du_case_(\d+)", dirname, re.IGNORECASE)
    if m:
        try:
            return "DU", int(m.group(1))
        except ValueError:
            pass
    return None, None

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


def build_cases_delta_index(conf_root: Path) -> Dict[str, Tuple[str, str]]:
    """Scan under conf_root for any cases_delta.json and build an index.

    Returns mapping from filename (e.g., 'du_case_001.json' or 'cu_case_01.json')
    to tuple(modified_key, error_value).
    """
    index: Dict[str, Tuple[str, str]] = {}
    for root, dirs, files in os.walk(conf_root):
        for file in files:
            if file == "cases_delta.json":
                full_path = Path(root) / file
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for entry in data:
                                filename = entry.get("filename")
                                modified_key = entry.get("modified_key", "")
                                error_value = entry.get("error_value", "")
                                if filename:
                                    index[filename] = (modified_key, error_value)
                except Exception as e:
                    print(f"Error reading cases_delta.json at {full_path}: {e}")
    return index


def find_tail100_summary_dirs(runlog_root: Path) -> List[Path]:
    """Find all directories under runlog_root that contain tail100_summary.json"""
    results: List[Path] = []
    for root, dirs, files in os.walk(runlog_root):
        if "tail100_summary.json" in files:
            results.append(Path(root))
    return results

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
0

def save_case(output_dir: Path, case_type: str, case_num: int, case_data: dict) -> None:
    """Save a single case file using the unified naming convention."""
    subdir = output_dir / case_type
    subdir.mkdir(parents=True, exist_ok=True)
    prefix = "cu" if case_type == "CU" else "du"
    # Use 2-digit case numbering to match existing examples
    output_file = subdir / f"{prefix}_case_{case_num:02d}_new_format.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved to {output_file}")

def main():
    conf_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/1_conf/du_conf_1014_800")
    runlog_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/2_runlog_workspace/logs_batch_run_du_1014_800")
    output_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/3_defined_input_format/new_defind_format_1014_800_case")
    du_config_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/2_json/du_conf_1014_800_json")

    # Store paths in a dictionary for easy iteration
    paths = {
        "conf_root": conf_root,
        "runlog_root": runlog_root,
        "output_dir": output_dir,
        "du_config_root": du_config_root
    }

    print("🔍 Checking path existence:")
    all_exist = True

    # Check if each path exists
    for name, path in paths.items():
        if path.exists():
            print(f"✅ {name} exists: {path}")
        else:
            print(f"❌ {name} does NOT exist: {path}")
            all_exist = False

    # Summary
    if all_exist:
        print("\n✅ All paths exist. Ready to proceed.")
    else:
        print("\n⚠️ Some paths do not exist. Please verify before continuing.")

    # Baseline JSONs for CU and UE filling
    baseline_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/0_required_inputs/baseline_conf_json")
    cu_baseline_path = baseline_dir / "cu_gnb.json"
    ue_baseline_path = baseline_dir / "ue.json"
    try:
        with open(cu_baseline_path, "r", encoding="utf-8") as f:
            cu_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading CU baseline at {cu_baseline_path}: {e}")
        cu_baseline = {}
    try:
        with open(ue_baseline_path, "r", encoding="utf-8") as f:
            ue_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading UE baseline at {ue_baseline_path}: {e}")
        ue_baseline = {}

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Scanning du_conf_1014_800_json for cases_delta.json...")
    delta_index = build_cases_delta_index(conf_root)
    print(f"Found {len(delta_index)} delta entries")

    print("Scanning logs_batch_run_1014_800_json for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(runlog_root)
    print(f"Found {len(case_dirs)} case directories with tail100_summary.json")

    du_saved = 0

    for case_dir in case_dirs:
        dirname = case_dir.name
        case_type, case_num = extract_case_type_and_number(dirname)
        if not case_type or case_num is None:
            parent_name = case_dir.parent.name
            case_type, case_num = extract_case_type_and_number(parent_name)
        if case_type != "DU" or case_num is None:
            continue

        # Load tail100_summary.json
        summary_path = case_dir / "tail100_summary.json"
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            print(f"Error reading {summary_path}: {e}")
            continue

        # Build misconfigured_param from delta index if available
        filename_key_variants = [
            f"du_case_{case_num:02d}.json",
            f"du_case_{case_num:03d}.json",
        ]

        modified_key = ""
        error_value = ""
        for key in filename_key_variants:
            if key in delta_index:
                modified_key, error_value = delta_index[key]
                break

        # Set misconfigured_param based on which parameter was modified for this case
        if modified_key:
            misconfigured_param = modified_key
        else:
            # Fallback when no delta info is available
            misconfigured_param = "unknown"

        case_payload = {
            "misconfigured_param": misconfigured_param,
            "logs": log_data,
            "network_config": {
                "cu_conf": cu_baseline,
                "du_conf": {},
                "ue_conf": ue_baseline
            }
        }

        # Merge DU per-case config JSON into network_config.du_conf
        # Prefer 3-digit case filenames (e.g., du_case_001.json); fall back to 2-digit if needed
        du_filename_candidates = [
            du_config_root / f"du_case_{case_num:03d}.json",
            du_config_root / f"du_case_{case_num:02d}.json",
        ]
        du_config_data = None
        for candidate in du_filename_candidates:
            if candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        du_config_data = json.load(f)
                except Exception as e:
                    print(f"Error reading DU config {candidate}: {e}")
                break

        if du_config_data is not None:
            case_payload["network_config"]["du_conf"] = du_config_data
        else:
            # If no per-case DU JSON is found, leave du_conf empty
            print(f"Warning: DU config JSON not found for case {case_num:03d}")

        try:
            save_case(output_dir, "DU", case_num, case_payload)
            du_saved += 1
        except Exception as e:
            print(f"Error saving DU case {case_num}: {e}")

    print("\n=== Creating Summary ===")
    create_summary_file(output_dir, 0, du_saved)

    print(f"\n=== Processing Complete ===")
    print(f"Total DU cases processed: {du_saved}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
