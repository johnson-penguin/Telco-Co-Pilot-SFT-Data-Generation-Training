DU merge script path fix: Updated `sft_data_processing/du_merge_analyze_with_cases.py` to use script-relative paths and create output directory with parents=True. Re-ran successfully; outputs in `sft_data_processing/merged_du_cases`.

CU analysis regenerated: Updated `sft_data_processing/analyze_tail100_cu_0930.py` to include `explanation_en` and `explanation_zh` for each entry, then re-ran to refresh all 25 JSON files under `sft_data_processing/analyze_log/cu_0930`.

DU merge completed: Created and ran `sft_data_processing/du_merge_analyze_with_cases.py` to merge `analyze_log/du_0930` with `du_cases_split`, output to `sft_data_processing/merged_du_cases` with LLM analysis fields at the top. All 25 DU cases merged; summary saved to `merge_summary.json`.

Analyzed DU logs per `sft_data_processing/3_analyze_log_prompt.md` and regenerated JSON outputs under `sft_data_processing/analyze_log/du_0930` by adding and running `sft_data_processing/analyze_tail100_du_0930.py`. All 25 cases processed successfully.

# 5G Log Analysis 與 Case 合併結果 (LLM分析置頂版)

## 任務完成總結

成功創建並執行了合併腳本，將 `analyze_log` 中的分析結果與 `cu_cases_split` 中對應的案例進行合併。**LLM分析結果現在位於文件頂部**，便於快速查看和分析。

## 合併腳本功能

### 腳本名稱
`merge_analyze_with_cases.py`

### 主要功能
1. **數據加載**：
   - 加載所有 `cu_cases_split` 中的案例數據（25個案例）
   - 加載所有 `analyze_log/cu_0930` 中的分析結果（25個分析文件）

2. **智能匹配**：
   - 根據案例編號自動匹配對應的分析結果
   - 確保每個案例都有對應的分析數據

3. **數據合併**：
   - **LLM分析結果置頂**：將分析結果放在文件最前面
   - 添加 `analyze_log` 字段包含詳細分析結果
   - 添加 `analysis_summary` 字段包含統計摘要
   - 原始案例數據緊隨其後

## 合併後的數據結構 (LLM分析置頂)

每個合併文件現在按以下順序排列：

### 1. LLM分析結果 (置頂)
- `analyze_log`: 結構化分析結果數組
  - `Unit`: 單元（CU/DU/UE）
  - `Error`: 錯誤類型
  - `Log Level`: 日誌級別
  - `Message`: 確切的日誌消息
  - `Event Description`: 事件描述

- `analysis_summary`: 分析統計摘要
  - `total_errors`: 總錯誤數
  - `total_success`: 總成功數
  - `errors_by_unit`: 按單元分類的錯誤數
  - `errors_by_type`: 按類型分類的錯誤數
  - `has_errors`: 是否有錯誤
  - `is_successful`: 是否成功

### 2. 原始案例數據
- `filename`: 原始文件名
- `modified_key`: 修改的配置鍵
- `original_value`: 原始值
- `error_value`: 錯誤值
- `error_type`: 錯誤類型
- `explanation`: 錯誤解釋
- `error_log`: 原始錯誤日誌

## 執行結果

### 處理統計
- **總案例數**: 25個
- **成功合併**: 25個
- **缺失分析數據**: 0個
- **成功率**: 100%

### 輸出文件
- **合併文件**: `merged_cu_cases/cu_case_XX_merged.json` (25個)
- **摘要報告**: `merged_cu_cases/merge_summary.json`

## 文件結構示例

```json
{
  "analyze_log": [
    {
      "Unit": "CU",
      "Error": "Configuration Error",
      "Log Level": "ERROR",
      "Message": "[CONFIG] config_check_intrange: tracking_area_code: 65535 invalid value",
      "Event Description": "Invalid configuration parameter detected"
    }
  ],
  "analysis_summary": {
    "total_errors": 14,
    "total_success": 0,
    "errors_by_unit": {
      "CU": 3,
      "DU": 11
    },
    "errors_by_type": {
      "Configuration Error": 2,
      "System Exit": 1,
      "Connection Failure": 11
    },
    "has_errors": true,
    "is_successful": false
  },
  "filename": "cu_case_02.json",
  "modified_key": "gNBs.tracking_area_code",
  "original_value": 1,
  "error_value": 65535,
  "error_type": "out_of_range",
  "explanation": "將 tracking_area_code 設定為超出有效範圍的值 65535...",
  "error_log": {
    "CU": [...],
    "DU": [...],
    "UE": [...]
  }
}
```

## 案例統計示例

### Case 01 (成功案例)
- 錯誤數: 0
- 成功數: 1
- 狀態: 成功運行
- LLM分析: 正常運行無錯誤

### Case 02 (配置錯誤)
- 錯誤數: 14
- 錯誤類型: 配置錯誤(2), 系統退出(1), 連接失敗(11)
- 錯誤單元: CU(3), DU(11)
- LLM分析: 檢測到配置參數無效

### Case 03 (PLMN不匹配)
- 錯誤數: 3
- 錯誤類型: F1AP設置失敗(2), PLMN不匹配(1)
- 錯誤單元: CU(2), DU(1)
- LLM分析: 檢測到PLMN配置不匹配

## 使用方式

```bash
cd sft_data_processing
python merge_analyze_with_cases.py
```

## 輸出目錄結構

```
sft_data_processing/
├── merged_cu_cases/
│   ├── cu_case_01_merged.json  # LLM分析置頂
│   ├── cu_case_02_merged.json  # LLM分析置頂
│   ├── ...
│   ├── cu_case_25_merged.json  # LLM分析置頂
│   └── merge_summary.json
```

## 優勢

1. **LLM分析優先**: 分析結果位於文件頂部，便於快速查看
2. **完整數據整合**: 將原始案例與分析結果完美結合
3. **統計摘要**: 提供快速錯誤統計和分析
4. **結構化數據**: 便於後續數據處理和分析
5. **自動化處理**: 一次性處理所有25個案例
6. **錯誤追蹤**: 詳細的錯誤分類和統計
7. **易於閱讀**: LLM分析結果優先顯示，提高可讀性

## 改進點

- **LLM分析置頂**: 將最重要的分析結果放在文件最前面
- **快速概覽**: 用戶可以立即看到案例的錯誤狀態和統計信息
- **層次清晰**: 分析結果 → 統計摘要 → 原始數據的清晰層次結構

合併後的數據現在以LLM分析結果為優先，提供了更好的可讀性和實用性，特別適合用於5G網絡配置錯誤的快速分析和機器學習訓練。