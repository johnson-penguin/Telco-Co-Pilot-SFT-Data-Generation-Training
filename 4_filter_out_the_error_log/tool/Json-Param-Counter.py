import os
import json
from collections import Counter

def analyze_param_distribution(root_directory, target_key):
    """
    遞迴掃描指定目錄下的所有 .json 檔案，統計並分析
    特定 key 的所有 value 的分布情況。
    """
    if not os.path.isdir(root_directory):
        print(f"錯誤：找不到目錄 '{root_directory}'")
        return

    # 使用 collections.Counter 來簡化計數過程，功能等同於字典
    distribution_counter = Counter()
    
    print(f"開始遞迴掃描目錄: {root_directory}")
    print(f"分析目標 Key: '{target_key}'\n")

    # os.walk() 會遍歷目錄樹
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith(".json"):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # 檢查 key 是否存在
                        if target_key in data:
                            # 取得 key 對應的值
                            value = data[target_key]
                            # 計數器自動加 1
                            distribution_counter[value] += 1

                except json.JSONDecodeError:
                    print(f"警告：檔案 '{file_path}' 不是有效的 JSON 格式，已跳過。")
                except Exception as e:
                    print(f"讀取檔案 '{file_path}' 時發生錯誤: {e}")

    # --- 掃描完成，開始輸出報告 ---
    print("\n--- 分析報告 ---")
    print(f"針對 Key '{target_key}' 的數值分布情況：\n")

    if not distribution_counter:
        print("在所有 .json 檔案中均未找到指定的 Key。")
        return

    # 按照出現次數從高到低排序，讓結果更清晰
    sorted_distribution = distribution_counter.most_common()

    total_files_found = sum(distribution_counter.values())
    print(f"總共在 {total_files_found} 個檔案中找到目標 Key。\n")
    
    print(f"{'出現次數':<10} | {'參數值 (Value)'}")
    print("-" * 60)
    for value, count in sorted_distribution:
        print(f"{count:<10} | {value}")

# --- 主要執行區塊 ---
if __name__ == "__main__":
    # 您只需要設定這兩個變數
    TARGET_DIRECTORY = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\4_filter_out_the_error_log\filter_defind_format_1014_2_1000_case"
    TARGET_KEY = "misconfigured_param"

    analyze_param_distribution(TARGET_DIRECTORY, TARGET_KEY)