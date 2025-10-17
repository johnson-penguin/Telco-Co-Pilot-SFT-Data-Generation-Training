import os
import json
from collections import Counter

def analyze_and_save_report(root_directory, target_key, output_filepath):
    """
    遞迴掃描指定目錄下的所有 .json 檔案，統計特定 key 的 value 分布，
    並將分析報告儲存到指定的檔案路徑。
    (Recursively scans .json files in a directory, analyzes the value distribution
     of a target key, and saves the report to a specified file path.)
    """
    if not os.path.isdir(root_directory):
        print(f"錯誤：找不到目錄 '{root_directory}'，已跳過。")
        print(f"(Error: Directory not found '{root_directory}', skipping.)")
        return

    distribution_counter = Counter()
    
    print(f"開始掃描目錄: {root_directory}")
    print(f"(Scanning directory: {root_directory})")

    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith(".json"):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if target_key in data:
                            value = data[target_key]
                            distribution_counter[value] += 1
                except json.JSONDecodeError:
                    print(f"警告：檔案 '{file_path}' 不是有效的 JSON 格式，已跳過。")
                    print(f"(Warning: File '{file_path}' is not a valid JSON format, skipping.)")
                except Exception as e:
                    print(f"讀取檔案 '{file_path}' 時發生錯誤: {e}")
                    print(f"(An error occurred while reading file '{file_path}': {e})")

    # --- 掃描完成，準備報告內容 ---
    report_lines = []
    
    report_lines.append("--- 分析報告 (Analysis Report) ---")
    report_lines.append(f"分析目錄 (Analyzed Directory): {root_directory}")
    report_lines.append(f"分析目標 Key (Target Key): '{target_key}'\n")

    if not distribution_counter:
        report_lines.append("在所有 .json 檔案中均未找到指定的 Key。 (The specified Key was not found in any .json files.)")
    else:
        sorted_distribution = distribution_counter.most_common()
        total_files_found = sum(distribution_counter.values())
        
        report_lines.append(f"總共在 {total_files_found} 個檔案中找到目標 Key。\n (Found the target Key in a total of {total_files_found} files.)\n")
        report_lines.append(f"{'出現次數 (Count)':<20} | {'參數值 (Value)'}")
        report_lines.append("-" * 80)
        
        for value, count in sorted_distribution:
            report_lines.append(f"{count:<20} | {value}")

    # --- 將報告內容寫入檔案 ---
    try:
        report_content = "\n".join(report_lines)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"報告已成功儲存至: {output_filepath}")
        print(f"(Report successfully saved to: {output_filepath})\n")
    except Exception as e:
        print(f"儲存報告 '{output_filepath}' 時發生錯誤: {e}")
        print(f"(Error saving report to '{output_filepath}': {e})\n")


# --- 主要執行區塊 (Main execution block) ---
if __name__ == "__main__":
    # --- 您只需要設定這裡的變數 ---

    # 1. 設定包含所有要分析資料夾的「上層目錄」
    PARENT_DIRECTORY = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\4_filter_out_the_error_log"

    # 2. 以列表形式，填入所有要分析的「資料夾名稱」
    FOLDERS_TO_ANALYZE = [
        "filter_defind_format_50_case",
        "filter_defind_format_1001_400_case",
        "filter_defind_format_1002_600_case",
        "filter_defind_format_1014_800_case",
        "filter_defind_format_1014_2000_case",
        "filter_defind_format_cu_1009_200_case",
        "filter_defind_format_cu_1016_150_case",
        "filter_defind_format_du_1009_200_case",
        "filter_defind_format_ue_1016_175_case"
    ]

    # 3. 設定要分析的 Key
    TARGET_KEY = "misconfigured_param"

    # 4. 設定儲存報告的資料夾路徑。
    OUTPUT_REPORTS_DIR = os.path.join(PARENT_DIRECTORY, "param_check_reports")

    # --- 執行迴圈，處理所有指定的資料夾 ---
    
    # 建立儲存報告的資料夾 (如果不存在)
    if not os.path.exists(OUTPUT_REPORTS_DIR):
        print(f"建立報告儲存目錄: {OUTPUT_REPORTS_DIR}")
        print(f"(Creating report directory: {OUTPUT_REPORTS_DIR})")
        os.makedirs(OUTPUT_REPORTS_DIR)

    print("\n--- 開始執行多目錄分析 ---")
    print("--- (Starting multi-directory analysis) ---\n")

    for folder_name in FOLDERS_TO_ANALYZE:
        current_directory = os.path.join(PARENT_DIRECTORY, folder_name)
        output_file = os.path.join(OUTPUT_REPORTS_DIR, f"{folder_name}_report.txt")
        analyze_and_save_report(current_directory, TARGET_KEY, output_file)

    print("--- 所有分析任務已完成 ---")
    print("--- (All analysis tasks completed) ---")