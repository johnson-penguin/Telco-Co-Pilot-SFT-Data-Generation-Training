#!/usr/bin/env python3
"""
Filter tool to extract cases that do NOT contain the success message:
"Received PDU Session Establishment Accept"
and also skip those containing "Received PDU Session Establishment reject"

This script will:
1. Scan all JSON files in the new_defind_format_1002_1000_case directory
2. Skip files containing either the success or reject message
3. Copy files WITHOUT both messages to the filter_defind_format_1002_1000_case directory
4. Maintain the same directory structure (CU/DU/UE)
"""

import os
import json
import shutil

def contains_message(file_path, pattern):
    """Check if a JSON file contains the given message pattern."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'logs' not in data:
            return False

        for unit in ['CU', 'DU', 'UE']:
            if unit in data['logs']:
                for log_line in data['logs'][unit]:
                    if pattern in log_line:
                        return True
        return False

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False


def create_output_directory(output_base_dir):
    """Create the output directory structure."""
    os.makedirs(os.path.join(output_base_dir, 'CU'), exist_ok=True)
    os.makedirs(os.path.join(output_base_dir, 'DU'), exist_ok=True)
    os.makedirs(os.path.join(output_base_dir, 'UE'), exist_ok=True)
    print(f"Created output directories under {output_base_dir}")


def filter_cases(input_dir, output_dir, success_pattern, reject_pattern):
    """Filter cases that do NOT contain success or reject messages."""
    create_output_directory(output_dir)

    total_files = 0
    filtered_files = 0
    cu_filtered = 0
    du_filtered = 0
    ue_filtered = 0

    for unit in ['CU', 'DU', 'UE']:
        input_subdir = os.path.join(input_dir, unit)
        output_subdir = os.path.join(output_dir, unit)

        if not os.path.exists(input_subdir):
            continue

        print(f"\nProcessing {unit} directory: {input_subdir}")
        for filename in os.listdir(input_subdir):
            if not filename.endswith('.json'):
                continue

            total_files += 1
            file_path = os.path.join(input_subdir, filename)

            # 檢查是否含有 Accept 或 reject
            has_success = contains_message(file_path, success_pattern)
            has_reject = contains_message(file_path, reject_pattern)

            if not has_success and not has_reject:
                shutil.copy2(file_path, os.path.join(output_subdir, filename))
                print(f"  [FILTERED] {filename}")
                filtered_files += 1
                if unit == 'CU':
                    cu_filtered += 1
                elif unit == 'DU': 
                    du_filtered += 1
                elif unit == 'UE': 
                    ue_filtered += 1
            else:
                reason = "success" if has_success else "reject"
                print(f"  [SKIPPED-{reason.upper()}] {filename}")

    # 統計輸出
    print("\n" + "="*60)
    print("FILTERING SUMMARY")
    print("="*60)
    print(f"Total files processed: {total_files}")
    print(f"Files WITHOUT success/reject message: {filtered_files}")
    print(f"  - CU cases: {cu_filtered}")
    print(f"  - DU cases: {du_filtered}")
    print(f"  - UE cases: {ue_filtered}") 
    print(f"Output directory: {output_dir}")
    print("="*60)


def main():
    base_dir = r"C:\Users\bmwlab\Desktop\cursor_gen_conf"
    input_dir = os.path.join(base_dir, "3_defined_input_format", "new_defind_format_ue_1016_175_case")
    output_dir = os.path.join(base_dir, "4_filter_out _the_error_log", "filter_defind_format_ue_1016_175_case")


    success_pattern = "Received PDU Session Establishment Accept"
    reject_pattern = "Received PDU Session Establishment reject"

    print("="*60)
    print("ERROR CASE FILTER TOOL (with REJECT skip)")
    print("="*60)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Filtering out cases containing:")
    print(f"  - {success_pattern}")
    print(f"  - {reject_pattern}")
    print("="*60)

    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return

    filter_cases(input_dir, output_dir, success_pattern, reject_pattern)

    print(f"\nFiltering completed! Check the output directory: {output_dir}")


if __name__ == "__main__":
    main()