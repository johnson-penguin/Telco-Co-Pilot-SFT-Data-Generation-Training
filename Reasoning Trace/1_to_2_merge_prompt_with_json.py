#!/usr/bin/env python3
"""
Merge a prompt template with JSON case files to produce CU-style reasoning trace Markdown files.

Usage examples:
  python merge_prompt_with_json.py \
    --prompt "C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\Reasoning Trace\\0_prompt\\prompt_ex_1" \
    --json_dir "C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\Reasoning Trace\\1_after_processing(clean)\\filter_defind_format_50_case" \
    --output_dir "C:\\Users\\bmwlab\\Desktop\\cursor_gen_conf\\Reasoning Trace\\2_prompt_with_json\\filter_defind_format_50_case_prompt_1"
"""

import argparse
import json
import os
from typing import Optional, Tuple


def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def split_prompt_at_json_header(prompt_text: str) -> Tuple[str, str]:
    """Split prompt into (header_including_marker, remainder_after_marker)."""
    lines = prompt_text.splitlines()
    json_header_index: Optional[int] = None
    for i, line in enumerate(lines):
        if line.strip() == "JSON File":
            json_header_index = i
            break

    if json_header_index is None:
        header = prompt_text.rstrip("\n") + "\n\nJSON File\n"
        return header, ""

    header_part = "\n".join(lines[: json_header_index + 1]) + "\n"
    remainder_part = "\n".join(lines[json_header_index + 1 :])
    return header_part, remainder_part


def derive_output_filename(input_json_path: str) -> str:
    base = os.path.basename(input_json_path)
    name, _ = os.path.splitext(base)
    if name.endswith("_reasoning_trace"):
        name = name[: -len("_reasoning_trace")]
    return f"{name}_reasoning_trace.md"


def render_output(prompt_text: str, data: dict) -> str:
    header, _ = split_prompt_at_json_header(prompt_text)
    pretty_json = json.dumps(data, ensure_ascii=False, indent=2)
    return f"{header}{pretty_json}\n"


def process_single(prompt_text: str, input_json_path: str, output_dir: str) -> str:
    data = load_json(input_json_path)
    content = render_output(prompt_text, data)
    os.makedirs(output_dir, exist_ok=True)
    out_name = derive_output_filename(input_json_path)
    out_path = os.path.join(output_dir, out_name)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return out_path


def process_directory(prompt_text: str, input_dir: str, output_dir: str) -> None:
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    created = 0
    for entry in sorted(os.listdir(input_dir)):
        if not entry.lower().endswith(".json"):
            continue
        src = os.path.join(input_dir, entry)
        try:
            out_path = process_single(prompt_text, src, output_dir)
            print(f"[OK] {entry} -> {out_path}")
            created += 1
        except Exception as exc:
            print(f"[SKIP] {entry} due to error: {exc}")
    print(f"Created {created} files in {output_dir}")


def process_root_with_subfolders(prompt_text: str, root_input_dir: str, root_output_dir: str) -> None:
    """Process a root directory that may contain CU/DU subfolders.

    For each of the subfolders that exist (CU, DU), render files into
    corresponding subfolders under the output root (create if missing).
    """
    if not os.path.isdir(root_input_dir):
        raise FileNotFoundError(f"Input root directory not found: {root_input_dir}")

    for sub in ("CU", "DU"):
        in_dir = os.path.join(root_input_dir, sub)
        if not os.path.isdir(in_dir):
            continue
        out_dir = os.path.join(root_output_dir, sub)
        os.makedirs(out_dir, exist_ok=True)
        print(f"Processing {sub}: {in_dir} -> {out_dir}")
        process_directory(prompt_text, in_dir, out_dir)


def parse_args() -> argparse.Namespace:
    base_dir = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace"

    default_prompt = os.path.join(base_dir, "0_prompt", "prompt_ex_1")
    default_input_root = os.path.join(base_dir, "1_after_processing(clean)", "filter_defind_format_1009_400_case")
    default_input_dir = default_input_root  # backward compatible default
    default_output = os.path.join(base_dir, "2_prompt_with_json", "filter_defind_format_1009_400_with_prompt_1")

    parser = argparse.ArgumentParser(
        description="Merge a prompt template with JSON case files to produce CU-style reasoning trace Markdown files.",
    )
    parser.add_argument("--prompt", type=str, default=default_prompt, help="Path to prompt template file.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--json", type=str, help="Path to a single input JSON file.")
    group.add_argument("--json_dir", type=str, help="Path to a directory containing input JSON files.")
    parser.add_argument(
        "--json_root_dir",
        type=str,
        default=default_input_root,
        help="Path to a root directory that may contain CU/DU subfolders.",
    )
    parser.add_argument("--output_dir", type=str, default=default_output, help="Directory to write Markdown outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt_text = read_text_file(args.prompt)

    if args.json:
        out_path = process_single(prompt_text, args.json, args.output_dir)
        print(f"Created: {out_path}")
        return

    if args.json_dir:
        process_directory(prompt_text, args.json_dir, args.output_dir)
        return

    if args.json_root_dir:
        process_root_with_subfolders(prompt_text, args.json_root_dir, args.output_dir)
        return


if __name__ == "__main__":
    main()
