### 1_confgen_workspace README

This workspace generates erroneous configuration test cases (JSON deltas and derived .conf files) for CU and DU based on baseline configs in `0_required_inputs/`.

#### Directory structure
- **cu_conf_1009_200/**: Generated CU artifacts (200-case set)
  - `json/`: Aggregate `cases_delta.json` and per-case deltas (if any)
  - `conf/`: Rendered `.conf` files with bilingual inline comments
- **du_conf_1009_200/**: Generated DU artifacts (200-case set)
  - `json/`: Aggregate `cases_delta.json` and per-case deltas (if any)
  - `conf/`: Rendered `.conf` files with bilingual inline comments
- **cu_gen_prompt.md / du_gen_prompt.md**: Prompt specs for generating initial 25-case deltas
- Python scripts:
  - `cu_generate_error_confs.py`: Render CU error `.conf` files from `cu_conf_1009_200/json/cases_delta.json` and `baseline_conf/cu_gnb.conf`
  - `du_generate_error_confs.py`: Render DU error `.conf` files from `du_conf_1009_200/json/cases_delta.json` and `baseline_conf/du_gnb.conf`

#### Inputs
- Baseline JSON: `0_required_inputs/baseline_conf_json/{cu_gnb.json, du_gnb.json}`
- Baseline conf: `0_required_inputs/baseline_conf/{cu_gnb.conf, du_gnb.conf}`
- Initial prompts: `cu_gen_prompt.md`, `du_gen_prompt.md`

#### Typical workflows
1) CU — render 200 erroneous confs from existing deltas
```bash
python cu_generate_error_confs.py
```

2) DU — render 200 erroneous confs from existing deltas
```bash
python du_generate_error_confs.py
```

#### Outputs
- JSON deltas: `.../json/du_case_XX.json`, `.../json/cu_case_XX.json`, plus `cases_delta.json`
- Rendered confs: `.../conf/*.conf` with bilingual inline comments after modified lines

#### Notes
- Scripts expect UTF-8 files; Windows PowerShell is supported.
- Array paths like `security.integrity_algorithms[0]` and nested paths like `plmn_list[0].mnc_length` are supported.
- Inline comments are appended to modified lines in generated confs to clarify changes (ZH/EN).

