## Reasoning Trace

This folder contains a three-stage pipeline that transforms raw log-derived JSON cases into prompt-embedded Markdown inputs and finally collects reasoning outputs. It is organized as: input data → filtered/cleaned cases → prompt-merged Markdown → automated Cursor reasoning capture.

### Folder structure
- `0_input_data(unclean)/`: Raw JSON cases in a unified schema, grouped by datasets.
  - `new_defind_format_50_case/`, `new_defind_format_1001_400_case/`, `new_defind_format_1002_1000_case/`
    - `CU/`, `DU/`: component-specific cases
    - `summary.json`: dataset-level quick stats or metadata

- `1_after_processing(clean)/`: Filtered error-focused cases produced by the filter tool.
  - Mirrors CU/DU subfolders per dataset, containing only cases without the success or reject signals.

- `2_prompt_with_json/`: Prompt templates merged with JSON payloads into Markdown files (inputs to Cursor).
  - `filter_defind_format_50_with_prompt_1/`
    - `CU/`, `DU/`: Markdown files per case combining the prompt header and pretty-printed JSON.

- `3_cursor_reasoning/`: Reasoning traces captured from Cursor for the Markdown inputs.
  - `defind_format_50_with_prompt_1_reason/`
    - `CU/`, `DU/`: finalized reasoning outputs.

- `0_prompt/`: Prompt templates (e.g., `prompt_ex_1`, `prompt_ex_2`, `prompt_ex_3`).

### Key scripts
- `0_to_1_tool_filter_error_cases.py`
  - Purpose: From an input dataset, copy only cases that do NOT contain either:
    - "Received PDU Session Establishment Accept"
    - "Received PDU Session Establishment reject"
  - Preserves CU/DU structure under `1_after_processing(clean)/<dataset>`.

- `1_to_2_merge_prompt_with_json.py`
  - Purpose: Merge a text prompt with JSON cases and produce Markdown files.
  - Finds the line "JSON File" in the prompt and appends pretty-printed JSON after it.
  - Outputs to `2_prompt_with_json/<target_folder>` mirroring CU/DU subfolders.

- `2_to_3_auto_analysis_tool.py`
  - Purpose: Automate sending Markdown prompts to Cursor and harvesting the reasoning outputs.
  - Loads Markdown from `2_prompt_with_json/.../CU|DU`, opens/focuses Cursor, pastes content, waits for `cursor_responses/cursor_response.md` to change, then writes results into `3_cursor_reasoning/.../CU|DU`.
  - Includes a lightweight mouse-move thread to prevent screen sleep.

### Typical workflow
1) Filter raw cases → cleaned cases
   - Configure input/output dataset paths inside `0_to_1_tool_filter_error_cases.py` (defaults target `.../new_defind_format_1001_400_case` → `.../filter_defind_format_1001_400_case`).
   - Run the script to create the filtered dataset in `1_after_processing(clean)/`.

2) Merge prompts with cleaned JSON → Markdown
   - Verify or set the prompt file in `1_to_2_merge_prompt_with_json.py` (default `0_prompt/prompt_ex_1`).
   - Choose one of:
     - Single file: `--json <path/to/file.json>`
     - Flat directory: `--json_dir <path/to/dir>`
     - Root with CU/DU: `--json_root_dir <path/to/root>` (default points to `filter_defind_format_50_case`).
   - The script writes `<case_name>_reasoning_trace.md` into `2_prompt_with_json/.../CU|DU`.

3) Auto-run in Cursor → collect reasoning
   - Review constants in `2_to_3_auto_analysis_tool.py`:
     - `PROMPT_DIR`: input Markdown root (e.g., `2_prompt_with_json/filter_defind_format_50_with_prompt_1`).
     - `OUTPUT_BASE`: output root under `3_cursor_reasoning/...`.
     - `response_file`: the file Cursor updates (project root `cursor_responses/cursor_response.md`).
   - Start the script. It will iterate CU/DU Markdown files, paste into Cursor, wait for `cursor_response.md` updates, then save each reasoning to the corresponding CU/DU folder.

### Notes
- Windows paths in scripts are preconfigured for this repository layout. Adjust if you relocate the project.
- The filtering logic only removes cases containing explicit success or reject signals; everything else is retained for analysis.
- The prompt merge keeps your original prompt header and appends the JSON payload for consistent context.

### Quick commands (examples)
```bash
# 1) Filter a dataset (adjust inside the script if needed)
python "Reasoning Trace/0_to_1_tool_filter_error_cases.py"

# 2) Merge prompts with a CU/DU root folder
python "Reasoning Trace/1_to_2_merge_prompt_with_json.py" --json_root_dir "Reasoning Trace/1_after_processing(clean)/filter_defind_format_50_case" --output_dir "Reasoning Trace/2_prompt_with_json/filter_defind_format_50_with_prompt_1"

# 3) Automate reasoning collection
python "Reasoning Trace/2_to_3_auto_analysis_tool.py"
```


