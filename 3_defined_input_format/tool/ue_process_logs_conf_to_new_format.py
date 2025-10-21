#!/usr/bin/env python3
"""
Aggregate UE run logs and config deltas to produce the defined input format.

This script scans:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\1_confgen_workspace\\ue_conf_YYYY_ZZZ
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\2_runlog_workspace\\logs_batch_run_ue_YYYY_ZZZ

and emits results into:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\3_defined_input_format\\new_defind_format_ue_YYYY_ZZZ_case

Rules:
  - Any directory under the runlogs root that contains a tail100_summary.json is considered a case directory
  - Case number is inferred from directory name patterns like "ue_case_XX" or "ue_case_XXX"
  - misconfigured_param is assembled using cases_delta.json under the UE config workspace when available
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Tuple, Optional, List


def extract_case_type_and_number(dirname: str) -> Tuple[Optional[str], Optional[int]]:
    """Infer case type ("CU", "DU", or "UE") and number from dirname."""
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
    m = re.search(r"ue_case_(\d+)", dirname, re.IGNORECASE)
    if m:
        try:
            return "UE", int(m.group(1))
        except ValueError:
            pass
    return None, None


def build_cases_delta_index(conf_root: Path) -> Dict[str, Tuple[str, str, str]]:
    """Scan under conf_root for any cases_delta.json and build an index.

    Returns mapping from filename (e.g., 'ue_case_01.json' or 'ue_case_001.json')
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


def save_case(output_dir: Path, case_type: str, case_num: int, case_data: dict) -> None:
    """Save a single case file using the unified naming convention."""
    case_type_upper = case_type.upper()
    case_type_lower = case_type.lower()
    subdir = output_dir / case_type_upper
    subdir.mkdir(parents=True, exist_ok=True)
    output_file = subdir / f"{case_type_lower}_case_{case_num:02d}_new_format.json"
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
    """Main function: merge UE runlogs and configs."""

    BASE_DIR = Path(__file__).resolve().parent
    # 專案根目錄：從 BASE_DIR 往上退兩層
    # C:\Users\wasd0\Desktop\Telco-Co-Pilot-SFT-Data-Generation-Training\
    PROJECT_ROOT = BASE_DIR.parent.parent 
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")

    # 使用 PROJECT_ROOT 搭配相對路徑
    conf_root = PROJECT_ROOT / "1_confgen_workspace/1_conf/ue_conf_1016_175"
    ue_config_root = PROJECT_ROOT / "1_confgen_workspace/2_json/ue_conf_1016_175_json"
    runlog_root_for_scan = PROJECT_ROOT / "2_runlog_workspace/logs_batch_run_ue_conf_1016_175"
    output_dir = PROJECT_ROOT / "3_defined_input_format/new_defind_format_ue_1016_175_case"

    
    # Baseline JSONs for CU and DU filling
    baseline_dir = PROJECT_ROOT / "0_required_inputs/baseline_conf_json"
    cu_baseline_path = baseline_dir / "cu_gnb.json"
    du_baseline_path = baseline_dir / "du_gnb.json"
    # 載入 CU 基準配置
    try:
        with open(cu_baseline_path, "r", encoding="utf-8") as f:
            cu_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading CU baseline at {cu_baseline_path}: {e}")
        cu_baseline = {}
        
    # 載入 DU 基準配置
    try:
        with open(du_baseline_path, "r", encoding="utf-8") as f:
            du_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading DU baseline at {du_baseline_path}: {e}")
        du_baseline = {}

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Scanning ue_conf_1016_175 for cases_delta.json...")
    delta_index = build_cases_delta_index(conf_root)
    print(f"Found {len(delta_index)} delta entries")

    print("Scanning logs_batch_run_ue_conf_1016_175 for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(runlog_root_for_scan)
    print(f"Found {len(case_dirs)} case directories with tail100_summary.json")

    ue_saved = 0

    for case_dir in case_dirs:
        dirname = case_dir.name
        case_type, case_num = extract_case_type_and_number(dirname)
        if not case_type or case_num is None:
            parent_name = case_dir.parent.name
            case_type, case_num = extract_case_type_and_number(parent_name)
        if case_type != "UE" or case_num is None:
            continue

        summary_path = case_dir / "tail100_summary.json"
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            print(f"Error reading {summary_path}: {e}")
            continue

        filename_key_variants = [
            f"ue_case_{case_num:02d}.json",
            f"ue_case_{case_num:03d}.json",
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
            # 找不到具體的錯誤參數時，使用 none
            misconfigured_param = "none"
            original_param = "none"

        case_payload = {
            "misconfigured_param": misconfigured_param,
            "correct_param": original_param,
            "logs": log_data,
            "network_config": {
                "cu_conf": cu_baseline,
                "du_conf": du_baseline,
                "ue_conf": {}
            }
        }

        # Merge UE per-case config JSON into network_config.ue_conf
        ue_filename_candidates = [
            ue_config_root / f"ue_case_{case_num:03d}.json",
            ue_config_root / f"ue_case_{case_num:02d}.json",
            ue_config_root / f"ue_case_{case_num}.json",
        ]
        ue_config_data = None
        for candidate in ue_filename_candidates:
            if candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        ue_config_data = json.load(f)
                except Exception as e:
                    print(f"Error reading UE config {candidate}: {e}")
                break

        if ue_config_data is not None:
            case_payload["network_config"]["ue_conf"] = ue_config_data
        else:
            print(f"Warning: UE config JSON not found for case {case_num:03d}")

        try:
            save_case(output_dir, case_type, case_num, case_payload)
            ue_saved += 1
        except Exception as e:
            print(f"Error saving UE case {case_num}: {e}")

    # summary
    summary = {"UE": ue_saved, "CU": 0, "DU": 0}
    summary_file = output_dir / "summary.json"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Created summary.json: UE={ue_saved}, CU=0, DU=0")
    except Exception as e:
        print(f"Error writing summary.json: {e}")

    print(f"\n=== Processing Complete ===")
    print(f"Total UE cases processed: {ue_saved}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()