import os
import datetime

def summarize_and_update_readme(root_dir, readme_path):
    """
    遍歷指定的根目錄，計算 'CU', 'DU', 'UE' 子資料夾中的檔案數量，
    然後將詳細結果和總結更新到指定的 Readme.md 檔案中。

    Args:
        root_dir (str): 要分析的根目錄路徑。
        readme_path (str): 要更新的 Readme.md 檔案的完整路徑。
    """
    # 檢查根目錄是否存在
    if not os.path.isdir(root_dir):
        print(f"❌ 錯誤：找不到目錄 '{root_dir}'，請檢查路徑。")
        return

    # 用於儲存總數的字典
    total_counts = {'CU': 0, 'DU': 0, 'UE': 0}
    
    # 用於建立 Markdown 檔案內容的列表
    markdown_output = []

    # --- 1. 產生詳細計數 ---
    print("--- 各資料夾詳細計數 ---")
    markdown_output.append("# 檔案計數報告")
    markdown_output.append(f"> 最後更新時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_output.append("\n---\n")
    markdown_output.append("## 📁 各資料夾詳細計數")

    # 遍歷根目錄中的所有項目，並排序以確保順序一致
    for folder_name in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, folder_name)

        # 只處理資料夾
        if os.path.isdir(folder_path):
            print(f"\n📁 資料夾：{folder_name}")
            
            folder_content = [] # 暫存這個資料夾的內容，如果為空則不加入
            
            # 檢查 'CU', 'DU', 'UE' 子資料夾
            for component in ['CU', 'DU', 'UE']:
                component_path = os.path.join(folder_path, component)

                if os.path.isdir(component_path):
                    try:
                        # 計算此目錄中的檔案數量（過濾掉子目錄）
                        num_files = len([name for name in os.listdir(component_path)
                                         if os.path.isfile(os.path.join(component_path, name))])
                        
                        if num_files > 0:
                            line = f"  - {component}: {num_files} cases"
                            print(line)
                            folder_content.append(f"- **{component}**: `{num_files}` cases")
                            # 累加到總數
                            total_counts[component] += num_files
                    
                    except OSError as e:
                        print(f"    無法讀取 {component_path}: {e}")

            # 如果這個資料夾下有找到任何 case，才將標題和內容加入 Markdown
            if folder_content:
                markdown_output.append(f"\n### {folder_name}")
                markdown_output.extend(folder_content)

    # --- 2. 產生總結 ---
    summary_title = "\n" + "="*25 + "\n📊 總結\n" + "="*25
    print(summary_title)
    print(f"總計 CU cases: {total_counts['CU']}")
    print(f"總計 DU cases: {total_counts['DU']}")
    print(f"總計 UE cases: {total_counts['UE']}")

    markdown_output.append("\n<br>\n\n---\n")
    markdown_output.append("## 📊 總結")
    markdown_output.append(f"- **總計 CU cases**: `{total_counts['CU']}`")
    markdown_output.append(f"- **總計 DU cases**: `{total_counts['DU']}`")
    markdown_output.append(f"- **總計 UE cases**: `{total_counts['UE']}`")

    # --- 3. 將結果寫入 Readme.md ---
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(markdown_output))
        print(f"\n✅ 報告已成功更新至：{readme_path}")
    except IOError as e:
        print(f"\n❌ 寫入檔案時發生錯誤：{e}")

# --- 如何使用 ---
# 1. 下方的路徑已經為您設定好。
# 2. 直接執行此 Python 腳本即可。

# 要分析的目標資料夾
target_directory = r'C:\Users\bmwlab\Desktop\cursor_gen_conf\4_filter_out_the_error_log'
# 要寫入的 Readme.md 檔案路徑
readme_file_path = r'C:\Users\bmwlab\Desktop\cursor_gen_conf\4_filter_out_the_error_log\Readme.md'

# 執行主功能
summarize_and_update_readme(target_directory, readme_file_path)