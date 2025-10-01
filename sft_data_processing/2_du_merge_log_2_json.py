#!/usr/bin/env python3
"""
將 logs_batch_run_cu_0930 中的 tail100_summary.json
貼到 cu_cases_split 裡對應 case 的 error_log 欄位
（忽略前面的 timestamp，只比對 case_name）
"""

import os
import json

# 路徑設定

CASES_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\sft_data_processing\cu_cases_split"
LOGS_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\sft_data_processing\logs_batch_run_cu_0930"

def find_log_file(case_name: str) -> str:
    """根據 case_name 在 LOGS_DIR 找對應的 tail100_summary.json"""
    for dirname in os.listdir(LOGS_DIR):
        if dirname.endswith(case_name):  # 比對結尾，不管前面的時間戳
            log_file = os.path.join(LOGS_DIR, dirname, "tail100_summary.json")
            if os.path.exists(log_file):
                return log_file
    return None

def main():
    for filename in os.listdir(CASES_DIR):
        if not filename.startswith("du_case_") or not filename.endswith(".json"):
            continue

        case_path = os.path.join(CASES_DIR, filename)
        case_name = filename.replace(".json", "")

        log_file = find_log_file(case_name)
        if not log_file:
            print(f"⚠️ 找不到對應的 log for {case_name}")
            continue

        # 讀取 case json
        with open(case_path, "r", encoding="utf-8") as f:
            case_data = json.load(f)

        # 讀取 log json
        with open(log_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        # 更新 error_log
        case_data["error_log"] = log_data

        # 覆寫原本檔案
        with open(case_path, "w", encoding="utf-8") as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)

        print(f"✅ 已更新 {case_path} (貼上 {log_file} 到 error_log)")


if __name__ == "__main__":
    main()
