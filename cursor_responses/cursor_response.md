Updated `3_defined_input_format/process_logs_to_new_format.py` to:
- Scan both `1_confgen_workspace` and `2_runlog_workspace`.
- Build a cases delta index from any `cases_delta.json` found under configs.
- Detect cases by locating `tail100_summary.json` in runlogs and inferring CU/DU and case numbers from directory names.
- Output up to 50 cases (balanced CU/DU when possible) into `3_defined_input_format/new_defind_format_50_case` with `misconfigured_param` and `logs` fields.
- Generate `summary.json` with CU/DU counts.

You can run it directly; it writes results into the specified output folder.

Additionally, added a DU-specific merge mode targeting:
- Logs: `2_runlog_workspace/logs_batch_run_1014_800`
- Configs: `1_confgen_workspace/du_conf_1014_800`
- Output: `3_defined_input_format/new_defind_format_1014_800_case`
This mode merges DU cases using `tail100_summary.json` and `cases_delta.json` to produce `misconfigured_param`, and writes a summary.

Created `3_defined_input_format/cu_process_logs_conf_to_new_format.py` to mirror DU logic for CU cases:
- Scans CU configs `1_confgen_workspace/cu_conf_1009_200` for `cases_delta.json`
- Scans CU runlogs `2_runlog_workspace/logs_batch_run_cu_1002_400`
- Outputs to `3_defined_input_format/new_defind_format_cu_1002_400_case` with `summary.json`
# Convert_to_defind_input.py 程式說明

## 程式功能
成功建立了一支程式 `Convert_to_defind_input.py`，能夠將以下兩個目錄的內容自動轉換成指定格式：

### 輸入來源
1. **配置檔案目錄**: `C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\du_conf_1014_800`
2. **日誌檔案目錄**: `C:\Users\bmwlab\Desktop\cursor_gen_conf\sft_data_processing\logs_batch_run_1014_800`

### 輸出目標
**目標目錄**: `C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\0_input_data(unclean)\new_defind_format_1014_800_case`

## 程式特色

### 1. 自動化處理流程
- 自動讀取 `cases_delta.json` 檔案獲取配置資訊
- 自動掃描日誌目錄中的所有 case 資料夾
- 自動匹配對應的配置和日誌資料

### 2. 資料格式轉換
- 從 `cases_delta.json` 中提取 `modified_key` 和 `error_value`
- 組合生成 `misconfigured_param` 欄位
- 讀取 `tail100_summary.json` 中的日誌資料
- 轉換成目標格式的 JSON 結構

### 3. 輸出格式
每個轉換後的檔案包含：
```json
{
  "misconfigured_param": "MACRLCs[0].remote_n_address=100.64.0.29",
  "logs": {
    "CU": [...],
    "DU": [...],
    "UE": [...]
  }
}
```

## 執行結果

### 處理統計
- **總處理案例數**: 800 個 DU cases
- **CU cases**: 0 個
- **DU cases**: 800 個
- **成功率**: 100%

### 輸出檔案結構
```
new_defind_format_1014_800_case/
├── DU/
│   ├── du_case_01_new_format.json
│   ├── du_case_02_new_format.json
│   ├── ...
│   └── du_case_800_new_format.json
└── summary.json
```

## 程式特點

### 1. 錯誤處理
- 完善的異常處理機制
- 詳細的錯誤訊息輸出
- 繼續處理其他案例，不會因單一錯誤而中斷

### 2. 進度追蹤
- 即時顯示處理進度
- 詳細的處理統計資訊
- 清楚的完成狀態報告

### 3. 檔案命名
- 自動生成符合格式的檔案名稱
- 使用零填充的 case 編號格式
- 統一的檔案命名規範

## 使用方式

```bash
cd "C:\Users\bmwlab\Desktop\cursor_gen_conf"
python Convert_to_defind_input.py
```

## 程式碼結構

### 主要函數
1. `load_cases_delta()`: 載入配置資訊
2. `extract_case_info()`: 提取案例資訊
3. `find_log_file()`: 尋找日誌檔案
4. `process_case()`: 處理單一案例
5. `main()`: 主程式流程

### 路徑設定
- 所有路徑都使用絕對路徑
- 支援 Windows 路徑格式
- 自動建立輸出目錄

## 成功驗證

程式已成功執行並完成所有 800 個案例的轉換，輸出檔案格式正確，符合目標格式要求。所有轉換後的檔案都包含完整的 `misconfigured_param` 和 `logs` 資料，可以直接用於後續的推理分析流程。