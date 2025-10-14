#!/usr/bin/env python3
"""
將 du_conf_1014_800 和 logs_batch_run_1014_800 的內容轉換成 new_defind_format_1001_400_case 的格式
"""

import os
import json
import re
from pathlib import Path

# 路徑設定
DU_CONF_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\du_conf_1014_800"
LOGS_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\sft_data_processing\logs_batch_run_1014_800"
OUTPUT_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\0_input_data(unclean)\new_defind_format_1014_800_case"

def load_cases_delta():
    """載入 cases_delta.json 檔案"""
    cases_delta_file = os.path.join(DU_CONF_DIR, "json", "cases_delta.json")
    if not os.path.exists(cases_delta_file):
        print(f"找不到 cases_delta.json: {cases_delta_file}")
        return []
    
    try:
        with open(cases_delta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"讀取 cases_delta.json 時發生錯誤: {e}")
        return []

def extract_case_info(dirname):
    """從目錄名稱提取 case 資訊"""
    # 格式: 20251014_024446_du_case_001
    pattern = r'(\d{8}_\d{6})_du_case_(\d+)'
    match = re.match(pattern, dirname)
    if match:
        timestamp, case_num = match.groups()
        return case_num, timestamp
    return None, None

def find_log_file(log_dir):
    """在 log_dir 找 tail100_summary.json"""
    log_file = os.path.join(log_dir, "tail100_summary.json")
    if os.path.exists(log_file):
        return log_file
    return None

def process_case(case_num, log_dir, cases_delta_data):
    """處理單一 case"""
    # 從 cases_delta_data 中找到對應的 case 資訊
    case_info = None
    for case_data in cases_delta_data:
        if case_data.get("filename") == f"du_case_{case_num.zfill(3)}.json":
            case_info = case_data
            break
    
    if not case_info:
        print(f"找不到 case {case_num} 的配置資訊")
        return None
    
    # 讀取 log 檔案
    log_file = find_log_file(log_dir)
    if not log_file:
        print(f"找不到 log file for du_case_{case_num}")
        return None

    try:
        # 讀取 log json
        with open(log_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        
        # 建立 misconfigured_param
        modified_key = case_info.get("modified_key", "")
        error_value = case_info.get("error_value", "")
        misconfigured_param = f"{modified_key}={error_value}"
        
        # 建立新的格式
        new_format_data = {
            "misconfigured_param": misconfigured_param,
            "logs": log_data
        }
        
        return new_format_data
        
    except Exception as e:
        print(f"處理 du_case_{case_num} 時發生錯誤: {e}")
        return None

def main():
    # 建立輸出目錄
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "DU"), exist_ok=True)
    
    print(f"開始處理 {DU_CONF_DIR} 和 {LOGS_DIR} 中的資料...")
    
    # 載入 cases_delta.json
    cases_delta_data = load_cases_delta()
    if not cases_delta_data:
        print("無法載入 cases_delta.json，程式結束")
        return
    
    print(f"載入了 {len(cases_delta_data)} 個 case 配置")
    
    du_count = 0
    
    # 遍歷所有 log 目錄
    for dirname in os.listdir(LOGS_DIR):
        if not os.path.isdir(os.path.join(LOGS_DIR, dirname)):
            continue
            
        case_num, timestamp = extract_case_info(dirname)
        if not case_num:
            continue
            
        log_dir = os.path.join(LOGS_DIR, dirname)
        print(f"處理 du_case_{case_num}...")
        
        # 處理 case
        new_format_data = process_case(case_num, log_dir, cases_delta_data)
        if not new_format_data:
            continue
            
        # 儲存到輸出目錄
        output_filename = f"du_case_{case_num.zfill(2)}_new_format.json"
        output_path = os.path.join(OUTPUT_DIR, "DU", output_filename)
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(new_format_data, f, indent=2, ensure_ascii=False)
            
            du_count += 1
            print(f"已處理 du_case_{case_num} -> {output_path}")
            
        except Exception as e:
            print(f"儲存 du_case_{case_num} 時發生錯誤: {e}")
    
    # 建立 summary.json
    summary = {
        "CU": 0,
        "DU": du_count
    }
    
    summary_file = os.path.join(OUTPUT_DIR, "summary.json")
    try:
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"已建立 summary.json: CU=0, DU={du_count}")
    except Exception as e:
        print(f"建立 summary.json 時發生錯誤: {e}")
    
    print(f"\n處理完成!")
    print(f"統計:")
    print(f"   CU cases: 0")
    print(f"   DU cases: {du_count}")
    print(f"   總計: {du_count}")

if __name__ == "__main__":
    main()
