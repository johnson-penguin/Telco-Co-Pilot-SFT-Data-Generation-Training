
# OAI Automated Test Script

## 📖 Introduction
This script automates **batch testing of OAI (OpenAirInterface)**.  
It launches **CU / DU / UE** based on provided conf files, runs them for a fixed duration, and collects logs.  
After each case, it cleans up leftover processes to avoid deadlocks.

## ⚙️ Features
- Batch testing with multiple **modified conf** files
- Automatic file decision:
  - `cu*` → CU modified + DU baseline
  - `du*` → DU modified + CU baseline
- Launch order: CU → DU → UE
- Each run lasts **30 seconds** (configurable)
- Prints `.` every 5 seconds as progress indicator
- Separate log folder per case, containing:
  - `cu.stdout.log / du.stdout.log / ue.stdout.log`
  - `tail100.summary.log` (last 100 lines)
  - `run_manifest.txt` (test metadata)
  - OAI generated `nrL1_stats.log / nrMAC_stats.log / nrRRC_stats.log`

## 📂 Project Structure
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

## 🚀 Usage
1. Edit the configuration section in the script  
2. Grant execute permission: `chmod +x run_batch_oai.sh`  
3. Run the script: `./run_batch_oai.sh`  
4. Results will be stored in `./logs_batch_run/`, one folder per case.

## 🧹 Cleanup
- Before and after each run, the script calls `cleanup_procs()`:
  - Force kills `nr-softmodem / nr-uesoftmodem`
  - Removes leftovers to ensure clean state

## 🔧 Configurable Parameters
- `RUNTIME_SECS` → Duration per test (default 30s)
- `PROGRESS_INTERVAL` → Progress dot interval (default 5s)
- `DELAY_AFTER_CU` / `DELAY_AFTER_DU` → Startup delays (default 4s)
- `LOG_ROOT` → Log root directory (default `./logs_batch_run`)

## 📌 Notes
- Use `screen` or `tmux` to avoid session interruptions
- Ensure baseline and modified conf files are valid
- If stuck, manually clean up with:
  ```bash
  sudo pkill -9 -f nr-softmodem
  sudo pkill -9 -f nr-uesoftmodem
  sudo ip link delete oaitun_ue1 2>/dev/null
  ```

✍️ Author: Johnson  
📅 Last Update: 2025-09-11
