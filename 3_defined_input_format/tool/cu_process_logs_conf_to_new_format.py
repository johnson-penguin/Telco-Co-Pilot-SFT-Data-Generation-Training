#!/usr/bin/env python3
"""
Aggregate CU run logs and config deltas to produce the defined input format.

This script scans:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\1_confgen_workspace\\cu_conf_1009_200
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\2_runlog_workspace\\logs_batch_run_cu_1002_400

and emits results into:
  - C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\3_defined_input_format\\new_defind_format_cu_1002_400_case

Rules:
  - Any directory under the runlogs root that contains a tail100_summary.json is considered a case directory
  - Case number is inferred from directory name patterns like "cu_case_XX" or "cu_case_XXX"
  - misconfigured_param is assembled using cases_delta.json under the CU config workspace when available
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

    Returns mapping from filename (e.g., 'cu_case_01.json' or 'cu_case_001.json')
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


def save_case(output_dir: Path, case_num: int, case_data: dict) -> None:
    """Save a single CU case file using the unified naming convention."""
    subdir = output_dir / "CU"
    subdir.mkdir(parents=True, exist_ok=True)
    output_file = subdir / f"cu_case_{case_num:02d}_new_format.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved to {output_file}")

def main():
    """Main function: merge CU runlogs and configs."""
    conf_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/1_conf/cu_conf_1016_150")
    runlog_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/2_runlog_workspace/logs_batch_run_cu_conf_1016_150")
    output_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/3_defined_input_format/new_defind_format_cu_1016_150_case")
    cu_config_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/2_json/cu_conf_1016_150_json")

    # Baseline JSONs for DU and UE filling
    baseline_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/0_required_inputs/baseline_conf_json")
    du_baseline_path = baseline_dir / "du_gnb.json"
    ue_baseline_path = baseline_dir / "ue.json"
    try:
        with open(du_baseline_path, "r", encoding="utf-8") as f:
            du_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading DU baseline at {du_baseline_path}: {e}")
        du_baseline = {}
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
    case_dirs = find_tail100_summary_dirs(runlog_root)
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
        error_value = ""
        for key in filename_key_variants:
            if key in delta_index:
                modified_key, error_value = delta_index[key]
                break

        if modified_key or error_value:
            misconfigured_param = f"{modified_key}={error_value}".strip("=")
        else:
            misconfigured_param = "gNBs.gNB_ID=0xFFFFFFFF"

        case_payload = {
            "misconfigured_param": misconfigured_param,
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
            save_case(output_dir, case_num, case_payload)
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


