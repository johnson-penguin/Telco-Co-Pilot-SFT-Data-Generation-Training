import json
import os
from pathlib import Path
# *******************************************************************
# 1. 設定變數 (請確認此路徑正確)
# *******************************************************************
# 您指定的根目錄路徑
BASE_DIR = Path(__file__).resolve()
PROJECT_ROOT = BASE_DIR.parent.parent.parent

# --- 🎯 步驟 1: 定義所有要合併的「資料夾名稱」清單 ---
# 請將所有想要合併的資料夾名稱放入這個列表中
SOURCE_FOLDERS = [
    "filter_defind_format_1002_600_case",
    "filter_defind_format_1014_800_case", 
    "filter_defind_format_1014_2000_case",
    "filter_defind_format_cu_1009_200_case",
    "filter_defind_format_cu_1016_150_case",
    "filter_defind_format_du_1009_200_case",
    "filter_defind_format_ue_1016_175_case"
]

# --- 🎯 步驟 2: 設定輸出路徑 (統一輸出到一個檔案) ---
OUTPUT_DIR = PROJECT_ROOT / "4_filter_out_the_error_log" / "merge_cae"
# 統一輸出檔案名稱 (避免檔名過長，並指出是多資料夾合併)
OUTPUT_FILE = OUTPUT_DIR / 'merged_from_multiple_sources.jsonl'

# 確保輸出目錄存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# *******************************************************************

all_data = []
total_files_processed = 0
failed_files = []

# --- 🎯 步驟 3: 遍歷所有指定的來源資料夾 ---
for folder_name in SOURCE_FOLDERS:
    
    # 計算當前資料夾的 ROOT_DIR
    ROOT_DIR = PROJECT_ROOT / "4_filter_out_the_error_log" / folder_name
    
    print(f"🔄 開始處理目錄: {ROOT_DIR}")

    if not ROOT_DIR.is_dir():
        print(f"⚠️ 警告: 來源目錄不存在，跳過: {ROOT_DIR}")
        continue

    # os.walk 會遞迴地遍歷 ROOT_DIR 下的所有目錄和檔案
    for dirpath, dirnames, filenames in os.walk(str(ROOT_DIR)):
        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(dirpath, filename)

                # 確保不會讀取到輸出檔案本身
                if file_path == str(OUTPUT_FILE):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        # 判斷 JSON 內容：
                        # 如果是列表 (常見於資料集)，則使用 extend() 將其內容攤平到 all_data
                        if isinstance(data, list):
                            all_data.extend(data)
                        # 如果是單一物件 (常見於單個設定檔)，則將其作為一個元素添加到 all_data
                        else:
                            all_data.append(data)

                        total_files_processed += 1

                except json.JSONDecodeError:
                    # 記錄失敗檔案的完整路徑
                    failed_files.append(f"檔案 {file_path} 無效 JSON 格式。")
                except Exception as e:
                    failed_files.append(f"檔案 {file_path} 讀取時發生錯誤: {e}")

# *******************************************************************
# 2. 寫入合併後的資料
# *******************************************************************
if all_data:
    try:
        # 使用標準 JSON Lines 寫法：逐行寫入，每行一個 JSON 物件
        with open(str(OUTPUT_FILE), 'w', encoding='utf-8') as outfile:
            for record in all_data:
                # 1. 將單個 Python 字典轉換成 JSON 字串
                # 2. 確保中文字元正確顯示 (ensure_ascii=False)
                # 3. 不使用 indent=4 (JSONL 檔案通常不格式化)
                # 4. 在末尾添加換行符 '\n'
                json_line = json.dumps(record, ensure_ascii=False)
                outfile.write(json_line + '\n')

        print("-" * 50)
        print(f"✅ 成功! 合併結果已儲存至：")
        print(f"   {OUTPUT_FILE}")
        print(f"📂 總共處理了 {total_files_processed} 個 JSON 檔案。")
        print(f"📜 總共合併了 {len(all_data)} 筆記錄 (JSON 列表的元素數量)。")
        if failed_files:
            print(f"⚠️ 警告: 有 {len(failed_files)} 個檔案處理失敗或格式無效。")
            # 如果需要查看失敗列表，可以取消註釋下面一行：
            # print("\n失敗檔案列表:\n" + "\n".join(failed_files))
        print("-" * 50)
    except Exception as e:
        print(f"寫入檔案時發生致命錯誤: {e}")
else:
    # 顯示所有嘗試過的根目錄
    searched_paths = "\n".join([str(PROJECT_ROOT / "4_filter_out_the_error_log" / f) for f in SOURCE_FOLDERS])
    print(f"❌ 警告: 在指定的路徑及其子目錄中沒有找到有效的 JSON 檔案。")
    print(f"嘗試搜索的根目錄:\n{searched_paths}")