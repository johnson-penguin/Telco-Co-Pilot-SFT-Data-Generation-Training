#!/usr/bin/env python3
"""
根據錯誤描述 JSON 修改 baseline.conf 並輸出新的錯誤 conf
每個修改的地方會自動加上中英雙語註解
"""

import os
import json
import re

SCRIPT_DIR = os.path.dirname(__file__)

# 基準檔與輸入/輸出目錄（指向 du_conf_1009_200）
BASELINE_CONF = os.path.join(SCRIPT_DIR, "..", "0_required_inputs", "baseline_conf", "du_gnb.conf")
ERROR_CASES_JSON = os.path.join(SCRIPT_DIR, "du_conf_1014_800", "json", "cases_delta.json")   # 存放錯誤描述 JSON
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "du_conf_1014_800", "conf")


def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """
    根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解
    支援:
      - 普通 key = value;
      - 陣列元素 key[index]
      - 巢狀結構 key[index].subkey
      - 特殊處理: gNBs[0].servingCellConfigCommon[0].subkey -> servingCellConfigCommon.subkey
      - 特殊處理: fhi_72.fh_config[0].subkey -> fhi_72.fh_config.subkey
    """

    # 特殊處理: gNBs[0].servingCellConfigCommon[0].absoluteFrequencySSB -> servingCellConfigCommon.absoluteFrequencySSB
    if "gNBs[0].servingCellConfigCommon[0]." in modified_key:
        subkey = modified_key.split("gNBs[0].servingCellConfigCommon[0].")[-1]
        pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"
        
        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)
        
        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"
        
        new_text, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            print(f"[WARN] 子參數 '{subkey}' 未在 gNBs[0] 中找到 / Warning: subkey '{subkey}' not found in gNBs[0]")
            return conf_text
        return new_text

    # 特殊處理: fhi_72.fh_config[0].subkey -> fhi_72.fh_config.subkey
    if "fhi_72.fh_config[0]." in modified_key:
        subkey = modified_key.split("fhi_72.fh_config[0].")[-1]
        pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"
        
        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)
        
        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"
        
        new_text, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            print(f"[WARN] 區塊 'fhi_72.fh_config' 未找到 / Warning: block 'fhi_72.fh_config' not found")
            return conf_text
        return new_text

    # case: plmn_list[0].mnc_length
    if "[" in modified_key and "]" in modified_key and "." in modified_key.split("]")[-1]:
        block_name = modified_key.split("[")[0]
        index = int(modified_key.split("[")[-1].split("]")[0])
        subkey = modified_key.split("].")[-1]

        # 找 plmn_list block
        pattern = rf"({block_name}\s*=\s*\(\s*{{.*?}}\s*\);)"
        matches = list(re.finditer(pattern, conf_text, flags=re.DOTALL))
        if not matches:
            print(f"[WARN] 區塊 '{block_name}' 未找到 / Warning: block '{block_name}' not found")
            return conf_text

        # 取 index-th block
        match = matches[index]
        block_text = match.group(1)

        # 替換 block 內部 subkey
        sub_pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"
        def sub_replacer(m):
            old_val = m.group(2).strip()
            if isinstance(error_value, str) and not error_value.startswith("0x"):
                new_val = f"\"{error_value}\""
            else:
                new_val = str(error_value)
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{m.group(1)}{new_val}{m.group(3)}{comment}"

        new_block, count = re.subn(sub_pattern, sub_replacer, block_text)
        if count == 0:
            print(f"[WARN] 子參數 '{subkey}' 未在 {block_name}[{index}] 中找到 / Warning: subkey '{subkey}' not found in {block_name}[{index}]")
            return conf_text

        # 替換回去
        return conf_text[:match.start()] + new_block + conf_text[match.end():]

    # case: key[index]
    elif "[" in modified_key and "]" in modified_key:
        key = modified_key.split(".")[-1].split("[")[0].strip()
        index = int(modified_key.split("[")[-1].split("]")[0])

        pattern = rf"({key}\s*=\s*\()(.*?)(\);)"
        def replacer(match):
            items = [v.strip() for v in match.group(2).split(",")]
            if 0 <= index < len(items):
                old_val = items[index].strip().strip("\"")
                new_val = f"\"{error_value}\"" if not str(error_value).startswith("0x") else str(error_value)
                items[index] = new_val
                comment = f"  # 修改: 原始值 {old_val} → 錯誤值 {error_value} / Modified: original {old_val} → error {error_value}"
                return f"{match.group(1)}{', '.join(items)}{match.group(3)}{comment}"
            return match.group(0)
        return re.sub(pattern, replacer, conf_text, flags=re.DOTALL)

    else:
        # 普通 key = value;
        key = modified_key.split(".")[-1]
        pattern = rf"({key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)

        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        return re.sub(pattern, replacer, conf_text)


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

        # ASCII-only console output for Windows
        print(f"[OK] {filename} 已生成 / Generated")
        print(f"   參數修改: {modified_key} → {error_value}")
        print(f"   Parameter modified: {modified_key} → {error_value}")
        print("-" * 60)


if __name__ == "__main__":
    main()
