#!/usr/bin/env python3
"""
根據錯誤描述 JSON 修改 baseline.conf 並輸出新的錯誤 conf
每個修改的地方會自動加上中英雙語註解
"""

import os
import json
import re

BASELINE_CONF = r"baseline_conf\cu_gnb.conf"
ERROR_CASES_JSON = "cu_output/json/cases_delta.json"   # 存放錯誤描述 JSON
OUTPUT_DIR = "cu_output/error_conf"


def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """
    根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解
    支援 array index，例如 security.integrity_algorithms[0]
    """

    if "[" in modified_key and "]" in modified_key:
        # e.g. integrity_algorithms[0]
        key = modified_key.split(".")[-1].split("[")[0].strip()
        index = int(modified_key.split("[")[-1].split("]")[0])

        pattern = rf"({key}\s*=\s*\()(.*?)(\);)"
        def replacer(match):
            values_str = match.group(2)
            items = [v.strip() for v in values_str.split(",")]
            if 0 <= index < len(items):
                old_val = items[index].strip().strip("\"")
                new_val = f"\"{error_value}\"" if not str(error_value).startswith("0x") else str(error_value)
                items[index] = new_val
                if original_value is not None:
                    comment = f"  # 修改: 原始值 {old_val} → 錯誤值 {error_value} / Modified: original {old_val} → error {error_value}"
                else:
                    comment = f"  # 修改為 {error_value} / Modified to {error_value}"
                return f"{match.group(1)}{', '.join(items)}{match.group(3)}{comment}"
            return match.group(0)
        new_conf, count = re.subn(pattern, replacer, conf_text, flags=re.DOTALL)
        if count == 0:
            print(f"[WARN] 陣列參數 '{key}[{index}]' 未在 baseline.conf 中找到 / Warning: array key '{key}[{index}]' not found in baseline.conf")
        return new_conf

    else:
        # 普通的 key = value;
        key = modified_key.split(".")[-1]
        pattern = rf"({key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)

        def replacer(match):
            if original_value is not None:
                comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            else:
                comment = f"  # 修改為 {error_value} / Modified to {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        new_conf, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            print(f"[WARN] 參數 '{key}' 未在 baseline.conf 中找到 / Warning: key '{key}' not found in baseline.conf")
        return new_conf


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 載入 baseline.conf
    with open(BASELINE_CONF, "r", encoding="utf-8") as f:
        baseline_text = f.read()

    # 載入錯誤描述 JSON
    with open(ERROR_CASES_JSON, "r", encoding="utf-8") as f:
        cases = json.load(f)

    for case in cases:
        filename = case["filename"].replace(".json", ".conf")
        modified_key = case["modified_key"]
        error_value = case["error_value"]
        original_value = case.get("original_value", None)

        # 替換 baseline.conf
        new_conf = replace_key_value(baseline_text, modified_key, error_value, original_value)

        # 輸出新檔案
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_conf)

        # Bilingual console output (ASCII only)
        print(f"[OK] {filename} 已生成 / Generated")
        print(f"   參數修改: {modified_key} → {error_value}")
        print(f"   Parameter modified: {modified_key} → {error_value}")
        print("-" * 60)


if __name__ == "__main__":
    main()
