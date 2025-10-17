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


def build_cases_delta_index(conf_root: Path) -> Dict[str, Tuple[str, str]]:
    """Scan under conf_root for any cases_delta.json and build an index.

    Returns mapping from filename (e.g., 'du_case_01.json' or 'du_case_001.json')
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


def save_du_case(output_dir: Path, case_num: int, case_data: dict) -> None:
    """Save a single DU case file using the unified naming convention."""
    subdir = output_dir / "DU"
    subdir.mkdir(parents=True, exist_ok=True)
    output_file = subdir / f"du_case_{case_num:02d}_new_format.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved to {output_file}")

def main():
    """Main function: merge DU runlogs and configs."""
    # --- 請根據您的 DU 專案路徑修改以下路徑 ---
    conf_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/1_conf/du_conf_1009_200")
    runlog_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/2_runlog_workspace/logs_batch_run_du_1009_200")
    output_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/3_defined_input_format/new_defind_format_du_1009_200_case")
    du_config_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/2_json/du_conf_1009_200_json")

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

    print(f"Scanning {conf_root.name} for cases_delta.json...")
    delta_index = build_cases_delta_index(conf_root)
    print(f"Found {len(delta_index)} delta entries")

    print(f"Scanning {runlog_root.name} for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(runlog_root)
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
        error_value = ""
        for key in filename_key_variants:
            if key in delta_index:
                modified_key, error_value = delta_index[key]
                break

        if modified_key or error_value:
            misconfigured_param = f"{modified_key}={error_value}".strip("=")
        else:
            # 修改: 使用一個 DU 相關的預設值
            misconfigured_param = "gNBs.DU_ID=0xFFFFFFFF"

        case_payload = {
            "misconfigured_param": misconfigured_param,
            "logs": log_data,
            "network_config": {
                "cu_conf": cu_baseline, # 修改: CU 使用基準設定
                "du_conf": {},          # 修改: DU 設定留空，待填入
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