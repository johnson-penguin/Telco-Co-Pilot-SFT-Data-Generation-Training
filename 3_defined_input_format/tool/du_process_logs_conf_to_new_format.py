#!/usr/bin/env python3
"""
Aggregate DU run logs and config deltas to produce the defined input format.

This script scans:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\1_confgen_workspace\\du_conf_...
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\2_runlog_workspace\\logs_batch_run_du_...

and emits results into:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\3_defined_input_format\\new_defind_format_du_..._case

Rules:
  - Any directory under the runlogs root that contains a tail100_summary.json is considered a case directory
  - Case number is inferred from directory name patterns like "du_case_XX" or "du_case_XXX"
  - misconfigured_param is assembled using cases_delta.json under the DU config workspace when available
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

    Returns mapping from filename (e.g., 'du_case_01.json' or 'du_case_001.json')
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


def save_du_case(output_dir: Path, case_num: int, case_data: dict) -> None:
    """Save a single DU case file using the unified naming convention."""
    subdir = output_dir / "DU"
    subdir.mkdir(parents=True, exist_ok=True)
    output_file = subdir / f"du_case_{case_num:02d}_new_format.json"
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
    """Main function: merge DU runlogs and configs."""

    BASE_DIR = Path(__file__).resolve().parent
    # 專案根目錄：從 BASE_DIR 往上退兩層
    # C:\Users\wasd0\Desktop\Telco-Co-Pilot-SFT-Data-Generation-Training\
    PROJECT_ROOT = BASE_DIR.parent.parent 
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")

    # 使用 PROJECT_ROOT 搭配相對路徑
    conf_root = PROJECT_ROOT / "1_confgen_workspace/1_conf/du_conf_1001_200"
    du_config_root = PROJECT_ROOT / "1_confgen_workspace/2_json/du_conf_1001_200_json"
    runlog_root_for_scan = PROJECT_ROOT / "2_runlog_workspace/logs_batch_run_du_1001_200"
    output_dir = PROJECT_ROOT / "3_defined_input_format/new_defind_format_du_1001_200_case"

    
    # Baseline JSONs for CU, UE, and DU filling
    baseline_dir = PROJECT_ROOT / "0_required_inputs/baseline_conf_json"

    cu_baseline_path = baseline_dir / "cu_gnb.json"
    ue_baseline_path = baseline_dir / "ue.json"
    # 載入 CU 基準配置
    try:
        with open(cu_baseline_path, "r", encoding="utf-8") as f:
            cu_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading CU baseline at {cu_baseline_path}: {e}")
        cu_baseline = {}
        
    # 載入 UE 基準配置
    try:
        with open(ue_baseline_path, "r", encoding="utf-8") as f:
            ue_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading UE baseline at {ue_baseline_path}: {e}")
        ue_baseline = {}

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Scanning du_conf_1009_200 for cases_delta.json...")
    delta_index = build_cases_delta_index(conf_root)
    print(f"Found {len(delta_index)} delta entries")

    print("Scanning logs_batch_run_du_1009_200 for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(runlog_root_for_scan)
    print(f"Found {len(case_dirs)} case directories with tail100_summary.json")

    du_saved = 0

    for case_dir in case_dirs:
        dirname = case_dir.name
        case_type, case_num = extract_case_type_and_number(dirname)
        if not case_type or case_num is None:
            parent_name = case_dir.parent.name
            case_type, case_num = extract_case_type_and_number(parent_name)
        
        # 修改: 只處理 DU 案例
        if case_type != "DU" or case_num is None:
            continue

        summary_path = case_dir / "tail100_summary.json"
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            print(f"Error reading {summary_path}: {e}")
            continue

        # 修改: 尋找 DU 案例的檔名
        filename_key_variants = [
            f"du_case_{case_num:02d}.json",
            f"du_case_{case_num:03d}.json",
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
            "original_param": original_param,
            "logs": log_data,
            "network_config": {
                "cu_conf": cu_baseline,
                "du_conf": {},
                "ue_conf": ue_baseline
            }
        }

        # Merge DU per-case config JSON into network_config.du_conf
        du_filename_candidates = [
            du_config_root / f"du_case_{case_num:03d}.json",
            du_config_root / f"du_case_{case_num:02d}.json",
            du_config_root / f"du_case_{case_num}.json",
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
            # 修改: 將 DU 設定填入 payload
            case_payload["network_config"]["du_conf"] = du_config_data
        else:
            print(f"Warning: DU config JSON not found for case {case_num:03d}")

        try:
            # 修改: 呼叫儲存 DU 案例的函式
            save_du_case(output_dir, case_num, case_payload)
            du_saved += 1
        except Exception as e:
            print(f"Error saving DU case {case_num}: {e}")

    # summary
    # 修改: 產生 DU 的摘要
    summary = {"CU": 0, "DU": du_saved}
    summary_file = output_dir / "summary.json"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Created summary.json: CU=0, DU={du_saved}")
    except Exception as e:
        print(f"Error writing summary.json: {e}")

    print(f"\n=== Processing Complete ===")
    print(f"Total DU cases processed: {du_saved}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()