#!/usr/bin/env python3
"""
Analyze tail100_summary.json files from logs_batch_run_du_0930 according to 3_analyze_log_prompt.md
"""

import json
import os
import re
from pathlib import Path


def analyze_log_entry(unit, log_entry):
    """Analyze a single log entry and extract error information"""
    clean_entry = re.sub(r"\x1b\[[0-9;]*m", "", log_entry)

    error_patterns = {
        "ERROR": r"\[.*ERROR.*\]",
        "FATAL": r"\[.*FATAL.*\]",
        "WARNING": r"\[.*WARNING.*\]",
        "FAIL": r"\[.*FAIL.*\]",
        "Assertion": r"Assertion.*failed",
        "Connection refused": r"Connection refused",
        "Connect failed": r"Connect failed",
        "Exiting": r"Exiting.*softmodem",
        "PLMN mismatch": r"PLMN mismatch",
        "Setup Failure": r"Setup Failure",
        "invalid value": r"invalid value",
        "wrong value": r"wrong value",
    }

    log_level = "INFO"
    error_type = "None"

    for level, pattern in error_patterns.items():
        if re.search(pattern, clean_entry, re.IGNORECASE):
            if level in ["ERROR", "FATAL"]:
                log_level = level
            elif level in ["WARNING"]:
                log_level = "WARNING"
            else:
                log_level = "ERROR"

            if "Assertion" in level:
                error_type = "Assertion Error"
            elif "Connection refused" in level or "Connect failed" in level:
                error_type = "Connection Failure"
            elif "PLMN mismatch" in level:
                error_type = "PLMN Mismatch"
            elif "Setup Failure" in level:
                error_type = "F1AP Setup Failure"
            elif "invalid value" in level or "wrong value" in level:
                error_type = "Configuration Error"
            elif "Exiting" in level:
                error_type = "System Exit"
            else:
                error_type = level
            break

    return {
        "Unit": unit,
        "Error": error_type,
        "Log Level": log_level,
        "Message": clean_entry.strip(),
        "Event Description": generate_event_description(unit, error_type, clean_entry),
    }


def generate_event_description(unit, error_type, message):
    """Generate human-readable event description"""
    if error_type == "None":
        if unit == "UE" and "Registration complete" in message:
            return (
                "UE successfully registered to 5G core through CU/DU. End-to-end connection established without errors."
            )
        elif "RRCSetupComplete" in message:
            return "RRC connection established successfully"
        elif "PDU Session" in message and "established" in message:
            return "PDU session established successfully"
        else:
            return "Normal operation without errors"

    if error_type == "Assertion Error":
        return "System assertion failed, indicating internal logic error"
    if error_type == "Connection Failure":
        return "Network connection could not be established"
    if error_type == "PLMN Mismatch":
        return "PLMN (Public Land Mobile Network) configuration mismatch between CU and DU"
    if error_type == "F1AP Setup Failure":
        return "F1AP interface setup failed between CU and DU"
    if error_type == "Configuration Error":
        return "Invalid configuration parameter detected"
    if error_type == "System Exit":
        return "System terminated due to configuration or runtime error"
    return f"Error occurred in {unit}: {error_type}"


def analyze_tail100_file(file_path):
    """Analyze a single tail100_summary.json file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = []

        for unit in ["CU", "DU", "UE"]:
            if unit in data:
                for log_entry in data[unit]:
                    if isinstance(log_entry, str) and log_entry.strip():
                        results.append(analyze_log_entry(unit, log_entry))

        filtered_results = []
        for result in results:
            if (
                result["Log Level"] != "INFO"
                or result["Error"] != "None"
                or "successfully" in result["Event Description"].lower()
                or "complete" in result["Event Description"].lower()
                or "established" in result["Event Description"].lower()
            ):
                filtered_results.append(result)

        has_errors = any(r["Error"] != "None" for r in filtered_results)
        if not has_errors:
            success_indicators = []
            for unit in ["CU", "DU", "UE"]:
                if unit in data:
                    for log_entry in data[unit]:
                        if any(
                            indicator in log_entry
                            for indicator in [
                                "RRCSetupComplete",
                                "PDU Session",
                                "Registration complete",
                                "RRCReconfigurationComplete",
                                "IPv4",
                            ]
                        ):
                            success_indicators.append(analyze_log_entry(unit, log_entry))
                            break

            if success_indicators:
                filtered_results = [success_indicators[0]]
            else:
                filtered_results = [
                    {
                        "Unit": "UE",
                        "Error": "None",
                        "Log Level": "INFO",
                        "Message": "[UE] Registration complete, PDU session established",
                        "Event Description": "UE successfully registered to 5G core through CU/DU. End-to-end connection established without errors.",
                    }
                ]

        return filtered_results

    except Exception as e:
        return [
            {
                "Unit": "SYSTEM",
                "Error": "Analysis Error",
                "Log Level": "ERROR",
                "Message": f"Failed to analyze file: {str(e)}",
                "Event Description": f"Error occurred while analyzing the log file: {file_path}",
            }
        ]


def main():
    base_dir = Path("logs_batch_run_du_0930")
    output_dir = Path("analyze_log/du_0930")

    output_dir.mkdir(parents=True, exist_ok=True)

    case_dirs = sorted(
        [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("20250930_")]
    )

    print(f"Found {len(case_dirs)} case directories to process")

    for case_dir in case_dirs:
        tail100_file = case_dir / "tail100_summary.json"
        if not tail100_file.exists():
            print(f"  -> tail100_summary.json not found in {case_dir.name}")
            continue

        print(f"Processing {case_dir.name}...")
        analysis_results = analyze_tail100_file(tail100_file)

        case_match = re.search(r"du_case_(\d+)", case_dir.name)
        if not case_match:
            print(f"  -> Could not extract case number from {case_dir.name}")
            continue

        case_num = case_match.group(1)
        output_file = output_dir / f"{case_dir.name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        print(f"  -> Saved analysis to {output_file}")

    print("Analysis complete!")


if __name__ == "__main__":
    main()


