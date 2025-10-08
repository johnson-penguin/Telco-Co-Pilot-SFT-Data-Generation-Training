#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from typing import Optional

try:
    import argparse  # optional; used if CLI flags provided
except Exception:
    argparse = None  # fallback to constants-only mode

try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # only needed for --invoke mode


# === ✨ 1. 手動設定區域 (可用 CLI 覆蓋) ===
PROMPT_FILE = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\2_prompt_with_json\filter_defind_format_50_with_prompt_1\CU\cu_case_02_new_format_reasoning_trace.md"
OUTPUT_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\3_cursor_reasoning\defind_format_50_with_prompt_1_reason"
RESPONSE_FILE = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\cursor_responses\cursor_response.md"

# 呼叫模型的選項（僅在 INVOKE=True 時使用）
INVOKE = False  # True: 直接送出 prompt 給模型並儲存回應；False: 從 RESPONSE_FILE 或 stdin 讀取
MODEL_PROVIDER = "openai"  # 目前支援 openai。未來可擴充成 azure/自架 API
MODEL_NAME = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")  # 可選，自架時使用
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant. Answer in Markdown.")


# === ✨ 2. 工具函式 ===
def derive_category_from_path(prompt_path: str) -> str:
    """從路徑的父資料夾名稱推導出 category (例如 CU 或 DU)"""
    parent = os.path.basename(os.path.dirname(prompt_path))
    return parent if parent else ""


def derive_case_stem(prompt_path: str) -> str:
    """取出檔名（不含副檔名）作為 case 名稱"""
    return os.path.splitext(os.path.basename(prompt_path))[0]


def compute_output_path(output_dir: str, category: str, case_stem: str) -> str:
    """建立輸出資料夾並回傳完整輸出檔路徑"""
    category_dir = os.path.join(output_dir, category) if category else output_dir
    os.makedirs(category_dir, exist_ok=True)

    # 🟢 修改：避免重複 "_reasoning_trace"
    if case_stem.endswith("_reasoning_trace"):
        case_stem = case_stem.removesuffix("_reasoning_trace")

    filename = f"{case_stem}_cursor_reasoning.md"
    return os.path.join(category_dir, filename)


def read_response(response_file: str) -> str:
    """讀取 Cursor 模型的輸出內容"""
    if not os.path.isfile(response_file):
        raise SystemExit(f"Response file not found: {response_file}")
    with open(response_file, "r", encoding="utf-8") as f:
        return f.read()


def write_output(output_path: str, content: str, source_prompt: str) -> None:
    """將內容寫入目標 Markdown 檔案"""
    banner = (
        f"<!-- Saved by save_reasoning_output.py at {datetime.now().isoformat()} -->\n"
        f"<!-- Source prompt: {source_prompt} -->\n\n"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(banner)
        f.write(content)


def read_text(file_path: str) -> str:
    if not os.path.isfile(file_path):
        raise SystemExit(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def invoke_chat_api(prompt_text: str, system_prompt: Optional[str] = None) -> str:
    """呼叫聊天模型取得回應。目前支援 OpenAI Chat Completions 相容 API。"""
    provider = MODEL_PROVIDER.lower().strip() if MODEL_PROVIDER else "openai"
    sys_prompt = system_prompt or SYSTEM_PROMPT

    if provider == "openai":
        if OpenAI is None:
            raise SystemExit("openai package not available. pip install openai>=1.0.0")
        if not OPENAI_API_KEY:
            raise SystemExit("OPENAI_API_KEY not set in environment.")

        client_kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL
        client = OpenAI(**client_kwargs)

        # 使用新的 chat.completions 介面（openai>=1.0.0）
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or ""
        return content

    raise SystemExit(f"Unsupported MODEL_PROVIDER: {MODEL_PROVIDER}")


# === ✨ 3. 主執行流程 ===
def parse_args_if_available():
    if argparse is None:
        return None
    parser = argparse.ArgumentParser(description="Save or generate reasoning output from a prompt.")
    parser.add_argument("--prompt-file", default=PROMPT_FILE)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--response-file", default=RESPONSE_FILE, help="If not invoking, read content from this file or stdin.")
    parser.add_argument("--invoke", action="store_true", default=INVOKE, help="Call chat API with the prompt and save the response.")
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--provider", default=MODEL_PROVIDER)
    parser.add_argument("--system-prompt", default=SYSTEM_PROMPT)
    return parser.parse_args()


def main() -> None:
    args = parse_args_if_available()

    prompt_file = os.path.normpath(args.prompt_file if args else PROMPT_FILE)
    output_dir = os.path.normpath(args.output_dir if args else OUTPUT_DIR)
    response_file = os.path.normpath(args.response_file if args else RESPONSE_FILE)

    if args:
        global INVOKE, MODEL_NAME, MODEL_PROVIDER, SYSTEM_PROMPT
        INVOKE = bool(args.invoke)
        MODEL_NAME = args.model
        MODEL_PROVIDER = args.provider
        SYSTEM_PROMPT = args.system_prompt

    if not os.path.isfile(prompt_file):
        raise SystemExit(f"Prompt file not found: {prompt_file}")

    category = derive_category_from_path(prompt_file)
    case_stem = derive_case_stem(prompt_file)
    output_path = compute_output_path(output_dir, category, case_stem)

    if INVOKE:
        prompt_text = read_text(prompt_file)
        content = invoke_chat_api(prompt_text, SYSTEM_PROMPT)
    else:
        content = read_response(response_file)

    write_output(output_path, content, prompt_file)
    print(f"✅ Saved reasoning to:\n{output_path}")


if __name__ == "__main__":
    main()
