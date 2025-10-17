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


def build_cases_delta_index(conf_root: Path) -> Dict[str, Tuple[str, str]]:
    """Scan under conf_root for any cases_delta.json and build an index.

    Returns mapping from filename (e.g., 'ue_case_01.json' or 'ue_case_001.json')
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


def main():
    """Main function: merge UE runlogs and configs."""
    # --- PLEASE UPDATE THESE PATHS FOR YOUR UE WORKSPACE ---
    conf_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/1_conf/ue_conf_1016_175")
    runlog_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/2_runlog_workspace/logs_batch_run_ue_conf_1016_175")
    output_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/3_defined_input_format/new_defind_format_ue_1016_175_case")
    ue_config_root = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/1_confgen_workspace/2_json/ue_conf_1016_175_json")

    
    # ---------------------------------------------------------

    # Baseline JSONs for CU and DU filling
    baseline_dir = Path(r"C:/Users/bmwlab/Desktop/cursor_gen_conf/0_required_inputs/baseline_conf_json")
    cu_baseline_path = baseline_dir / "cu_gnb.json"
    du_baseline_path = baseline_dir / "du_gnb.json"
    try:
        with open(cu_baseline_path, "r", encoding="utf-8") as f:
            cu_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading CU baseline at {cu_baseline_path}: {e}")
        cu_baseline = {}
    try:
        with open(du_baseline_path, "r", encoding="utf-8") as f:
            du_baseline = json.load(f)
    except Exception as e:
        print(f"Error reading DU baseline at {du_baseline_path}: {e}")
        du_baseline = {}

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {conf_root.name} for cases_delta.json...")
    delta_index = build_cases_delta_index(conf_root)
    print(f"Found {len(delta_index)} delta entries")

    print(f"Scanning {runlog_root.name} for tail100_summary.json directories...")
    case_dirs = find_tail100_summary_dirs(runlog_root)
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
        error_value = ""
        for key in filename_key_variants:
            if key in delta_index:
                modified_key, error_value = delta_index[key]
                break

        if modified_key or error_value:
            misconfigured_param = f"{modified_key}={error_value}".strip("=")
        else:
            # A default fallback misconfigured parameter for UE
            misconfigured_param = "supi=imsi-001010000000000"

        case_payload = {
            "misconfigured_param": misconfigured_param,
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