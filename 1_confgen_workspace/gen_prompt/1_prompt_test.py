import os
import google.generativeai as genai
import json # 用於解析和儲存 JSON
import re   # 用於在 LLM 輸出中尋找 JSON
from datetime import datetime # (★ 新增) 用於產生時間戳

# --- ⚠️ 請修改以下變數 ---

# 1. 您提到的「數量n」
N_VARIATIONS = 5 

# 2. (★ 已更新) 最終輸出的「目錄」
OUTPUT_DIRECTORY = "/home/ksmo/johnson/Trace-Reasoning-rApp/0_temp"

# --- 變數修改結束 ---


# 輔助函數：讀取檔案內容
def read_file_content(file_path):
    """安全地讀取檔案內容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到檔案 {file_path}")
        print("請檢查您的檔案路徑是否正確。")
        return None
    except Exception as e:
        print(f"❌ 讀取檔案 {file_path} 時發生錯誤: {e}")
        return None

# --- 驗證函數 (與 6_simplified_schema.py 相同) ---
def validate_llm_output(output_text, n):
    """
    驗證 LLM 輸出的結構是否符合預期。
    (檢查 4 個關鍵欄位)
    """
    try:
        json_match = re.search(r'\[.*\]', output_text, re.DOTALL)
        if not json_match:
            if output_text.startswith('[') and output_text.endswith(']'):
                json_text = output_text
            else:
                 return False, "Validation ❌ FAIL: 在 LLM 輸出中找不到 JSON 陣列 (即 '[]' 區塊)。", None
        else:
            json_text = json_match.group(0)
            
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return False, f"Validation ❌ FAIL: LLM 輸出不是有效的 JSON。錯誤: {e}", None
    except Exception as e:
        return False, f"Validation ❌ FAIL: 解析 JSON 時發生未知錯誤。{e}", None

    if not isinstance(data, list):
        return False, f"Validation ❌ FAIL: 預期輸出為 JSON 列表 (array)，但實際得到 {type(data)}。", None

    if len(data) != n:
        return False, f"Validation ❌ FAIL: 預期列表應有 {n} 個項目，但實際得到 {len(data)} 個。", None

    required_keys = {
        "filename", 
        "modified_key", 
        "original_value", 
        "error_value"
    }
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"Validation ❌ FAIL: 列表中的第 {i} 個項目不是一個有效的 JSON 物件 (dictionary)。", None
        
        missing_keys = required_keys - item.keys()
        if missing_keys:
            return False, f"Validation ❌ FAIL: 列表中的第 {i} 個項目缺少必要的欄位: {missing_keys}", None

    return True, f"Validation ✅ PASS: 輸出格式正確 (有效的 JSON 列表，包含 {n} 個項目，且所有 4 個欄位均存在)。", data


def run_specific_llm_test():
    """
    執行一個自動化的 LLM 測試。
    使用組合後的「模糊測試專家」提示 (4 欄位版本)。
    """
    
    # 檔案路徑
    conf_file_path = "/home/ksmo/johnson/Config-Variator-rApp/log_preprocessing_pipeline_tool/0_required_inputs/baseline_conf/du_gnb.conf"
    json_file_path = "/home/ksmo/johnson/Config-Variator-rApp/log_preprocessing_pipeline_tool/0_required_inputs/baseline_conf_json/du_gnb.json"
    
    # 1. 檢查 API Key
    api_key = os.getenv("Johnson_GOOGLE_API_KEY")
    if not api_key:
        print("❌ 錯誤: 找不到 Johnson_GOOGLE_API_KEY 環境變數。")
        return

    print("✅ Johnson_GOOGLE_API_KEY 已找到。")

    # 2. 讀取檔案內容
    print(f"正在讀取 {conf_file_path}...")
    conf_content = read_file_content(conf_file_path)
    if conf_content is None: return

    print(f"正在讀取 {json_file_path}...")
    json_content = read_file_content(json_file_path)
    if json_content is None: return
        
    print("✅ 檔案讀取完畢。")

    # 3. 建立 System Instruction 和 測試 Prompt (與 6_simplified_schema.py 相同)
    system_role = (
        "You are a 5G gNodeB configuration fuzz-test expert. "
        "You follow instructions precisely. "
        "Your response MUST be ONLY the JSON array (starting with '[' and ending with ']'), with no other text."
    )

    test_prompt = f"""
    Here is the task: You are a 5G gNodeB configuration fuzz-test expert.
    Given the following valid JSON configuration (Reference JSON) and the original .conf (Baseline Conf), 
    generate exactly {N_VARIATIONS} single-key error test cases and output them as a JSON array.

    ## Rules
    1.  Modify exactly one key per case (single-key error).
    2.  Produce {N_VARIATIONS} distinct cases.
    3.  Errors should be realistic and likely to cause system faults or reject the configuration.
    4.  Your output MUST be a JSON array, where each object contains the 4 keys defined in the "Output Schema".
    5.  Your entire response MUST be only the JSON array. Do not include any other text.

    ## Input: Baseline .conf file content
    ---[START DU_GNB.CONF]---
    {conf_content}
    ---[END DU_GNB.CONF]---

    ## Input: Reference .json file content
    ---[START DU_GNB.JSON]---
    {json_content}
    ---[END DU_GNB.JSON]---

    ## Output Schema (Produce a JSON array of objects like this)
    [
      {{
        "filename": "du_case_001.json",
        "modified_key": "path.to.the.key",
        "original_value": "original_value_from_json",
        "error_value": "new_generated_error_value"
      }},
      ...
    ]

    Generate the {N_VARIATIONS} error-case variations now as a JSON array.
    """

    print("=============================================")
    print(f"系統指令 (System Instruction): {system_role}")
    print(f"將傳送的 Prompt (前 200 字): {test_prompt[:200]}...")
    print("=============================================")

    try:
        # 4. API 設定與呼叫 (與 6_simplified_schema.py 相同)
        genai.configure(api_key=api_key)
        model_name = 'gemini-2.5-flash'
        
        model = genai.GenerativeModel(model_name, system_instruction=system_role)
        chat = model.start_chat(history=[])
        
        print(f"\n✅ 模型 {model_name} 初始化完畢。")
        print(f"... 正在傳送請求 (要求 {N_VARIATIONS} 個案例)...")
        
        response = chat.send_message(test_prompt)
        actual_output = response.text.strip()
        
        print("\n--- [Gemini 實際輸出] ---")
        print(actual_output)
        print("--- [輸出結束] ---")

        # 5. 執行結構化驗證 (與 6_simplified_schema.py 相同)
        print("\n\n--- 驗證 (Validation) ---")
        
        is_valid, message, parsed_data = validate_llm_output(actual_output, N_VARIATIONS)
        
        print(message) # 顯示 PASS 或 FAIL 訊息

        # 6. (★ 已更新) 儲存檔案
        if is_valid and parsed_data:
            print(f"\n--- 儲存檔案 ---")
            
            full_output_path = "" # 預先定義變數，以便在 except 中使用
            try:
                # (★ 新增) 產生時間戳 (格式: YYYYMMDD_HHMMSS)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # (★ 新增) 組合檔案名稱
                dynamic_filename = f"{timestamp}_cases_delta.json"
                
                # (★ 新增) 組合完整路徑
                full_output_path = os.path.join(OUTPUT_DIRECTORY, dynamic_filename)

                # (★ 新增) 確保目錄存在，如果不存在則自動建立
                print(f"正在確保目錄存在: {OUTPUT_DIRECTORY}")
                os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

                # (★ 更新) 使用 full_output_path 寫入檔案
                with open(full_output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=4, ensure_ascii=False)
                
                print(f"✅ 成功將驗證後的 JSON 儲存至: {full_output_path}")
            
            except Exception as e:
                print(f"❌ 儲存檔案 {full_output_path} 時發生錯誤: {e}")
                print("請檢查您的目錄權限或路徑。")
                
        elif not is_valid:
            print("\n[實際輸出 (用於偵錯)]:")
            print(actual_output)

    except Exception as e:
        print(f"\n❌ 請求或驗證過程中發生錯誤: {e}")
        print("請檢查您的 prompt 內容、網路連線或 API key。")

if __name__ == "__main__":
    run_specific_llm_test()