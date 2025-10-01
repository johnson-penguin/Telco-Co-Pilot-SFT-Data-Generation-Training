#!/usr/bin/env python3
"""
Merge analyze_log results with cu_cases_split data
將 analyze_log 中的分析結果與 cu_cases_split 中對應的案例進行合併
"""

import json
import os
import re
from pathlib import Path

def load_analyze_log_data(analyze_log_dir):
    """Load all analyze_log data and create a mapping by case number"""
    analyze_data = {}
    
    for file_path in Path(analyze_log_dir).glob("*.json"):
        # Extract case number from filename like "20250930_154458_cu_case_01.json"
        match = re.search(r'cu_case_(\d+)\.json$', file_path.name)
        if match:
            case_num = int(match.group(1))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                analyze_data[case_num] = data
                print(f"Loaded analyze_log data for case {case_num}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return analyze_data

def load_cu_cases_data(cu_cases_dir):
    """Load all cu_cases_split data"""
    cu_cases_data = {}
    
    for file_path in Path(cu_cases_dir).glob("cu_case_*.json"):
        # Extract case number from filename like "cu_case_01.json"
        match = re.search(r'cu_case_(\d+)\.json$', file_path.name)
        if match:
            case_num = int(match.group(1))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cu_cases_data[case_num] = data
                print(f"Loaded cu_cases data for case {case_num}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return cu_cases_data

def merge_case_data(cu_case_data, analyze_data):
    """Merge a single cu_case with its corresponding analyze_log data"""
    # Create new merged data structure with LLM analysis at the top
    merged_data = {}
    
    # Add analyze_log data at the top
    merged_data["analyze_log"] = analyze_data
    
    # Add summary statistics
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
    
    # Add original cu_case data after LLM analysis
    merged_data.update(cu_case_data)
    
    return merged_data

def main():
    """Main function to merge analyze_log with cu_cases_split data"""
    # Define paths
    cu_cases_dir = Path("cu_cases_split")
    analyze_log_dir = Path("analyze_log/cu_0930")
    output_dir = Path("merged_cu_cases")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("Loading cu_cases_split data...")
    cu_cases_data = load_cu_cases_data(cu_cases_dir)
    
    print("Loading analyze_log data...")
    analyze_data = load_analyze_log_data(analyze_log_dir)
    
    print(f"Found {len(cu_cases_data)} cu_cases and {len(analyze_data)} analyze_log entries")
    
    # Merge data for each case
    merged_count = 0
    missing_analyze_count = 0
    
    for case_num in sorted(cu_cases_data.keys()):
        cu_case_data = cu_cases_data[case_num]
        analyze_log_data = analyze_data.get(case_num, [])
        
        if not analyze_log_data:
            print(f"Warning: No analyze_log data found for case {case_num}")
            missing_analyze_count += 1
        
        # Merge the data
        merged_data = merge_case_data(cu_case_data, analyze_log_data)
        
        # Save merged data
        output_file = output_dir / f"cu_case_{case_num:02d}_merged.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
            print(f"Merged case {case_num} -> {output_file}")
            merged_count += 1
        except Exception as e:
            print(f"Error saving case {case_num}: {e}")
    
    print(f"\nMerge complete!")
    print(f"Successfully merged: {merged_count} cases")
    print(f"Missing analyze_log data: {missing_analyze_count} cases")
    print(f"Output directory: {output_dir}")
    
    # Generate summary report
    generate_summary_report(output_dir, merged_count, missing_analyze_count)

def generate_summary_report(output_dir, merged_count, missing_count):
    """Generate a summary report of the merge process"""
    report = {
        "merge_summary": {
            "total_cases_processed": merged_count + missing_count,
            "successfully_merged": merged_count,
            "missing_analyze_data": missing_count,
            "merge_timestamp": str(Path().cwd()),
        },
        "case_statistics": {}
    }
    
    # Analyze each merged case
    for file_path in sorted(output_dir.glob("cu_case_*_merged.json")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            case_num = data.get("filename", "").replace("cu_case_", "").replace(".json", "")
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
    
    # Save summary report
    summary_file = output_dir / "merge_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Summary report saved to: {summary_file}")

if __name__ == "__main__":
    main()
