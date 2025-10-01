#!/usr/bin/env python3
"""
Update all 200 CU case JSONs to include both explanation_en and explanation_zh fields.
This script reads cases_delta.json, adds English explanations, and updates both
the aggregate file and individual case files.
"""

import json
import os
from typing import Any, Dict, List

JSON_DIR = os.path.join("cu_output", "json")
CASES_DELTA_PATH = os.path.join(JSON_DIR, "cases_delta.json")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_english_explanation(zh_explanation: str, error_type: str, modified_key: str) -> str:
    """Generate English explanation based on Chinese explanation and context."""
    
    # Common patterns for error types
    if error_type == "out_of_range":
        if "超出有效範圍" in zh_explanation or "超出範圍" in zh_explanation:
            return f"Setting {modified_key} to an out-of-range value will cause configuration validation failure during system initialization."
        elif "負值" in zh_explanation or "負" in zh_explanation:
            return f"Setting {modified_key} to a negative value violates protocol constraints and causes configuration rejection."
        else:
            return f"Setting {modified_key} to an invalid value will cause configuration validation failure and system rejection."
    
    elif error_type == "wrong_type":
        return f"Changing {modified_key} from expected type to string will cause parsing errors during configuration loading."
    
    elif error_type == "invalid_enum":
        if "枚舉" in zh_explanation:
            return f"Setting {modified_key} to an invalid enum value will cause configuration validation failure during module initialization."
        else:
            return f"Setting {modified_key} to an unknown enum value will cause negotiation failure and system rejection."
    
    elif error_type == "invalid_format":
        if "IP" in modified_key or "address" in modified_key.lower():
            return f"Setting {modified_key} to invalid IP format will cause network stack rejection and connection failure."
        elif "格式" in zh_explanation:
            return f"Setting {modified_key} to invalid format will cause parsing errors and configuration failure."
        else:
            return f"Setting {modified_key} to malformed value will cause decoding errors and system failure."
    
    elif error_type == "logical_contradiction":
        if "衝突" in zh_explanation or "衝突" in zh_explanation:
            return f"Setting {modified_key} to conflicting value will cause port conflicts and connection establishment failure."
        elif "協議違反" in zh_explanation:
            return f"Setting {modified_key} to invalid value violates protocol requirements and causes connection failure."
        else:
            return f"Setting {modified_key} to contradictory value will cause logical errors and system malfunction."
    
    elif error_type == "missing_value":
        return f"Missing {modified_key} configuration will cause incomplete setup and undefined policy errors."
    
    else:
        return f"Invalid {modified_key} configuration will cause system failure and operational errors."


def main():
    # Load existing cases
    cases = read_json(CASES_DELTA_PATH)
    
    updated_cases = []
    for case in cases:
        # Create updated case with both explanation fields
        updated_case = case.copy()
        
        # Rename existing explanation to explanation_zh
        if "explanation" in updated_case:
            updated_case["explanation_zh"] = updated_case.pop("explanation")
        
        # Generate English explanation
        zh_explanation = updated_case.get("explanation_zh", "")
        error_type = updated_case.get("error_type", "")
        modified_key = updated_case.get("modified_key", "")
        
        updated_case["explanation_en"] = generate_english_explanation(zh_explanation, error_type, modified_key)
        
        updated_cases.append(updated_case)
        
        # Write individual case file
        filename = case["filename"]
        case_path = os.path.join(JSON_DIR, filename)
        write_json(case_path, updated_case)
    
    # Update aggregate file
    write_json(CASES_DELTA_PATH, updated_cases)
    
    print(f"Updated {len(updated_cases)} CU cases with both explanation_en and explanation_zh fields.")
    print("Sample updated case:")
    if updated_cases:
        sample = updated_cases[0]
        print(f"  {sample['filename']}: {sample['modified_key']}")
        print(f"  EN: {sample['explanation_en']}")
        print(f"  ZH: {sample['explanation_zh']}")


if __name__ == "__main__":
    main()
