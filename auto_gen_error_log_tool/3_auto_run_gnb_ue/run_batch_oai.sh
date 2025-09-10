#!/usr/bin/env bash
set -euo pipefail

### ====== 使用者可調整區 / User-tunable Settings ======
# 放一堆 modified conf 的資料夾（會依字母序逐一處理）
# Directory containing modified conf files (processed in lexicographic order)
CONF_DIR="/home/oai72/Johnson/auto_run_gnb_ue/error_conf"

# baseline conf（當對側沒被修改時使用）
# Baseline confs used for the counterpart when only CU/DU is modified
BASELINE_CU="/home/oai72/Johnson/auto_run_gnb_ue/baseline_conf/cu_gnb.conf"
BASELINE_DU="/home/oai72/Johnson/auto_run_gnb_ue/baseline_conf/du_gnb.conf"

# UE conf（固定） / Fixed UE conf
UE_CONF="/home/oai72/Johnson/auto_run_gnb_ue/baseline_conf/ue_oai.conf"

# 可執行檔位置（相對或絕對都可） / Binaries (absolute or relative)
NR_GNB_BIN="/home/oai72/oai_johnson/openairinterface5g/cmake_targets/ran_build/build/nr-softmodem"
NR_UE_BIN="/home/oai72/oai_johnson/openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem"

# RFSIM 伺服器環境變數 / RFSIM server env var
RFSIMULATOR_TARGET="server"

# 每輪測試持續秒數 / Per-run active duration (seconds)
RUNTIME_SECS=30

# 進度點點的間隔秒數（每 N 秒印一個 .）
# Interval in seconds for printing progress dots
PROGRESS_INTERVAL=5

# 啟動間的緩衝秒數（讓前一個元件先起來）
# Staggered start delays (give time for previous component to come up)
DELAY_AFTER_CU=4
DELAY_AFTER_DU=4

# 輸出 log 根目錄 / Logs root directory
LOG_ROOT="./logs_batch_run"
### ====== 使用者可調整區 / End of User-tunable Settings ======


timestamp() { date +"%Y%m%d_%H%M%S"; }

ensure_bins() {
  for b in "$NR_GNB_BIN" "$NR_UE_BIN"; do
    if [[ ! -x "$b" ]]; then
      echo "❌ 找不到或不可執行：$b  / Not found or not executable"
      exit 1
    fi
  done
}

cleanup_procs() {
  # 殺掉所有可能殘留的進程（容忍找不到） / Kill any lingering processes (ignore if none)
  sudo pkill -9 -f "[n]r-softmodem" 2>/dev/null || true
  sudo pkill -9 -f "[n]r-uesoftmodem" 2>/dev/null || true
}

sleep_with_dots() {
  # 每 PROGRESS_INTERVAL 秒印出一個 .，直到 RUNTIME_SECS 結束
  # Print a dot every PROGRESS_INTERVAL seconds until RUNTIME_SECS elapses
  local total="$RUNTIME_SECS"
  local step="$PROGRESS_INTERVAL"
  local elapsed=0

  echo -n "⏱️  測試進行中（${total}s）/ Running (${total}s): "
  while (( elapsed + step <= total )); do
    sleep "$step"
    elapsed=$(( elapsed + step ))
    echo -n "."
  done
  # 若有餘數，補最後一段 / Sleep the remainder if any
  if (( elapsed < total )); then
    sleep $(( total - elapsed ))
  fi
  echo ""  # 換行 / newline
}

run_one_case() {
  local MOD_CONF="$1"
  local CASE_NAME="$2"
  local OUT_DIR="${LOG_ROOT}/$(timestamp)_${CASE_NAME}"
  mkdir -p "$OUT_DIR"

  echo "🚀 ==== 開始測試 / Start Test：$CASE_NAME → log：$OUT_DIR ===="

  # 判斷誰用 modified、誰用 baseline
  local FILE_BASENAME
  FILE_BASENAME="$(basename "$MOD_CONF")"
  shopt -s nocasematch
  local CU_CONF_TO_USE DU_CONF_TO_USE
  if [[ "$FILE_BASENAME" == cu* ]]; then
    CU_CONF_TO_USE="$MOD_CONF"
    DU_CONF_TO_USE="$BASELINE_DU"
  elif [[ "$FILE_BASENAME" == du* ]]; then
    CU_CONF_TO_USE="$BASELINE_CU"
    DU_CONF_TO_USE="$MOD_CONF"
  else
    echo "ℹ️  略過（非 cu/du 開頭）：$FILE_BASENAME  / Skip (not cu/du prefix)"
    return 0
  fi
  shopt -u nocasematch

  # 將 conf 轉為絕對路徑，避免 cd OUT_DIR 後相對路徑失效
  CU_CONF_TO_USE="$(readlink -f "$CU_CONF_TO_USE")"
  DU_CONF_TO_USE="$(readlink -f "$DU_CONF_TO_USE")"
  local UE_CONF_ABS
  UE_CONF_ABS="$(readlink -f "$UE_CONF")"

  echo "🧹 清理殘留進程 / Cleaning up lingering processes..."
  cleanup_procs

  # 在 case 目錄內啟動（stats 檔會落在這裡）
  pushd "$OUT_DIR" >/dev/null

  # 啟動 CU
  echo "🟦 [CU] 啟動 / Launch: $CU_CONF_TO_USE"
  sudo -E env RFSIMULATOR="$RFSIMULATOR_TARGET" \
    "$NR_GNB_BIN" --rfsim --sa \
    -O "$CU_CONF_TO_USE" \
    > "cu.stdout.log" 2>&1 &
  local CU_PID=$!
  echo "    PID = $CU_PID"
  sleep "${DELAY_AFTER_CU}"

  # 啟動 DU
  echo "🟩 [DU] 啟動 / Launch: $DU_CONF_TO_USE"
  sudo -E env RFSIMULATOR="$RFSIMULATOR_TARGET" \
    "$NR_GNB_BIN" --rfsim --sa \
    -O "$DU_CONF_TO_USE" \
    > "du.stdout.log" 2>&1 &
  local DU_PID=$!
  echo "    PID = $DU_PID"
  sleep "${DELAY_AFTER_DU}"

  # 啟動 UE
  echo "🟨 [UE] 啟動 / Launch: $UE_CONF_ABS"
  sudo "$NR_UE_BIN" -r 106 --numerology 1 --band 78 -C 3619200000 \
    --rfsim -O "$UE_CONF_ABS" \
    > "ue.stdout.log" 2>&1 &
  local UE_PID=$!
  echo "    PID = $UE_PID"

  # 跑固定秒數 + 進度點點
  echo "📡  進入測試窗口 / Entering test window..."
  sleep_with_dots

  # 收尾
  echo "🛑 時間到，清理進程 / Time's up, cleaning up processes..."
  cleanup_procs

  # 各自最後 100 行摘要（在 OUT_DIR 內直接讀）
  {
    echo "===== CU stdout (tail -n 100) ====="; tail -n 100 "cu.stdout.log" 2>/dev/null || true; echo
    echo "===== DU stdout (tail -n 100) ====="; tail -n 100 "du.stdout.log" 2>/dev/null || true; echo
    echo "===== UE stdout (tail -n 100) ====="; tail -n 100 "ue.stdout.log" 2>/dev/null || true; echo
  } > "tail100.summary.log"

  # 紀錄本輪使用的 conf
  {
    echo "CASE_NAME=${CASE_NAME}"
    echo "CU_CONF=${CU_CONF_TO_USE}"
    echo "DU_CONF=${DU_CONF_TO_USE}"
    echo "UE_CONF=${UE_CONF_ABS}"
    echo "START_TIME=$(date -Iseconds)"
    echo "DURATION=${RUNTIME_SECS}s"
  } > "run_manifest.txt"

  popd >/dev/null

  echo "✅ ==== 完成 / Done：$CASE_NAME ===="
}


main() {
  echo "🔎 檢查執行檔 / Checking binaries..."
  ensure_bins

  mkdir -p "$LOG_ROOT"

  # Ctrl-C 時也清掉殘留 / Clean up on interrupt
  trap 'echo "⚠️ 捕捉到中斷，清理進程 / Caught interrupt, cleaning up..."; cleanup_procs; exit 130' INT TERM

  # 逐一處理 conf / iterate confs
  shopt -s nullglob
  mapfile -t conf_list < <(ls -1 "${CONF_DIR}"/*.conf | sort)
  shopt -u nullglob

  if (( ${#conf_list[@]} == 0 )); then
    echo "📭 在 ${CONF_DIR} 找不到任何 .conf 檔 / No .conf files found in ${CONF_DIR}"
    exit 1
  fi

  echo "🗂️  待處理數量 / Items to process: ${#conf_list[@]}"

  for conf in "${conf_list[@]}"; do
    case_name="$(basename "$conf" .conf)"
    run_one_case "$conf" "$case_name"
    echo
    # 小休息，避免下一輪太快黏在一起 / short pause between cases
    sleep 2
  done

  echo "🎉 全部測試完成 / All tests finished. Log 根目錄 / Logs root: $LOG_ROOT"
}

main "$@"
