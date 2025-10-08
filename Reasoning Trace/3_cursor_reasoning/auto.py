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


# ---------- 路徑設定 ----------
WAIT_TIME = 10
response_file = r"C:\Users\bmwlab\Desktop\CursorAutomation\cursor_responses\cursor_response.md"

PROMPT_DIR = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\2_prompt_with_json\filter_defind_format_50_with_prompt_1"
OUTPUT_BASE = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\Reasoning Trace\3_cursor_reasoning\defind_format_50_with_prompt_1_reason_auto"


# ---------- 讀取 .md prompt ----------
def load_prompts(base_dir):
    table = []
    for category in ["CU", "DU"]:
        folder = os.path.join(base_dir, category)
        if not os.path.exists(folder):
            print(f"⚠️ 找不到資料夾: {folder}")
            continue
        prompt_files = glob.glob(os.path.join(folder, "*.md"))
        print(f"讀取 {category} 目錄，共 {len(prompt_files)} 個檔案")
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


# ---------- 傳送 prompt ----------
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


# ---------- 主程式 ----------
if __name__ == "__main__":
    try:
        print("Starting Cursor automation...")
        mouse_thread = start_mouse_mover()
        table = load_prompts(PROMPT_DIR)
        print(f"共載入 {len(table)} 個 prompts")

        loaded = find_cursor_window()
        print(f"Cursor window found and focused: {loaded}")

        if loaded:
            time.sleep(1)
            print("Opening AI chat (Ctrl+L)...")
            pyautogui.hotkey('ctrl', 'l')

            old_response = ""
            if os.path.exists(response_file):
                with open(response_file, 'r', encoding='utf-8') as file:
                    old_response = file.read()
            new_response = old_response

            for i, item in enumerate(table):
                prompt = item["prompt"]
                category = item["category"]
                filename = item["file"]

                success = send_prompt(prompt)
                if not success:
                    print("❌ Failed to send prompt")
                    continue

                print(f"Prompt {i+1}/{len(table)} sent successfully!")
                respFileChanged = False

                for j in range(50):
                    time.sleep(WAIT_TIME)
                    if os.path.exists(response_file):
                        with open(response_file, 'r', encoding='utf-8') as file:
                            new_response = file.read()
                    print(f"[{category}] {filename}: {j*10} secs passed")

                    if new_response == old_response:
                        if checkError():
                            print("⚠️ Request blocked error detected")
                            new_response = "Request blocked error"
                            respFileChanged = True
                            break
                        continue
                    else:
                        print(f"✅ Response detected for {filename}")
                        time.sleep(35)
                        respFileChanged = True
                        break

                # ---------- 儲存結果 ----------
                category_dir = os.path.join(OUTPUT_BASE, category)
                os.makedirs(category_dir, exist_ok=True)

                output_name = filename.replace("_new_format_", "_").replace(".md", "_reasoning_trace.md")
                output_path = os.path.join(category_dir, output_name)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(new_response)

                print(f"✅ Saved: {output_path}")

                # 清空 response_file
                with open(response_file, "w", encoding="utf-8") as f:
                    f.write("9")

        else:
            print("Could not find or focus Cursor window")

    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(e)
    finally:
        stop_mouse_mover_thread()
        print("Cleanup completed")
