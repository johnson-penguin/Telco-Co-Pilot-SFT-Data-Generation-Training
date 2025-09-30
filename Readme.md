## cursor_gen_conf

A small toolkit for generating CU/DU error configuration files for OpenAirInterface (OAI) based on a baseline `.conf` and a JSON list of parameter mutations. The scripts annotate each modified line with bilingual comments (Chinese/English) for clarity.

### Contents
- `baseline_conf/`: Baseline configuration seeds used as the starting point
  - `cu_gnb.conf`, `du_gnb.conf`
- `baseline_conf_json/`: Baseline configs in JSON form (reference)
  - `cu_gnb.json`, `du_gnb.json`
- `cu_gen_prompt.md`, `du_gen_prompt.md`: Prompt notes for generating error cases
- `cu_generate_error_confs.py`: Generates CU error `.conf` files from JSON deltas
- `du_generate_error_confs.py`: Generates DU error `.conf` files from JSON deltas
- `cu_output/`:
  - `json/`: CU case deltas (`cases_delta.json`, `cu_case_XX.json`)
  - `error_conf/`: Generated CU error `.conf` files
- `du_output/`:
  - `json/`: DU case deltas (`cases_delta.json`)
  - `error_conf/`: Generated DU error `.conf` files
- `openairinterface5g/`: OAI source tree (for reference/testing; not modified by the generators)

### Prerequisites
- Python 3.8+
- Windows PowerShell or any shell capable of running Python

### Quick Start
1) Prepare baseline configs and error case deltas (already provided in this repo):
   - Baselines: `baseline_conf/c{u|u}_gnb.conf`
   - Deltas: `cu_output/json/cases_delta.json` and `du_output/json/cases_delta.json`

2) Generate CU error configs:
```bash
python cu_generate_error_confs.py
```
Outputs to `cu_output/error_conf/` (e.g., `cu_case_01.conf`).

3) Generate DU error configs:
```bash
python du_generate_error_confs.py
```
Outputs to `du_output/error_conf/` (e.g., `du_case_01.conf`).

### How it works
Both generator scripts read a baseline `.conf`, apply a list of mutations from the corresponding `cases_delta.json`, and write new `.conf` files. Each changed line is annotated with a bilingual comment to show the original and error value, for example:
```
key = "new_value";  # 修改: 原始值 old → 錯誤值 new / Modified: original old → error new
```

Supported mutation keys:
- Plain assignments: `key`
- Array elements: `key[index]`
- Nested array fields (DU script): `block[index].subkey`

### Directory details
- `cu_output/json/` and `du_output/json/`: JSON files describing the changes per case
- `cu_output/error_conf/` and `du_output/error_conf/`: Generated `.conf` files
- `openairinterface5g/`: Upstream OAI codebase used for integration and testing; not directly altered by the scripts here

### Troubleshooting
- No changes applied for a key:
  - Ensure the key exists in the baseline and matches the expected shape (plain vs array vs nested)
  - The scripts log a warning if a target key cannot be found
- String vs numeric values:
  - Values are quoted unless they look like hex (e.g., `0x12`)
- Output directory missing:
  - The scripts create output directories automatically, but verify write permissions if files are not created

### Notes
- All generated files include bilingual change annotations for easier auditing and sharing with mixed-language teams.
- The `openairinterface5g/` tree contains its own LICENSE and documentation. Refer to OAI docs for build/run instructions.


