#!/usr/bin/env python3
"""
將 logs_batch_run_1009_400 中的資料處理成 new_defind_format_1009_400_case 的格式
參考 2_cu_merge_log_2_json.py 和 2_du_merge_log_2_json.py 的處理方式
"""

import os
import json
import re
from pathlib import Path

# 路徑設定
LOGS_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\sft_data_processing\logs_batch_run_1009_400"
OUTPUT_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\0_input_data(unclean)\new_defind_format_1009_400_case"

def extract_case_info(dirname):
    """從目錄名稱提取 case 資訊"""
    # 格式: 20251009_165141_cu_case_01 或 20251009_190536_du_case_01
    pattern = r'(\d{8}_\d{6})_(cu|du)_case_(\d+)'
    match = re.match(pattern, dirname)
    if match:
        timestamp, case_type, case_num = match.groups()
        return case_type, case_num, timestamp
    return None, None, None

def find_log_file(log_dir, case_type):
    """根據 case_type 在 log_dir 找對應的 tail100_summary.json"""
    log_file = os.path.join(log_dir, "tail100_summary.json")
    if os.path.exists(log_file):
        return log_file
    return None

def process_case(log_dir, case_type, case_num, timestamp):
    """處理單一 case"""
    log_file = find_log_file(log_dir, case_type)
    if not log_file:
        print(f"找不到 log file for {case_type}_case_{case_num}")
        return None

    try:
        # 讀取 log json
        with open(log_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        
        # 從 log_data 中提取 misconfigured_param
        # 假設錯誤參數在 CU 或 DU 的 log 中，需要根據實際情況調整
        misconfigured_param = None
        if case_type == "cu":
            # 從 CU logs 中尋找錯誤參數
            for log_line in log_data.get("CU", []):
                if "gNBs.gNB_ID" in log_line or "error" in log_line.lower():
                    # 提取錯誤參數，這裡需要根據實際 log 格式調整
                    if "gNBs.gNB_ID" in log_line:
                        misconfigured_param = "gNBs.gNB_ID=0xFFFFFFFF"  # 預設值，需要根據實際情況調整
                        break
        elif case_type == "du":
            # 從 DU logs 中尋找錯誤參數
            for log_line in log_data.get("DU", []):
                if "gNBs.gNB_ID" in log_line or "error" in log_line.lower():
                    if "gNBs.gNB_ID" in log_line:
                        misconfigured_param = "gNBs.gNB_ID=0xFFFFFFFF"  # 預設值，需要根據實際情況調整
                        break
        
        # 如果找不到錯誤參數，使用預設值
        if not misconfigured_param:
            misconfigured_param = f"gNBs.gNB_ID=0xFFFFFFFF"
        
        # 建立新的格式
        new_format_data = {
            "misconfigured_param": misconfigured_param,
            "logs": log_data
        }
        
        return new_format_data
        
    except Exception as e:
        print(f"處理 {case_type}_case_{case_num} 時發生錯誤: {e}")
        return None

def main():
    # 建立輸出目錄
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "CU"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "DU"), exist_ok=True)
    
    print(f"開始處理 {LOGS_DIR} 中的資料...")
    
    cu_count = 0
    du_count = 0
    
    # 遍歷所有目錄
    for dirname in os.listdir(LOGS_DIR):
        if not os.path.isdir(os.path.join(LOGS_DIR, dirname)):
            continue
            
        case_type, case_num, timestamp = extract_case_info(dirname)
        if not case_type or not case_num:
            continue
            
        log_dir = os.path.join(LOGS_DIR, dirname)
        print(f"處理 {case_type}_case_{case_num}...")
        
        # 處理 case
        new_format_data = process_case(log_dir, case_type, case_num, timestamp)
        if not new_format_data:
            continue
            
        # 儲存到對應的目錄
        output_filename = f"{case_type}_case_{case_num}_new_format.json"
        output_path = os.path.join(OUTPUT_DIR, case_type.upper(), output_filename)
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(new_format_data, f, indent=2, ensure_ascii=False)
            
            if case_type == "cu":
                cu_count += 1
            else:
                du_count += 1
                
            print(f"已處理 {case_type}_case_{case_num} -> {output_path}")
            
        except Exception as e:
            print(f"儲存 {case_type}_case_{case_num} 時發生錯誤: {e}")
    
    print(f"\n處理完成!")
    print(f"統計:")
    print(f"   CU cases: {cu_count}")
    print(f"   DU cases: {du_count}")
    print(f"   總計: {cu_count + du_count}")

if __name__ == "__main__":
    main()
