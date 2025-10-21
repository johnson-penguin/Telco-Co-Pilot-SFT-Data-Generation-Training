#!/usr/bin/env python3
"""
CU Log Aggregation and Formatting Script

This script aggregates Configuration Unit (CU) run logs and configuration delta files
to produce the defined input format for training or analysis.

### Source Directories:
1.  **CU Configuration Root:**
    C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/cu_conf_1009_200
2.  **CU Run Log Root:**
    C:/Users/bmwlab/Desktop/cursor_gen_conf/2_runlog_workspace/logs_batch_run_cu_1002_400

### Output Directory:
Results are emitted into:
C:/Users/bmwlab/Desktop/cursor_gen_conf/3_defined_input_format/new_defind_format_cu_1002_400_case

### Processing Rules:
* **Case Identification:** Any directory under the run logs root that contains a `tail100_summary.json` file is considered a single "case directory."
* **Case Number Inference:** The case number is inferred from directory name patterns (e.g., "cu_case_XX" or "cu_case_XXX").
* **Misconfigured Parameters:** The `misconfigured_param` field is assembled using data from `cases_delta.json` located within the CU configuration workspace, when that file is available.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Tuple, Optional, List


def extract_case_type_and_number(dirname: str) -> Tuple[Optional[str], Optional[int]]:
    """Infer case type ("CU" or "DU") and number from dirname."""
    m = re.search(r"cu_case_(\d+)", dirname, re.IGNORECASE)
    if m:
        try:
            return "CU", int(m.group(1))
        except ValueError:
            pass
    m = re.search(r"du_case_(\d+)", dirname, re.IGNORECASE)
    if m:
        try:
            return "DU", int(m.group(1))
        except ValueError:
            pass
    return None, None


def build_cases_delta_index(conf_root: Path) -> Dict[str, Tuple[str, str, str]]:
    """Scan under conf_root for any cases_delta.json and build an index.

    Returns mapping from filename (e.g., 'cu_case_01.json' or 'cu_case_001.json')
    to tuple(modified_key, original_value, error_value).
    """
    index: Dict[str, Tuple[str, str, str]] = {}
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
                                original_value = entry.get("original_value", "")
                                error_value = entry.get("error_value", "")
                                if filename:
                                    index[filename] = (modified_key, original_value, error_value)
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


def save_cu_case(output_dir: Path, case_num: int, case_data: dict) -> None:
    """Save a single CU case file using the unified naming convention."""
    subdir = output_dir / "CU"
    subdir.mkdir(parents=True, exist_ok=True)
    output_file = subdir / f"cu_case_{case_num:02d}_new_format.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved to {output_file}")


def get_value_from_json_path(data: dict, path: str):
    """
    Traverse a nested dict/list structure using a dot-separated path.
    Handles list indices (e.g., 'gNBs.0.gNB_ID').
    """
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and key.isdigit():
            try:
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None  # Index out of bounds
            except ValueError:
                return None  # Should not happen if isdigit() is true
        else:
            return None  # Key not found or unexpected structure
        
        if current is None:
            return None  # Path ended early
    return current


def main():
    """Main function: merge CU runlogs and configs."""

    BASE_DIR = Path(__file__).resolve().parent
    # 專案根目錄：從 BASE_DIR 往上退兩層
    # C:\Users\wasd0\Desktop\Telco-Co-Pilot-SFT-Data-Generation-Training\
    PROJECT_ROOT = BASE_DIR.parent.parent 
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")

    # 使用 PROJECT_ROOT 搭配相對路徑
    conf_root = PROJECT_ROOT / "1_confgen_workspace/1_conf/cu_conf_1009_200"
    cu_config_root = PROJECT_ROOT / "1_confgen_workspace/2_json/cu_conf_1009_200_json"
    runlog_root_for_scan = PROJECT_ROOT / "2_runlog_workspace/logs_batch_run_cu_1009_200"
    output_dir = PROJECT_ROOT / "3_defined_input_format/new_defind_format_cu_1009_200_case"

    
    # Baseline JSONs for DU, UE, and CU filling
    baseline_dir = PROJECT_ROOT / "0_required_inputs/baseline_conf_json"

    du_baseline_path = baseline_dir / "du_gnb.json"
    ue_baseline_path = baseline_dir / "ue.json"

    # 載入 DU 基準配置
    try:
        with open(du_baseline_path, "r", encoding="utf-8") as f:
            du_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading DU baseline at {du_baseline_path}: {e}")
        du_baseline = {}
        
    # 載入 UE 基準配置
    try:
        with open(ue_baseline_path, "r", encoding="utf-8") as f:
            ue_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading UE baseline at {ue_baseline_path}: {e}")
        ue_baseline = {}
        

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Scanning cu_conf_1009_200 for cases_delta.json...")
    delta_index = build_cases_delta_index(conf_root)
    print(f"Found {len(delta_index)} delta entries")

    print("Scanning logs_batch_run_cu_1002_400 for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(runlog_root_for_scan) # NOTE: 這裡我調整了掃描路徑以符合註釋中的 C:\Users\bmwlab\Desktop\cursor_gen_conf\2_runlog_workspace\logs_batch_run_cu_1002_400
    print(f"Found {len(case_dirs)} case directories with tail100_summary.json")

    cu_saved = 0

    for case_dir in case_dirs:
        dirname = case_dir.name
        case_type, case_num = extract_case_type_and_number(dirname)
        if not case_type or case_num is None:
            parent_name = case_dir.parent.name
            case_type, case_num = extract_case_type_and_number(parent_name)
        if case_type != "CU" or case_num is None:
            continue

        summary_path = case_dir / "tail100_summary.json"
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            print(f"Error reading {summary_path}: {e}")
            continue

        filename_key_variants = [
            f"cu_case_{case_num:02d}.json",
            f"cu_case_{case_num:03d}.json",
        ]

        modified_key = ""
        original_value = ""
        error_value = ""

        for key in filename_key_variants:
            if key in delta_index:
                # 變更 tuple 解包方式
                modified_key, original_value, error_value = delta_index[key]
                break

        original_param = ""
        misconfigured_param = ""

        if modified_key or error_value:
            # misconfigured_param 依然使用 error_value
            misconfigured_param = f"{modified_key}={error_value}".strip("=")
            
            # === 使用提取到的 original_value 建構 Original_param ===
            original_param = f"{modified_key}={original_value}".strip("=")
            # =======================================================
        
        else:
            # 處理預設錯誤值的情況
            misconfigured_param = "gNBs.gNB_ID=0xFFFFFFFF"
            # 針對預設錯誤，嘗試查找 gNB_ID 的原始參數 (假設路徑為 gNBs.0.gNB_ID)
            default_key = "gNBs.0.gNB_ID" 
            default_original_value = get_value_from_json_path(cu_baseline, default_key)
            if default_original_value is not None:
                original_param = f"{default_key}={default_original_value}"
            else:
                original_param = "gNBs.gNB_ID=<CORRECT_DEFAULT_ID_NOT_FOUND>"


        case_payload = {
            "misconfigured_param": misconfigured_param,
            "original_param": original_param,
            "logs": log_data,
            "network_config": {
                "cu_conf": {},
                "du_conf": du_baseline,
                "ue_conf": ue_baseline
            }
        }

        # Merge CU per-case config JSON into network_config.cu_conf
        cu_filename_candidates = [
            cu_config_root / f"cu_case_{case_num:03d}.json",
            cu_config_root / f"cu_case_{case_num:02d}.json",
            cu_config_root / f"cu_case_{case_num}.json",
        ]
        cu_config_data = None
        for candidate in cu_filename_candidates:
            if candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        cu_config_data = json.load(f)
                except Exception as e:
                    print(f"Error reading CU config {candidate}: {e}")
                break

        if cu_config_data is not None:
            case_payload["network_config"]["cu_conf"] = cu_config_data
        else:
            print(f"Warning: CU config JSON not found for case {case_num:03d}")

        try:
            save_cu_case(output_dir, case_num, case_payload)
            cu_saved += 1
        except Exception as e:
            print(f"Error saving CU case {case_num}: {e}")

    # summary
    summary = {"CU": cu_saved, "DU": 0}
    summary_file = output_dir / "summary.json"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Created summary.json: CU={cu_saved}, DU=0")
    except Exception as e:
        print(f"Error writing summary.json: {e}")

    print(f"\n=== Processing Complete ===")
    print(f"Total CU cases processed: {cu_saved}")
    print(f"Output directory: {output_dir}")



if __name__ == "__main__":
    main()