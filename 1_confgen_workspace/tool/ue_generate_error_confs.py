#!/usr/bin/env python3
"""
根據錯誤描述 JSON 修改 baseline UE conf 並輸出新的錯誤 conf
每個修改的地方會自動加上中英雙語註解
"""

import os
import json
import re
import argparse

SCRIPT_DIR = os.path.dirname(__file__)

# 預設路徑（以 repo 相對路徑為準）
DEFAULT_BASELINE_CONF = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "0_required_inputs", "baseline_conf", "ue_oai.conf"))
DEFAULT_ERROR_CASES_JSON = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "1_conf", "ue_conf_1016_175", "json", "cases_delta.json"))
DEFAULT_OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "1_conf", "ue_conf_1016_175", "conf"))


def _find_block_span(conf_text: str, block_name: str, index: int):
    """Return (start, end) span in conf_text for block `block_name = ( ... );` at given occurrence index.

    Uses balanced-parentheses scanning to avoid premature termination on inner ")".
    Returns None if not found or malformed.
    """
    pattern = rf"{re.escape(block_name)}\s*=\s*\("
    matches = list(re.finditer(pattern, conf_text))
    if index >= len(matches):
        return None
    open_paren_pos = matches[index].end() - 1

    depth = 0
    pos = open_paren_pos
    end_pos = None
    while pos < len(conf_text):
        ch = conf_text[pos]
        if ch == '(':  # open
            depth += 1
        elif ch == ')':  # close
            depth -= 1
            if depth == 0:
                end_pos = pos
                break
        pos += 1

    if end_pos is None:
        return None

    tail_pos = end_pos + 1
    while tail_pos < len(conf_text) and conf_text[tail_pos].isspace():
        tail_pos += 1
    if tail_pos < len(conf_text) and conf_text[tail_pos] == ';':
        tail_pos += 1

    start_of_block = matches[index].start()
    end_of_block = tail_pos
    return (start_of_block, end_of_block)


def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """
    根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解
    支援:
      - 普通 key = value;
      - 陣列元素 key[index]
      - 巢狀結構 key[index].subkey
    """

    # case: block[index].subkey
    if "[" in modified_key and "]" in modified_key and "." in modified_key.split("]")[-1]:
        block_name = modified_key.split("[")[0]
        index = int(modified_key.split("[")[-1].split("]")[0])
        subkey = modified_key.split("].")[-1]

        span = _find_block_span(conf_text, block_name, index)
        if span is None:
            exists_first = _find_block_span(conf_text, block_name, 0) is not None
            if not exists_first:
                print(f"[WARN] 區塊 '{block_name}' 未找到 / Warning: block '{block_name}' not found")
            else:
                print(f"[WARN] 區塊 '{block_name}[{index}]' 超出索引 / Warning: block '{block_name}[{index}]' out of range or malformed")
            return conf_text
        start_idx, end_idx = span
        block_text = conf_text[start_idx:end_idx]

        sub_pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"

        def sub_replacer(m):
            if isinstance(error_value, str) and not str(error_value).startswith("0x"):
                new_val = f'"{error_value}"'
            else:
                new_val = str(error_value)
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{m.group(1)}{new_val}{m.group(3)}{comment}"

        new_block, count = re.subn(sub_pattern, sub_replacer, block_text)
        if count == 0:
            key = subkey.split(".")[-1]
            global_pattern = rf"({re.escape(key)}\s*=\s*)([^;]+)(;)"

            if isinstance(error_value, str) and not str(error_value).startswith("0x"):
                global_new_val = f'"{error_value}"'
            else:
                global_new_val = str(error_value)

            def global_replacer(m):
                return f"{m.group(1)}{global_new_val}{m.group(3)}  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"

            conf_text_after, global_count = re.subn(global_pattern, global_replacer, conf_text)
            if global_count == 0:
                print(f"[WARN] 子參數 '{subkey}' 未在 {block_name}[{index}] 或全域中找到 / Warning: subkey '{subkey}' not found in {block_name}[{index}] or globally")
                return conf_text
            return conf_text_after

        return conf_text[:start_idx] + new_block + conf_text[end_idx:]

    # case: key[index]
    elif "[" in modified_key and "]" in modified_key:
        key = modified_key.split(".")[-1].split("[")[0].strip()
        index = int(modified_key.split("[")[-1].split("]")[0])

        pattern = rf"({key}\s*=\s*\()(.*?)(\);)"

        def replacer(match):
            items = [v.strip() for v in match.group(2).split(",")]
            if 0 <= index < len(items):
                old_val = items[index].strip().strip("\"")
                new_val = f'"{error_value}"' if not str(error_value).startswith("0x") else str(error_value)
                items[index] = new_val
                comment = f"  # 修改: 原始值 {old_val} → 錯誤值 {error_value} / Modified: original {old_val} → error {error_value}"
                return f"{match.group(1)}{', '.join(items)}{match.group(3)}{comment}"
            return match.group(0)

        return re.sub(pattern, replacer, conf_text, flags=re.DOTALL)

    # default: 普通 key = value;
    else:
        key = modified_key.split(".")[-1]
        pattern = rf"({key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f'"{error_value}"'
        else:
            formatted_value = str(error_value)

        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        return re.sub(pattern, replacer, conf_text)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate erroneous UE conf files from baseline using cases JSON")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE_CONF, help="Path to baseline ue_oai.conf")
    parser.add_argument("--cases", default=DEFAULT_ERROR_CASES_JSON, help="Path to error cases JSON (cases_delta.json)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory to write generated .conf files")
    return parser.parse_args()


def main():
    args = parse_args()

    os.makedirs(args.output, exist_ok=True)

    # 載入 baseline UE conf
    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline_text = f.read()

    # 載入錯誤描述 JSON
    with open(args.cases, "r", encoding="utf-8") as f:
        cases = json.load(f)

    for case in cases:
        filename = case["filename"].replace(".json", ".conf")
        modified_key = case["modified_key"]
        error_value = case["error_value"]
        original_value = case.get("original_value", None)

        # 替換 baseline.conf
        new_conf = replace_key_value(baseline_text, modified_key, error_value, original_value)

        # 輸出新檔案
        output_path = os.path.join(args.output, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_conf)

        # ASCII-only console output for Windows
        print(f"[OK] {filename} 已生成 / Generated")
        print(f"   參數修改: {modified_key} → {error_value}")
        print(f"   Parameter modified: {modified_key} → {error_value}")
        print("-" * 60)


if __name__ == "__main__":
    main()


