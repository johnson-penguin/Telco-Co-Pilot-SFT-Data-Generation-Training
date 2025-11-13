import os
import google.generativeai as genai
import json 
import re   
from datetime import datetime 

# --- ⚠️ PLEASE MODIFY THE FOLLOWING VARIABLES ---

# 1. The specified quantity 'n'
N_VARIATIONS = 5 

# 2. (★ Updated) The final output 'directory'
OUTPUT_DIRECTORY = "/home/ksmo/johnson/Trace-Reasoning-rApp/0_temp"

# --- END OF VARIABLE MODIFICATION ---

# Helper Function: Read File Content
def read_file_content(file_path):
    """Safely reads the content of a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ ERROR: File not found {file_path}")
        print("Please check if your file path is correct.")
        return None
    except Exception as e:
        print(f"❌ An error occurred while reading file {file_path}: {e}")
        return None
# --- Validation Function (Same as 6_simplified_schema.py) ---
def validate_llm_output(output_text, n):
    """
    Validates if the LLM output structure meets expectations.
    (Checks for 4 essential fields)
    """
    try:
        # Try to find the JSON array block (starting with '[' and ending with ']')
        json_match = re.search(r'\[.*\]', output_text, re.DOTALL)
        if not json_match:
            if output_text.startswith('[') and output_text.endswith(']'):
                json_text = output_text
            else:
                 return False, "Validation ❌ FAIL: Could not find a JSON array (i.e., the '[]' block) in the LLM output.", None
        else:
            json_text = json_match.group(0)
            
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return False, f"Validation ❌ FAIL: LLM output is not valid JSON. Error: {e}", None
    except Exception as e:
        return False, f"Validation ❌ FAIL: Unknown error occurred while parsing JSON. {e}", None

    if not isinstance(data, list):
        return False, f"Validation ❌ FAIL: Expected output to be a JSON list (array), but received {type(data)}.", None

    if len(data) != n:
        return False, f"Validation ❌ FAIL: Expected list to have {n} items, but actually received {len(data)}.", None

    required_keys = {
        "filename", 
        "modified_key", 
        "original_value", 
        "error_value"
    }
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"Validation ❌ FAIL: Item number {i} in the list is not a valid JSON object (dictionary).", None
        
        missing_keys = required_keys - item.keys()
        if missing_keys:
            return False, f"Validation ❌ FAIL: Item number {i} in the list is missing required keys: {missing_keys}", None

    return True, f"Validation ✅ PASS: Output format is correct (valid JSON list, containing {n} items, with all 4 fields present).", data


def run_specific_llm_test():
    """
    Executes an automated LLM test.
    Uses the structured 'Fuzz-Test Expert' prompt (4-field version).
    """
    
    # File Paths
    conf_file_path = "/home/ksmo/johnson/Config-Variator-rApp/log_preprocessing_pipeline_tool/0_required_inputs/baseline_conf/du_gnb.conf"
    json_file_path = "/home/ksmo/johnson/Config-Variator-rApp/log_preprocessing_pipeline_tool/0_required_inputs/baseline_conf_json/du_gnb.json"
    
    # 1. Checking API Key
    api_key = os.getenv("Johnson_GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: Could not find Johnson_GOOGLE_API_KEY environment variable.")
        return

    print("✅ Johnson_GOOGLE_API_KEY found.")
 # 2. Reading File Content
    print(f"Reading {conf_file_path}...")
    conf_content = read_file_content(conf_file_path)
    if conf_content is None: return

    print(f"Reading {json_file_path}...")
    json_content = read_file_content(json_file_path)
    if json_content is None: return
        
    print("✅ File reading complete.")

    # 3. Creating System Instruction and Test Prompt (Same as 6_simplified_schema.py)
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
    print(f"System Instruction: {system_role}")
    print(f"Prompt to be sent (first 200 characters): {test_prompt[:200]}...")
    print("=============================================")

    try:
        # 4. API Configuration and Call (Same as 6_simplified_schema.py)
        genai.configure(api_key=api_key)
        model_name = 'gemini-2.5-flash'
        
        model = genai.GenerativeModel(model_name, system_instruction=system_role)
        chat = model.start_chat(history=[])
        
        print(f"\n✅ Model {model_name} initialized.")
        print(f"... Sending request (asking for {N_VARIATIONS} cases)...")
        
        response = chat.send_message(test_prompt)
        actual_output = response.text.strip()
        
        print("\n--- [Gemini Actual Output] ---")
        print(actual_output)
        print("--- [Output End] ---")

        # 5. Executing Structural Validation (Same as 6_simplified_schema.py)
        print("\n\n--- Validation ---")
        
        is_valid, message, parsed_data = validate_llm_output(actual_output, N_VARIATIONS)
        
        print(message) # Displaying PASS or FAIL message

        # 6. (★ Updated) Saving File
        if is_valid and parsed_data:
            print(f"\n--- Saving File ---")
            
            full_output_path = "" # Pre-defining variable for use in the except block
            try:
                # (★ Added) Generating timestamp (Format: YYYYMMDD_HHMMSS)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # (★ Added) Assembling the file name
                dynamic_filename = f"{timestamp}_cases_delta.json"
                
                # (★ Added) Assembling the full path
                full_output_path = os.path.join(OUTPUT_DIRECTORY, dynamic_filename)

                # (★ Added) Ensuring the directory exists; creating it if it doesn't.
                print(f"Ensuring directory exists: {OUTPUT_DIRECTORY}")
                os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

                # (★ Updated) Writing the file using full_output_path
                with open(full_output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=4, ensure_ascii=False)
                
                print(f"✅ Successfully saved validated JSON to: {full_output_path}")
            
            except Exception as e:
                print(f"❌ An error occurred while saving the file {full_output_path}: {e}")
                print("Please check your directory permissions or path.")
                
        elif not is_valid:
            print("\n[Actual Output (for debugging)]:")
            print(actual_output)

    except Exception as e:
        print(f"\n❌ An error occurred during the request or validation process: {e}")
        print("Please check your prompt content, network connection, or API key.")

if __name__ == "__main__":
    run_specific_llm_test()
