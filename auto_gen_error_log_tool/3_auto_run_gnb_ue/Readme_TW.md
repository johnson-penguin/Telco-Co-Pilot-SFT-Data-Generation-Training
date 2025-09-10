
# OAI 自動化測試腳本

## 📖 簡介
本腳本用於 **自動批次執行 OAI (OpenAirInterface) 測試**。
它會根據指定的 conf 檔案，自動啟動 **CU / DU / UE**，運行固定時間並收集 log。
每個 case 測試結束後會自動清理進程，避免殘留導致卡死。

## ⚙️ 功能
- 支援多個 **modified conf** 自動測試 (批次模式)
- 自動判斷檔案種類：
  - `cu*` → 測試 CU modified + DU baseline
  - `du*` → 測試 DU modified + CU baseline
- 自動啟動流程：CU → DU → UE
- 每輪固定運行 **30 秒**（可調整）
- 每 5 秒印出一個 `.` 作為進度條
- 每個 case 獨立 log 資料夾，包含：
  - `cu.stdout.log / du.stdout.log / ue.stdout.log`
  - `tail100.summary.log`（各 log 最後 100 行）
  - `run_manifest.txt`（測試紀錄）
  - OAI 產生的 `nrL1_stats.log / nrMAC_stats.log / nrRRC_stats.log`

## 📂 專案結構
```
.
├── run_batch_oai.sh
├── logs_batch_run/
│   ├── 20250911_101530_cu_gnb.row001.modified/
│   │   ├── cu.stdout.log
│   │   ├── du.stdout.log
│   │   ├── ue.stdout.log
│   │   ├── tail100.summary.log
│   │   ├── run_manifest.txt
│   │   ├── nrL1_stats.log
│   │   ├── nrMAC_stats.log
│   │   └── nrRRC_stats.log
│   └── ...
└── baseline_conf/
    ├── cu_gnb.conf
    ├── du_gnb.conf
    └── ue_oai.conf
```

## 🚀 使用方法
1. 修改腳本中的設定區域
2. 給予執行權限：`chmod +x run_batch_oai.sh`
3. 執行腳本：`./run_batch_oai.sh`
4. 結果會輸出到 `./logs_batch_run/`，每個 case 一個資料夾。

## 🧹 清理機制
- 每個 case 前後，腳本會自動呼叫 `cleanup_procs()`：
  - 強制殺掉 `nr-softmodem / nr-uesoftmodem`
  - 清理殘留進程，避免干擾下次測試

## 🔧 可調整參數
- `RUNTIME_SECS` → 每輪測試時長 (預設 30 秒)
- `PROGRESS_INTERVAL` → 進度點點間隔 (預設 5 秒)
- `DELAY_AFTER_CU` / `DELAY_AFTER_DU` → 啟動間隔 (預設 4 秒)
- `LOG_ROOT` → log 根目錄 (預設 `./logs_batch_run`)

## 📌 注意事項
- 建議使用 `screen` 或 `tmux` 避免 session 中斷
- 確保 baseline 與 modified conf 格式正確
- 如遇到卡死可手動清理：
  ```bash
  sudo pkill -9 -f nr-softmodem
  sudo pkill -9 -f nr-uesoftmodem
  sudo ip link delete oaitun_ue1 2>/dev/null
  ```

✍️ Author: Johnson  
📅 Last Update: 2025-09-11
