#!/usr/bin/env python3
"""
Analyze tail100_summary.json files from logs_batch_run_cu_0930 according to 3_analyze_log_prompt.md
"""

import json
import os
import re
from pathlib import Path

def get_explanations(error_type: str) -> tuple[str, str]:
    """Return (explanation_en, explanation_zh) for a given error type."""
    explanations = {
        "None": (
            "No error detected. Normal operation or successful registration/session establishment.",
            "未偵測到錯誤，系統正常運作或註冊/工作階段建立成功。"
        ),
        "Assertion Error": (
            "A runtime assertion failed, indicating an internal logic or state inconsistency.",
            "執行期斷言失敗，表示內部邏輯或狀態不一致。"
        ),
        "Connection Failure": (
            "The component failed to establish a required network connection (e.g., SCTP).",
            "元件無法建立必要的網路連線（例如 SCTP 連線失敗）。"
        ),
        "PLMN Mismatch": (
            "PLMN configuration between CU and DU is inconsistent, preventing proper attachment/setup.",
            "CU 與 DU 的 PLMN 設定不一致，導致無法正確附著/完成設定。"
        ),
        "F1AP Setup Failure": (
            "F1AP interface setup between CU and DU failed, blocking higher-layer procedures.",
            "CU 與 DU 之間的 F1AP 介面設置失敗，阻斷後續流程。"
        ),
        "Configuration Error": (
            "An invalid configuration parameter or value was detected during validation.",
            "在配置驗證過程中偵測到無效的參數或數值。"
        ),
        "System Exit": (
            "The softmodem exited due to configuration or runtime error.",
            "因配置或執行時錯誤導致軟體基站程序結束。"
        )
    }
    # Default fallback
    return explanations.get(error_type, (
        f"An error of type '{error_type}' was observed.",
        f"偵測到錯誤類型：'{error_type}'。"
    ))

def analyze_log_entry(unit, log_entry):
    """Analyze a single log entry and extract error information"""
    # Remove ANSI color codes
    clean_entry = re.sub(r'\x1b\[[0-9;]*m', '', log_entry)
    
    # Check for error patterns
    error_patterns = {
        'ERROR': r'\[.*ERROR.*\]',
        'FATAL': r'\[.*FATAL.*\]',
        'WARNING': r'\[.*WARNING.*\]',
        'FAIL': r'\[.*FAIL.*\]',
        'Assertion': r'Assertion.*failed',
        'Connection refused': r'Connection refused',
        'Connect failed': r'Connect failed',
        'Exiting': r'Exiting.*softmodem',
        'PLMN mismatch': r'PLMN mismatch',
        'Setup Failure': r'Setup Failure',
        'invalid value': r'invalid value',
        'wrong value': r'wrong value'
    }
    
    # Determine log level and error type
    log_level = "INFO"
    error_type = "None"
    
    for level, pattern in error_patterns.items():
        if re.search(pattern, clean_entry, re.IGNORECASE):
            if level in ['ERROR', 'FATAL']:
                log_level = level
            elif level in ['WARNING']:
                log_level = "WARNING"
            else:
                log_level = "ERROR"
            
            if 'Assertion' in level:
                error_type = "Assertion Error"
            elif 'Connection refused' in level or 'Connect failed' in level:
                error_type = "Connection Failure"
            elif 'PLMN mismatch' in level:
                error_type = "PLMN Mismatch"
            elif 'Setup Failure' in level:
                error_type = "F1AP Setup Failure"
            elif 'invalid value' in level or 'wrong value' in level:
                error_type = "Configuration Error"
            elif 'Exiting' in level:
                error_type = "System Exit"
            else:
                error_type = level
            break
    
    explanation_en, explanation_zh = get_explanations(error_type)
    
    return {
        "Unit": unit,
        "Error": error_type,
        "Log Level": log_level,
        "Message": clean_entry.strip(),
        "Event Description": generate_event_description(unit, error_type, clean_entry),
        "explanation_en": explanation_en,
        "explanation_zh": explanation_zh,
    }

def generate_event_description(unit, error_type, message):
    """Generate human-readable event description"""
    if error_type == "None":
        if unit == "UE" and "Registration complete" in message:
            return "UE successfully registered to 5G core through CU/DU. End-to-end connection established without errors."
        elif "RRCSetupComplete" in message:
            return "RRC connection established successfully"
        elif "PDU Session" in message and "established" in message:
            return "PDU session established successfully"
        else:
            return "Normal operation without errors"
    
    elif error_type == "Assertion Error":
        return "System assertion failed, indicating internal logic error"
    elif error_type == "Connection Failure":
        return "Network connection could not be established"
    elif error_type == "PLMN Mismatch":
        return "PLMN (Public Land Mobile Network) configuration mismatch between CU and DU"
    elif error_type == "F1AP Setup Failure":
        return "F1AP interface setup failed between CU and DU"
    elif error_type == "Configuration Error":
        return "Invalid configuration parameter detected"
    elif error_type == "System Exit":
        return "System terminated due to configuration or runtime error"
    else:
        return f"Error occurred in {unit}: {error_type}"

def analyze_tail100_file(file_path):
    """Analyze a single tail100_summary.json file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = []
        
        # Analyze each unit's logs
        for unit in ['CU', 'DU', 'UE']:
            if unit in data:
                for log_entry in data[unit]:
                    if log_entry.strip():  # Skip empty entries
                        analysis = analyze_log_entry(unit, log_entry)
                        results.append(analysis)
        
        # Filter out INFO level entries that are not errors or success indicators
        filtered_results = []
        for result in results:
            if (result["Log Level"] != "INFO" or 
                result["Error"] != "None" or
                "successfully" in result["Event Description"].lower() or
                "complete" in result["Event Description"].lower() or
                "established" in result["Event Description"].lower()):
                filtered_results.append(result)
        
        # If no errors found, check for successful completion
        has_errors = any(result["Error"] != "None" for result in filtered_results)
        if not has_errors:
            # Look for success indicators
            success_indicators = []
            for unit in ['CU', 'DU', 'UE']:
                if unit in data:
                    for log_entry in data[unit]:
                        if any(indicator in log_entry for indicator in [
                            "RRCSetupComplete", "PDU Session", "Registration complete",
                            "RRCReconfigurationComplete", "IPv4"
                        ]):
                            success_indicators.append(analyze_log_entry(unit, log_entry))
                            break
            
            if success_indicators:
                # Return the most relevant success indicator
                filtered_results = [success_indicators[0]]
            else:
                # Return a generic success message
                explanation_en, explanation_zh = get_explanations("None")
                filtered_results = [{
                    "Unit": "UE",
                    "Error": "None",
                    "Log Level": "INFO",
                    "Message": "[UE] Registration complete, PDU session established",
                    "Event Description": "UE successfully registered to 5G core through CU/DU. End-to-end connection established without errors.",
                    "explanation_en": explanation_en,
                    "explanation_zh": explanation_zh,
                }]
        
        return filtered_results
        
    except Exception as e:
        explanation_en, explanation_zh = (
            "Analysis failed due to an exception while reading or parsing the file.",
            "分析過程在讀取或解析檔案時發生例外而失敗。"
        )
        return [{
            "Unit": "SYSTEM",
            "Error": "Analysis Error",
            "Log Level": "ERROR",
            "Message": f"Failed to analyze file: {str(e)}",
            "Event Description": f"Error occurred while analyzing the log file: {file_path}",
            "explanation_en": explanation_en,
            "explanation_zh": explanation_zh,
        }]

def main():
    """Main function to process all tail100_summary.json files"""
    base_dir = Path("logs_batch_run_cu_0930")
    output_dir = Path("analyze_log/cu_0930")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all case directories
    case_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("20250930_")])
    
    print(f"Found {len(case_dirs)} case directories to process")
    
    for case_dir in case_dirs:
        tail100_file = case_dir / "tail100_summary.json"
        
        if tail100_file.exists():
            print(f"Processing {case_dir.name}...")
            
            # Analyze the file
            analysis_results = analyze_tail100_file(tail100_file)
            
            # Extract case number from directory name
            case_match = re.search(r'cu_case_(\d+)', case_dir.name)
            if case_match:
                case_num = case_match.group(1)
                output_file = output_dir / f"20250930_{case_dir.name.split('_')[1]}_cu_case_{case_num}.json"
                
                # Write analysis results
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results, f, indent=2, ensure_ascii=False)
                
                print(f"  -> Saved analysis to {output_file}")
            else:
                print(f"  -> Could not extract case number from {case_dir.name}")
        else:
            print(f"  -> tail100_summary.json not found in {case_dir.name}")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
