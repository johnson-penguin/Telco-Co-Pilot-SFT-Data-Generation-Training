#!/usr/bin/env python3
import os
import re
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _strip_comments(text: str) -> str:
    # Remove # comments at end-of-line
    text = re.sub(r"#[^\n]*", "", text)
    return text


def _first_block(text: str, name: str) -> Optional[str]:
    # Locate the start of the named block and return balanced-brace body of the first object
    m = re.search(rf"{re.escape(name)}\s*=\s*", text)
    if not m:
        return None
    idx = m.end()

    # Move to first '{'
    while idx < len(text) and text[idx] != '{':
        idx += 1
    if idx >= len(text) or text[idx] != '{':
        return None
    # Extract balanced body inside this '{...}'
    start = idx + 1
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '"':
            # skip quoted strings
            i += 1
            while i < len(text):
                if text[i] == '"' and text[i-1] != '\\':
                    i += 1
                    break
                i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        i += 1
    end = i - 1
    if depth != 0 or end <= start:
        return None
    return text[start:end]


def _find_value(block: str, key: str) -> Optional[str]:
    # Match: key = value[;]? — stop at ';' or newline or '}'
    m = re.search(rf"{re.escape(key)}\s*=\s*([^;\n\r}}]+)", block)
    if not m:
        return None
    return m.group(1).strip()


def _to_int_or_str(raw: Optional[str]) -> Optional[Any]:
    if raw is None:
        return None
    s = raw.strip()
    # remove a possible trailing comma or semicolon
    if s.endswith(',') or s.endswith(';'):
        s = s[:-1].strip()
    # Quoted string
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # Integers
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            return s
    # Fallback
    return s.strip('"')


def parse_uicc_block(block: str) -> Dict[str, Any]:
    """Parses the content of a uicc block."""
    return {
        "imsi": _to_int_or_str(_find_value(block, "imsi")),
        "key": _to_int_or_str(_find_value(block, "key")),
        "opc": _to_int_or_str(_find_value(block, "opc")),
        "dnn": _to_int_or_str(_find_value(block, "dnn")),
        "nssai_sst": _to_int_or_str(_find_value(block, "nssai_sst")),
    }


def parse_conf_to_json(conf_text: str) -> Dict[str, Any]:
    """Parses a UE conf file text into a JSON-compatible dictionary."""
    text = _strip_comments(conf_text)
    
    # Assuming only one UICC block for now, as per the example
    uicc0_block = _first_block(text, "uicc0")

    result: Dict[str, Any] = {}

    if uicc0_block:
        result["uicc0"] = parse_uicc_block(uicc0_block)
    
    return result


def convert_file(input_path: str, output_path: str) -> None:
    print(f"Converting: {input_path} -> {output_path}")
    conf_text = read_text(input_path)
    data = parse_conf_to_json(conf_text)
    write_json(output_path, data)
    print(f"Successfully converted {os.path.basename(input_path)}.")


def main() -> None:
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent
    # print("--------------------------------")
    # print(f"BASE_DIR: {BASE_DIR}")
    # print("--------------------------------")

    # DEFAULT_INPUT = PROJECT_ROOT / "1_confgen_workspace" / "1_conf" / "ue_conf_1016_175" / "conf"
    # DEFAULT_OUTPUT = PROJECT_ROOT / "1_confgen_workspace" / "2_json" / "ue_conf_1016_175_json"
    DEFAULT_INPUT = PROJECT_ROOT / "1_confgen_workspace" / "0_workable_conf" / "ue_conf"
    DEFAULT_OUTPUT = PROJECT_ROOT / "1_confgen_workspace" / "0_workable_json_conf" / "ue_json"



    parser = argparse.ArgumentParser(description="Convert UE .conf to JSON matching baseline structure")
    parser.add_argument("--input", help="Input .conf file or directory", required=False, default=DEFAULT_INPUT)
    parser.add_argument("--output", help="Output .json file or directory", required=False, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    
    # Fallback to workspace-relative paths if absolute defaults are not present
    if not os.path.exists(args.input):
        print(f"Warning: Default input path not found: {args.input}")
        rel_input = os.path.join("1_confgen_workspace", "1_conf", "ue_conf_default", "conf")
        if os.path.exists(rel_input):
            print(f"Falling back to relative path: {rel_input}")
            args.input = rel_input
        else:
            print(f"Error: Could not find fallback path either: {rel_input}")
            return

    if os.path.isdir(args.input):
        in_dir = args.input
        out_dir = args.output
        os.makedirs(out_dir, exist_ok=True)
        print(f"Processing directory: {in_dir} -> {out_dir}")
        for name in sorted(os.listdir(in_dir)):
            if not name.endswith(".conf"):
                continue
            in_path = os.path.join(in_dir, name)
            out_name = os.path.splitext(name)[0] + ".json"
            out_path = os.path.join(out_dir, out_name)
            convert_file(in_path, out_path)
        print("\nDirectory processing complete.")
        return

    # Single file
    convert_file(args.input, args.output)
    print("\nFile conversion complete.")


if __name__ == "__main__":
    main()