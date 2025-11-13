### 1_confgen_workspace README

This workspace generates erroneous configuration test cases (JSON deltas and derived .conf files) for CU, DU, and UE based on baseline configs in `0_required_inputs/`.

#### Directory structure

**Input directories:**
- `0_workable_conf/`: Workable baseline configuration files
  - `cu_conf/cu_gnb.conf`
  - `du_conf/du_gnb.conf`
  - `ue_conf/ue_oai.conf`
- `0_workable_json_conf/`: Workable baseline JSON configurations
  - `cu_gnb_json/cu_gnb.json`
  - `du_gnb_json/du_gnb.json`
  - `ue_json/ue_oai.json`

**Generated configuration sets (`1_conf/`):**
- **CU sets:**
  - `cu_conf_1001_200/`: 200 CU error cases (error_conf/, json/)
  - `cu_conf_1002_400/`: 400 CU error cases (error_conf/, json/)
  - `cu_conf_1009_200/`: 200 CU error cases (conf/, json/)
  - `cu_conf_1016_150/`: 150 CU error cases (conf/, json/)
- **DU sets:**
  - `du_conf_1001_200/`: 200 DU error cases (error_conf/, json/)
  - `du_conf_1002_600/`: 600 DU error cases (conf/, json/)
  - `du_conf_1009_200/`: 200 DU error cases (conf/, json/)
  - `du_conf_1014_2000/`: 2000 DU error cases (conf/, json/)
  - `du_conf_1014_800/`: 800 DU error cases (conf/, json/)
- **UE sets:**
  - `ue_conf_1016_175/`: 175 UE error cases (conf/, json/)

Each set contains:
- `conf/` or `error_conf/`: Rendered `.conf` files with bilingual inline comments
- `json/`: JSON deltas (`cases_delta.json` and per-case deltas if any)

**Converted JSON outputs (`2_json/`):**
- Converted JSON files from `.conf` files, organized by configuration set
- Examples: `cu_conf_1001_200_json/`, `du_conf_1014_2000_json/`, `ue_conf_1016_175_json/`

**Tools and scripts:**
- `tool/`: Error configuration generators
  - `cu_generate_error_confs.py`: Generate CU error `.conf` files from JSON deltas
  - `du_generate_error_confs.py`: Generate DU error `.conf` files from JSON deltas
  - `ue_generate_error_confs.py`: Generate UE error `.conf` files from JSON deltas
- Conversion scripts:
  - `1_to_2_cu_conf_to_json.py`: Convert CU `.conf` files to JSON format
  - `1_to_2_du_conf_to_json.py`: Convert DU `.conf` files to JSON format
  - `1_to_2_ue_conf_to_json.py`: Convert UE `.conf` files to JSON format
- `gen_prompt/`: Prompt specifications for generating error cases
  - `cu_gen_prompt.md`: CU generation prompts
  - `du_gen_prompt.md`: DU generation prompts

#### Inputs
- Baseline JSON: `0_required_inputs/baseline_conf_json/{cu_gnb.json, du_gnb.json, ue_oai.json}`
- Baseline conf: `0_required_inputs/baseline_conf/{cu_gnb.conf, du_gnb.conf, ue_oai.conf}`
- Workable configs: `0_workable_conf/` and `0_workable_json_conf/`
- Generation prompts: `gen_prompt/cu_gen_prompt.md`, `gen_prompt/du_gen_prompt.md`

#### Typical workflows

**1) Generate error configurations from JSON deltas:**
```bash
# CU
python tool/cu_generate_error_confs.py

# DU
python tool/du_generate_error_confs.py

# UE
python tool/ue_generate_error_confs.py
```

**2) Convert .conf files to JSON format:**
```bash
# CU
python 1_to_2_cu_conf_to_json.py

# DU
python 1_to_2_du_conf_to_json.py

# UE
python 1_to_2_ue_conf_to_json.py
```

#### Outputs
- **JSON deltas**: `1_conf/{set_name}/json/cases_delta.json` and per-case deltas (if any)
- **Rendered confs**: `1_conf/{set_name}/conf/*.conf` or `1_conf/{set_name}/error_conf/*.conf` with bilingual inline comments after modified lines
- **Converted JSON**: `2_json/{set_name}_json/*.json` - JSON representations of generated `.conf` files

#### Notes
- Scripts expect UTF-8 files; Windows PowerShell is supported.
- Array paths like `security.integrity_algorithms[0]` and nested paths like `plmn_list[0].mnc_length` are supported.
- Inline comments are appended to modified lines in generated confs to clarify changes (ZH/EN).
- Different configuration sets may use different directory naming conventions (`conf/` vs `error_conf/`).
- The workspace supports CU, DU, and UE configuration generation and conversion.

