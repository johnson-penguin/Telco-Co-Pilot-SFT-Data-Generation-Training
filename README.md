## cursor_gen_conf

An end-to-end toolkit for generating erroneous configuration cases, filtering error logs, and automating reasoning runs in Cursor for CU/DU/UE scenarios. It includes:
- Baseline inputs (conf and JSON)
- Massive generated datasets (JSON and .conf)
- Batch run logs and artifacts
- A pipeline to convert datasets into prompt+JSON Markdown and collect Cursor reasoning outputs

This README provides an English overview of the repository layout and how to use each workspace.

### Prerequisites
- Python 3.8+
- Windows 10+ with PowerShell (`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`)
- Sufficient disk space for large datasets and logs

### Repository structure (top-level)
- `0_required_inputs/`
  - `baseline_conf/`: Seeds for CU/DU/UE (e.g., `cu_gnb.conf`, `du_gnb.conf`, `ue_oai.conf`)
  - `baseline_conf_json/`: Baseline configs in JSON (e.g., `cu_gnb.json`, `du_gnb.json`, `ue.json`)
- `1_confgen_workspace/`: Config generation workspace for CU/DU
  - `1_conf/`: Multiple generated sets (e.g., `cu_conf_1009_200`, `du_conf_1014_800`, etc.) containing hundreds to thousands of `.conf` and `.json` files
  - Scripts: `1_to_2_cu_conf_to_json.py`, `1_to_2_du_conf_to_json.py`, `1_to_2_ue_conf_to_json.py`
  - Tools: `tool/cu_generate_error_confs.py`, `tool/du_generate_error_confs.py`, `tool/ue_generate_error_confs.py`
  - `gen_prompt/`: Prompt notes for CU/DU generation (`cu_gen_prompt.md`, `du_gen_prompt.md`)
- `2_runlog_workspace/`: Batch run outputs (logs/json/txt) for many datasets (CU/DU/UE)
- `3_defined_input_format/`: Normalized JSON datasets in a unified input schema
- `4_filter_out_the_error_log/`: Filtered subsets keeping only error-focused cases, with summary reports
- `Reasoning Trace/`: A pipeline converting datasets → prompt+JSON Markdown → Cursor reasoning outputs
- `README.md`: This document

### 1) Config generation (CU/DU/UE) — `1_confgen_workspace/`
Generate erroneous configuration cases from baselines and deltas; produce `.conf` and `.json` artifacts with bilingual inline comments for modified lines.

Key files and folders:
- `1_conf/`:
  - `cu_conf_*`, `du_conf_*`, `ue_conf_*`: large generated sets (e.g., `du_conf_1014_2000` has 2000 `.conf` files and a summary JSON)
- `tool/`:
  - `cu_generate_error_confs.py`, `du_generate_error_confs.py`, `ue_generate_error_confs.py`: render error `.conf` from baselines and case deltas
- `gen_prompt/`: `cu_gen_prompt.md`, `du_gen_prompt.md`

Example commands (run from repo root):
```bash
python "1_confgen_workspace/tool/cu_generate_error_confs.py"
python "1_confgen_workspace/tool/du_generate_error_confs.py"
python "1_confgen_workspace/tool/ue_generate_error_confs.py"
```

Inputs and assumptions:
- Baseline confs: `0_required_inputs/baseline_conf/{cu_gnb.conf,du_gnb.conf,ue_oai.conf}`
- Baseline JSON: `0_required_inputs/baseline_conf_json/{cu_gnb.json,du_gnb.json,ue.json}`
- The generators annotate modified lines with ZH/EN comments for auditability.

### 2) Run logs — `2_runlog_workspace/`
Contains artifacts from batch executions across many datasets. Each subfolder aggregates thousands of `.log` files plus associated `.json`/`.txt` summaries, e.g.:
- `logs_batch_run_du_1014_800/` (≈7.5K files)
- `logs_batch_run_1014_2000/` (≈13K files)
- CU series like `logs_batch_run_cu_1002_400/`, `logs_batch_run_cu_1009_200/`
- UE series like `logs_batch_run_ue_conf_1016_175/`

These are used downstream by filtering and reasoning steps.

### 3) Unified datasets — `3_defined_input_format/`
Canonical JSON datasets in a consistent schema used by the later pipeline. Examples:
- `new_defind_format_1001_400_case/` (400+ files)
- `new_defind_format_1002_600_case/` (600+ files)
- `new_defind_format_1014_800_case/` (800+ files)
- CU/DU/UE-targeted sets like `new_defind_format_cu_1016_150_case/`, `new_defind_format_du_1009_200_case/`, `new_defind_format_ue_1016_175_case/`

`tool/` under this folder contains helpers operating on the unified format.

### 4) Filter error-focused cases — `4_filter_out_the_error_log/`
Creates filtered subsets by removing success/reject cases and keeping only those relevant to error analysis. Each subfolder mirrors a source dataset, with counts and summaries under `param_check_reports/`.

See also the local `Readme.md` here for detailed counts (in Chinese).

### 5) Reasoning pipeline — `Reasoning Trace/`
Automates preparation of prompt+JSON inputs and harvesting of reasoning outputs from Cursor.

Key scripts:
- `0_to_1_tool_filter_error_cases.py`: From a dataset, copy only cases that do not include success/reject signals into `1_after_processing(clean)/`.
- `1_to_2_merge_prompt_with_json.py`: Merge a prompt header with JSON payloads and produce Markdown files under `2_prompt_with_json/`.
- `2_to_3_auto_analysis_tool.py`: Open each Markdown in Cursor, wait for responses written to `cursor_responses/cursor_response.md`, then save outputs into `3_cursor_reasoning/`.

Typical flow:
```bash
# 1) Filter raw cases → cleaned cases
python "Reasoning Trace/0_to_1_tool_filter_error_cases.py"

# 2) Merge prompts with cleaned JSON → Markdown
python "Reasoning Trace/1_to_2_merge_prompt_with_json.py" --json_root_dir "Reasoning Trace/1_after_processing(clean)/filter_defind_format_50_case" --output_dir "Reasoning Trace/2_prompt_with_json/filter_defind_format_50_with_prompt_1"

# 3) Automate reasoning collection in Cursor
python "Reasoning Trace/2_to_3_auto_analysis_tool.py"
```

Notes:
- The automation expects Cursor to update `cursor_responses/cursor_response.md` whenever a response is produced.
- Windows paths in scripts are preconfigured for this repository layout. Adjust if relocating the project.

### Troubleshooting
- Large directory counts: Some folders contain thousands of files; ensure sufficient disk and that your editor/git tooling can handle large trees.
- Encoding: Scripts assume UTF-8. If you encounter encoding errors on Windows, confirm file encodings.
- Missing outputs: Ensure the target output directories are writable; generators will create them if absent.
- Value formatting: JSON→conf renderers may quote strings and preserve hex forms (e.g., `0x12`).

### License and upstream
Any upstream OAI components referenced by this repository follow their own licenses and documentation. This repository does not modify upstream sources directly.

