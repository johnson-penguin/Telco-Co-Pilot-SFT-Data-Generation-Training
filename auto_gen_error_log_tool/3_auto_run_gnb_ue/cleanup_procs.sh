cleanup_procs() {
  echo "🧹 Cleaning up all OAI processes and leftover interfaces..."

  # 1. 強制殺掉所有 gNB (nr-softmodem) 和 UE (nr-uesoftmodem)
  sudo pkill -9 -f nr-softmodem 2>/dev/null || true
  sudo pkill -9 -f nr-uesoftmodem 2>/dev/null || true

  # 2. 確認是否還有殘留
  pgrep -a softmodem || echo "✅ No softmodem processes running."

  # 3. 移除殘留的 OAI tunnel (UE 介面)
  if ip link show oaitun_ue1 >/dev/null 2>&1; then
    echo "🗑️  Removing leftover interface oaitun_ue1"
    sudo ip link delete oaitun_ue1
  fi
}
