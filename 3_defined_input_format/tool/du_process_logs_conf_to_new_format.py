#!/usr/bin/env python3
"""
Aggregate DU run logs and configs.
Compares with baseline to find misconfigured_param.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any


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

def find_tail100_summary_dirs(runlog_root: Path) -> List[Path]:
    """Find all directories under runlog_root that contain tail100_summary.json"""
    results: List[Path] = []
    if not runlog_root.exists():
        print(f"Warning: runlog_root directory not found: {runlog_root}")
        return results

    for root, dirs, files in os.walk(runlog_root):
        if "tail100_summary.json" in files:
            results.append(Path(root))
    return results


def save_du_case(output_dir: Path, case_num: int, case_data: dict) -> None:
    """Save a single DU case file using the unified naming convention."""
    subdir = output_dir / "DU"
    subdir.mkdir(parents=True, exist_ok=True)
    output_file = subdir / f"du_case_{case_num:03d}_new_format.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    print(f"    -> Saved to {output_file}")


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

# --- NEW: Function to find the first difference ---
def find_first_diff_recursive(baseline: Any, current: Any, path: str = "") -> Optional[Tuple[str, Any, Any]]:
    """
    Recursively compares two nested structures (dicts/lists) and returns
    the first difference found.
    Returns: (path, baseline_value, current_value) or None
    """
    
    # 比較字典
    if isinstance(baseline, dict) and isinstance(current, dict):
        # 檢查 baseline 中的 key
        for key in baseline:
            current_path = f"{path}.{key}" if path else key
            
            if key not in current:
                return (current_path, baseline[key], "[MISSING]") # 參數被刪除
            
            b_val = baseline[key]
            c_val = current[key]
            
            # 遞迴進入
            if isinstance(b_val, (dict, list)) and isinstance(c_val, (dict, list)):
                diff = find_first_diff_recursive(b_val, c_val, current_path)
                if diff:
                    return diff
            # 找到值的差異
            elif b_val != c_val:
                return (current_path, b_val, c_val)

        # 檢查 current 中多出來的 key
        for key in current:
            if key not in baseline:
                current_path = f"{path}.{key}" if path else key
                return (current_path, "[ADDED]", current[key]) # 參數是新增的

    # 比較列表
    elif isinstance(baseline, list) and isinstance(current, list):
        if len(baseline) != len(current):
            return (path, f"list[len={len(baseline)}]", f"list[len={len(current)}]") # 列表長度不同
        
        for i in range(len(baseline)):
            current_path = f"{path}.{i}" # 使用 .0, .1 標記列表索引
            
            b_val = baseline[i]
            c_val = current[i]
            
            # 遞迴進入
            if isinstance(b_val, (dict, list)) and isinstance(c_val, (dict, list)):
                diff = find_first_diff_recursive(b_val, c_val, current_path)
                if diff:
                    return diff
            # 找到值的差異
            elif b_val != c_val:
                return (current_path, b_val, c_val)

    # 比較基本類型 (string, int, bool, etc.)
    elif baseline != current:
        return (path, baseline, current)
        
    return None # 沒有找到差異
# --- *** END NEW *** ---

def main():
    """Main function: merge DU runlogs and configs."""

    BASE_DIR = Path(__file__).resolve().parent
    # 專案根目錄：從 BASE_DIR 往上退兩層
    # C:\Users\wasd0\Desktop\Telco-Co-Pilot-SFT-Data-Generation-Training\
    PROJECT_ROOT = BASE_DIR.parent.parent 
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")

    # 使用 PROJECT_ROOT 搭配相對路徑
    conf_root = PROJECT_ROOT / "1_confgen_workspace/1_conf/du_conf_1114_30"
    du_config_root = PROJECT_ROOT / "1_confgen_workspace/2_json/du_conf_1114_30_json"
    runlog_root_for_scan = PROJECT_ROOT / "2_runlog_workspace/logs_batch_run_1114_30"
    output_dir = PROJECT_ROOT / "3_defined_input_format/new_defind_format_du_1114_30_case"

    
    cu_baseline_path = baseline_dir / "cu_gnb.json"
    ue_baseline_path = baseline_dir / "ue.json"
    # --- NEW: Define DU baseline path ---
    du_baseline_path = baseline_dir / "du_gnb.json"
    # --- *** END NEW ---

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
    
    # --- NEW: Load DU baseline config ---
    try:
        with open(du_baseline_path, "r", encoding="utf-8") as f:
            du_baseline = json.load(f)
        print(f"Successfully loaded DU baseline from {du_baseline_path}")
    except Exception as e:
        print(f"Error reading DU baseline at {du_baseline_path}: {e}")
        print("!!! Warning: DU baseline failed to load. Diff logic will be skipped. !!!")
        du_baseline = None # 設置為 None 以便後續檢查
    # --- *** END NEW *** ---

    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Scanning for logs ---
    print(f"Scanning {du_runlog_root} for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(du_runlog_root)
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

        # --- Reading log data ---
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
            du_json_conf_root / f"du_case_{case_num:03d}.json",
            du_json_conf_root / f"du_case_{case_num:02d}.json",
            du_json_conf_root / f"du_case_{case_num}.json",
        ]
        du_config_data = None
        du_config_path = None
        for candidate in du_filename_candidates:
            if candidate.exists():
                du_config_path = candidate
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        du_config_data = json.load(f)
                except Exception as e:
                    print(f"Error reading DU config {candidate}: {e}")
                break
        
        if du_config_data is None:
            print(f"Warning: DU config JSON not found for case {case_num:03d}")

        # 2. 初始化 diff 欄位
        misconfigured_param = "none"
        correct_param = "none" 

        # 3. 執行 diff (前提是 baseline 和 case config 都已載入)
        if du_config_data is not None and du_baseline is not None:
            print(f"Comparing {du_config_path.name} with {du_baseline_path.name}...")
            diff_result = find_first_diff_recursive(du_baseline, du_config_data)
            
            if diff_result:
                path, baseline_val, current_val = diff_result
                misconfigured_param = f"{path}={current_val}"
                correct_param = f"{path}={baseline_val}"
                print(f"  Found diff: {correct_param} -> {misconfigured_param}")
            else:
                print(f"  No difference found between case {case_num:03d} and baseline.")
                # 如果沒有差異，可以選擇填入 "none" 或其他標記
                misconfigured_param = "no_diff" 
                correct_param = "no_diff"
        
        elif du_baseline is None:
            print(f"Skipping diff for case {case_num:03d} (DU baseline not loaded).")
        # --- *** END MODIFIED *** ---

        # 4. 建立 payload
        case_payload = {
            "misconfigured_param": misconfigured_param,
            "correct_param": correct_param,
            "logs": log_data,
            "network_config": {
                "cu_conf": cu_baseline,
                "du_conf": du_config_data if du_config_data is not None else {}, # 填入 DU 設定
                "ue_conf": ue_baseline
            }
        }

        try:
            save_du_case(output_dir, case_num, case_payload)
            du_saved += 1
        except Exception as e:
            print(f"Error saving DU case {case_num}: {e}")

    # summary
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