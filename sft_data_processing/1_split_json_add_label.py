#!/usr/bin/env python3
"""
讀取 JSON，為每個案例新增 error_log 欄位 (預設空字串)
並依據 filename 分離成獨立 JSON 檔案
"""

import os
import json

INPUT_FILE = "cu_output/json/cases_delta.json"            # 輸入 JSON
OUTPUT_DIR = "sft_data_processing/cu_cases_split"    # 輸出資料夾


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 讀入 JSON
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # 遍歷每個案例
    for case in cases:
        # 強制新增 error_log 欄位為空白字串
        case["error_log"] = " "

        # 輸出檔案名稱 (根據 filename)
        output_file = os.path.join(OUTPUT_DIR, case["filename"])
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)

        print(f"✅ 已生成 {output_file} (error_log 預設為空白)")


if __name__ == "__main__":
    main()
