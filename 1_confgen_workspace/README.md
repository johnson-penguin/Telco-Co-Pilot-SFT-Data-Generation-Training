### 1_confgen_workspace README

This workspace generates erroneous configuration test cases (JSON deltas and derived .conf files) for CU and DU based on baseline configs in `0_required_inputs/`.

#### Directory structure
- **cu_conf/**: Generated CU artifacts
  - `json/`: Per-case JSON deltas and aggregate `cases_delta.json`
  - `error_conf/`: Rendered `.conf` files with bilingual inline comments
- **cu_conf_1002_400/**: Larger CU set variant (e.g., 400 rendered confs)
  - Same subfolders: `json/`, `error_conf/`
- **du_conf/**: Generated DU artifacts
  - `json/`: Per-case JSON deltas and aggregate `cases_delta.json`
  - `error_conf/`: Rendered `.conf` files with bilingual inline comments
- **du_conf_1002_600/**: Larger DU set variant (e.g., 600 cases; first 400 rendered by default)
  - Same subfolders: `json/`, `error_conf/`
- **cu_gen_prompt.md / du_gen_prompt.md**: Prompt specs for generating initial 25-case deltas
- Python scripts:
  - `cu_generate_error_confs.py`: Render CU error `.conf` files from `cu_output/json/cases_delta.json` and `baseline_conf/cu_gnb.conf`
  - `cu_generate_more_cases.py`: Expand CU cases to 200 and update `cu_output/json/cases_delta.json`
  - `cu_update_explanations.py`: Add `explanation_en` from `explanation_zh` for CU cases
  - `du_generate_error_confs.py`: Render DU error `.conf` files from `du_output/json/cases_delta.json` and `baseline_conf/du_gnb.conf`
  - `du_generate_more_cases.py`: Expand DU cases to 200 and update `du_output/json/cases_delta.json`
  - `du_generate_1002_600.py`: Build a 600-case DU set and render confs into `du_conf_1002_400`

#### Inputs
- Baseline JSON: `0_required_inputs/baseline_conf_json/{cu_gnb.json, du_gnb.json}`
- Baseline conf: `0_required_inputs/baseline_conf/{cu_gnb.conf, du_gnb.conf}`
- Initial prompts: `cu_gen_prompt.md`, `du_gen_prompt.md`

#### Typical workflows
1) CU — expand to 200 cases and render confs
```bash
python cu_generate_more_cases.py
python cu_generate_error_confs.py
```

2) DU — expand to 200 cases and render confs
```bash
python du_generate_more_cases.py
python du_generate_error_confs.py
```

3) DU — build 600 cases (writes to `du_conf_1002_400`) and render first 400 confs
```bash
python du_generate_1002_600.py --rebuild
# optionally render all 600 confs
python du_generate_1002_600.py --render-all
```

4) CU — enrich explanations with English text
```bash
python cu_update_explanations.py
```

#### Outputs
- JSON deltas: `.../json/du_case_XX.json`, `.../json/cu_case_XX.json`, plus `cases_delta.json`
- Rendered confs: `.../error_conf/*.conf` with bilingual inline comments after modified lines

#### Notes
- Scripts expect UTF-8 files; Windows PowerShell is supported.
- Array paths like `security.integrity_algorithms[0]` and nested paths like `plmn_list[0].mnc_length` are supported.
- Inline comments are appended to modified lines in generated confs to clarify changes (ZH/EN).

