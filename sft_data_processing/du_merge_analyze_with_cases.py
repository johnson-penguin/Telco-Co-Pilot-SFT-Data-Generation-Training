#!/usr/bin/env python3
"""
Merge analyze_log results with du_cases_split data
將 analyze_log 中的分析結果與 du_cases_split 中對應的案例進行合併（LLM 分析置頂）
"""

import json
import os
import re
from pathlib import Path

def load_analyze_log_data(analyze_log_dir):
    """Load all analyze_log data and create a mapping by case number"""
    analyze_data = {}
    
    for file_path in Path(analyze_log_dir).glob("*.json"):
        # Extract case number from filename like "20250930_162207_du_case_12.json"
        match = re.search(r'du_case_(\d+)\.json$', file_path.name)
        if match:
            case_num = int(match.group(1))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                analyze_data[case_num] = data
                print(f"Loaded analyze_log data for DU case {case_num}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return analyze_data

def load_du_cases_data(du_cases_dir):
    """Load all du_cases_split data"""
    du_cases_data = {}
    
    for file_path in Path(du_cases_dir).glob("du_case_*.json"):
        # Extract case number from filename like "du_case_01.json"
        match = re.search(r'du_case_(\d+)\.json$', file_path.name)
        if match:
            case_num = int(match.group(1))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                du_cases_data[case_num] = data
                print(f"Loaded du_cases data for case {case_num}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return du_cases_data

def merge_case_data(du_case_data, analyze_data):
    """Merge a single du_case with its corresponding analyze_log data (LLM analysis on top)"""
    merged_data = {}
    
    # LLM analysis on top
    merged_data["analyze_log"] = analyze_data
    
    # Summary statistics
    if analyze_data:
        error_count = len([item for item in analyze_data if item.get("Error") != "None"])
        success_count = len([item for item in analyze_data if item.get("Error") == "None"])
        
        # Count errors by unit
        unit_errors = {}
        for item in analyze_data:
            unit = item.get("Unit", "Unknown")
            if item.get("Error") != "None":
                unit_errors[unit] = unit_errors.get(unit, 0) + 1
        
        # Count errors by type
        error_types = {}
        for item in analyze_data:
            error_type = item.get("Error", "None")
            if error_type != "None":
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        merged_data["analysis_summary"] = {
            "total_errors": error_count,
            "total_success": success_count,
            "errors_by_unit": unit_errors,
            "errors_by_type": error_types,
            "has_errors": error_count > 0,
            "is_successful": error_count == 0 and success_count > 0
        }
    else:
        merged_data["analysis_summary"] = {
            "total_errors": 0,
            "total_success": 0,
            "errors_by_unit": {},
            "errors_by_type": {},
            "has_errors": False,
            "is_successful": False
        }
    
    # Append original DU case content after LLM analysis
    merged_data.update(du_case_data)
    
    return merged_data

def main():
    """Main function to merge analyze_log with du_cases_split data"""
    # Resolve base directory to the script's folder so paths are robust
    base_dir = Path(__file__).resolve().parent

    du_cases_dir = base_dir / "du_cases_split"
    analyze_log_dir = base_dir / "analyze_log" / "du_0930"
    output_dir = base_dir / "merged_du_cases"
    
    # Ensure output directory exists (including parents)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading du_cases_split data...")
    du_cases_data = load_du_cases_data(du_cases_dir)
    
    print("Loading DU analyze_log data...")
    analyze_data = load_analyze_log_data(analyze_log_dir)
    
    print(f"Found {len(du_cases_data)} DU cases and {len(analyze_data)} analyze_log entries")
    
    merged_count = 0
    missing_analyze_count = 0
    
    for case_num in sorted(du_cases_data.keys()):
        du_case_data = du_cases_data[case_num]
        analyze_log_data = analyze_data.get(case_num, [])
        
        if not analyze_log_data:
            print(f"Warning: No analyze_log data found for DU case {case_num}")
            missing_analyze_count += 1
        
        merged_data = merge_case_data(du_case_data, analyze_log_data)
        
        output_file = output_dir / f"du_case_{case_num:02d}_merged.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
            print(f"Merged DU case {case_num} -> {output_file}")
            merged_count += 1
        except Exception as e:
            print(f"Error saving DU case {case_num}: {e}")
    
    print("\nMerge complete!")
    print(f"Successfully merged: {merged_count} DU cases")
    print(f"Missing analyze_log data: {missing_analyze_count} DU cases")
    print(f"Output directory: {output_dir}")
    
    generate_summary_report(output_dir, merged_count, missing_analyze_count)

def generate_summary_report(output_dir, merged_count, missing_count):
    """Generate a summary report of the DU merge process"""
    report = {
        "merge_summary": {
            "total_cases_processed": merged_count + missing_count,
            "successfully_merged": merged_count,
            "missing_analyze_data": missing_count,
            "merge_timestamp": str(Path().cwd()),
        },
        "case_statistics": {}
    }
    
    for file_path in sorted(output_dir.glob("du_case_*_merged.json")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            case_num = data.get("filename", "").replace("du_case_", "").replace(".json", "")
            if case_num:
                summary = data.get("analysis_summary", {})
                report["case_statistics"][f"case_{case_num}"] = {
                    "has_errors": summary.get("has_errors", False),
                    "is_successful": summary.get("is_successful", False),
                    "total_errors": summary.get("total_errors", 0),
                    "error_types": summary.get("errors_by_type", {}),
                    "error_units": summary.get("errors_by_unit", {})
                }
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    summary_file = output_dir / "merge_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Summary report saved to: {summary_file}")

if __name__ == "__main__":
    main()
