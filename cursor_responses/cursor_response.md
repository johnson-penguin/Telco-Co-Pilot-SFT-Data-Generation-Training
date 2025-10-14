Conversion tool added and executed.

How to run:
```
python 1_confgen_workspace/du_conf_to_json.py --input 1_confgen_workspace/conf/du_conf_1014_800/conf --output 1_confgen_workspace/conf/du_conf_1014_800/json
```

Notes:
- Output JSONs mirror `0_required_inputs/baseline_conf_json/du_gnb.json` structure.
- Example generated: `1_confgen_workspace/conf/du_conf_1014_800/json/du_case_001.json`.

Hardcoded paths:
- Input (default): `C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\conf\du_conf_1014_800\conf`
- Output (default): `C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\conf\du_conf_1014_800\json`

Run without arguments:
```
python 1_confgen_workspace/du_conf_to_json.py
```


---

2025-10-14: Enhanced DU new-format generator

- Integrated per-case DU config from `1_confgen_workspace/2_json/du_conf_1014_800_json/du_case_XXX.json` into `network_config.du_conf`.
- Filled `network_config.cu_conf` and `network_config.ue_conf` from baselines at `0_required_inputs/baseline_conf_json` (`cu_gnb.json`, `ue.json`).
- Safe fallbacks: if per-case DU JSON missing, `du_conf` remains empty and a warning is printed.
- File edited: `3_defined_input_format/du_process_logs_conf_to_new_format.py`.
 - Change: `misconfigured_param` now records the modified parameter name (from cases_delta), fallback to `Asn1_verbosity` when unknown.

2025-10-14: Enhanced CU new-format generator

- Integrated per-case CU config from `1_confgen_workspace/1_conf/cu_conf/json/cu_case_XXX.json` into `network_config.cu_conf`.
- Filled `network_config.du_conf` and `network_config.ue_conf` from baselines at `0_required_inputs/baseline_conf_json` (`du_gnb.json`, `ue.json`).
- Safe fallbacks: if per-case CU JSON missing, `cu_conf` remains empty and a warning is printed.
- File edited: `3_defined_input_format/cu_process_logs_conf_to_new_format.py`.

