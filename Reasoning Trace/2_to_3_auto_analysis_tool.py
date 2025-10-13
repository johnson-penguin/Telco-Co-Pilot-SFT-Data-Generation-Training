import pyautogui
import pyperclip
import time
import os
import glob
import threading

# ---------- 防止螢幕休眠 ----------
stop_mouse_mover = False

def mouse_mover():
    global stop_mouse_mover
    x, y = pyautogui.position()
    while not stop_mouse_mover:
        try:
            pyautogui.moveTo(x + 100, y)
            time.sleep(0.4)
            pyautogui.moveTo(x, y)
            time.sleep(5)
        except Exception as e:
            print(f"Mouse mover error: {e}")
            time.sleep(5)

def start_mouse_mover():
    global stop_mouse_mover
    stop_mouse_mover = False
    mouse_thread = threading.Thread(target=mouse_mover, daemon=True)
    mouse_thread.start()
    print("Mouse mover started")
    return mouse_thread

def stop_mouse_mover_thread():
    global stop_mouse_mover
    stop_mouse_mover = True
    print("Mouse mover stopped")


# ---------- 基本設定 ----------
WAIT_TIME = 2  # 每次輪詢間隔（秒）
response_file = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\cursor_responses\cursor_response.md"

PROMPT_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\2_prompt_with_json\filter_defind_format_1001_400_with_prompt_1"
OUTPUT_BASE = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\3_cursor_reasoning\defind_format_1001_400_with_prompt_1_reason"


# ---------- 載入 prompt ----------
def load_prompts(base_dir):
    table = []
    for category in ["CU", "DU"]:
        folder = os.path.join(base_dir, category)
        if not os.path.exists(folder):
            continue
        prompt_files = glob.glob(os.path.join(folder, "*.md"))
        for file_path in prompt_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            table.append({
                "file": os.path.basename(file_path),
                "category": category,
                "prompt": content
            })
    return table


# ---------- 錯誤檢查 ----------
def checkError():
    img = 'error.png'
    if not os.path.exists(img):
        return False
    try:
        return pyautogui.locateOnScreen(img, confidence=0.8) is not None
    except Exception:
        return False


# ---------- 尋找 Cursor 視窗 ----------
def find_cursor_window():
    try:
        cursor_window = None
        all_windows = pyautogui.getAllWindows()

        for window in all_windows:
            if window.title.endswith("- Cursor"):
                cursor_window = window
                print(f"Found Cursor window (Method 1): {window.title}")
                break

        if not cursor_window:
            for window in all_windows:
                title_lower = window.title.lower()
                if ("cursor" in title_lower and
                    "visual studio code" not in title_lower and
                    "vs code" not in title_lower and
                    window.title.strip() != ""):
                    cursor_window = window
                    print(f"Found Cursor window (Method 2): {window.title}")
                    break

        if cursor_window:
            if cursor_window.isMinimized:
                print("Restoring minimized window...")
                cursor_window.restore()
                time.sleep(2)
            cursor_window.activate()
            time.sleep(1)
            center_x = cursor_window.left + cursor_window.width // 2
            center_y = cursor_window.top + cursor_window.height // 2
            pyautogui.click(center_x, center_y)
            time.sleep(1)
            return True

    except Exception as e:
        print(f"Error activating Cursor window: {e}")
        return False

    print("Cursor window not found")
    return False


# ---------- 傳送 Prompt ----------
def send_prompt(prompt):
    try:
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyperclip.copy(prompt)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        pyautogui.press('enter')
        return True
    except Exception as e:
        print(f"Error sending prompt: {e}")
        return False


# ---------- 監控回應檔案 ----------
def wait_for_response_change(response_file, old_response, max_rounds=50, wait_interval=10):
    """
    舊版風格的等待：比對檔案內容變化，直到 Cursor 寫入新結果。
    max_rounds × wait_interval = 最長等待時間（秒）
    """
    for j in range(max_rounds):
        time.sleep(wait_interval)

        if not os.path.exists(response_file):
            continue

        with open(response_file, "r", encoding="utf-8") as f:
            new_response = f.read()

        print(f"⏳ [{j}] Checking response.md ({j * wait_interval}s passed)")

        if new_response.strip() == old_response.strip():
            continue  # 尚未變化
        else:
            print("✅ Response detected, waiting for completion...")
            time.sleep(35)  # 給 Cursor 一段時間完整寫入
            return new_response  # 回傳新的回應內容

    print("⚠️ Timeout: response.md 未更新")
    return None


# ---------- 主程式 ----------
if __name__ == "__main__":
    try:
        print("Starting Cursor automation...")
        mouse_thread = start_mouse_mover()
        table = load_prompts(PROMPT_DIR)
        print(f"共載入 {len(table)} 個 prompts")

        loaded = find_cursor_window()
        print(f"Cursor window found and focused: {loaded}")

        if not loaded:
            print("❌ Could not find Cursor window.")
            exit()

        pyautogui.hotkey('ctrl', 'l')  # 開啟 AI chat

        # 取得初始修改時間
        if os.path.exists(response_file):
            with open(response_file, "r", encoding="utf-8") as f:
                old_response = f.read()
        else:
            old_response = "9"  # 預設起始內容


        for i, item in enumerate(table):
            category = item["category"]
            filename = item["file"]
            prompt = item["prompt"]

            print(f"\n🟢 [{i+1}/{len(table)}] Sending prompt: {filename}")
            success = send_prompt(prompt)
            if not success:
                print("❌ Failed to send prompt.")
                continue

            # 等待檔案變動
            print("⌛ Waiting for response.md to update...")
            content = wait_for_response_change(response_file, old_response, max_rounds=15, wait_interval=10)


            if not content:
                print("⚠️ Timeout or no update detected.")
                continue

            # 儲存到輸出資料夾
            category_dir = os.path.join(OUTPUT_BASE, category)
            os.makedirs(category_dir, exist_ok=True)

            output_name = filename.replace("_new_format_", "_").replace(".md", "_reasoning_trace.md")
            output_path = os.path.join(category_dir, output_name)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Saved: {output_path}")

            # 清空回應檔
            with open(response_file, "w", encoding="utf-8") as f:
                f.write("9")
            old_response = "9"
            print("🧹 Cleared cursor_response.md")

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        stop_mouse_mover_thread()
        print("Cleanup completed.")
