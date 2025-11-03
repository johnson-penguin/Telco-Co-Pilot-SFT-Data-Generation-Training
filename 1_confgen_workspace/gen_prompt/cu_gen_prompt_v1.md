You are a 5G gNodeB configuration fuzz-test expert. Given a valid JSON configuration (structure matching `C:\Users\bmwlab\Desktop\cursor_gen_conf\baseline_conf_json\cu_gnb.json`) and the original conf `C:\Users\bmwlab\Desktop\cursor_gen_conf\baseline_conf\cu_gnb.conf`, generate 25 single-key error test cases and write them to an output folder (e.g. `C:\Users\bmwlab\Desktop\cursor_gen_conf\cu_output\json`). Follow the rules and output schema below.

## Rules

1. Modify exactly one key per case (single-key error). Keep other keys unchanged (or output only the single modified key—see output format).
2. producing 25 distinct cases, covering different error categories.
3. Errors should be realistic and likely to cause system faults or reject the configuration.
4. Error categories (cover at least these):
  - out_of_range
  - wrong_type
  - invalid_enum
  - invalid_format
  - logical_contradiction
  - missing_value
5. Provide a short professional explanation (1–2 sentences) in English explaining why the modified value causes an error and which flow it affects.
6. Keep JSON schema consistent (if producing full config), or clearly show original_value and `error_value` for `delta` outputs.
7. Produce a summary file `cases_delta.json.`
8. Optional flags: --seed <int> for reproducibility; --format full|delta.
9. If schema constraints exist for the key (e.g., allowed enum), generate errors that violate those constraints.
c
Example delta output
[
 {
    "filename": "cu_case_001.json",
    "modified_key": "paramater",
    "original_value": "original_paramater_value",
    "error_value": "error_paramater_value"
  },
  {
    "filename": "cu_case_002.json",
    "modified_key": "paramater",
    "original_value": "original_paramater_value",
    "error_value": "error_paramater_value"
  },
  .
  .
  .
  .
  .
  .
    {
    "filename": "cu_case_n.json",
    "modified_key": "paramater",
    "original_value": "original_paramater_value",
    "error_value": "error_paramater_value"
  },
]


## Return

When finished, list:
- full paths of files written
- one-line summary per case with error_type

If you cannot read the actual file paths, simulate using the JSON structure and still produce the 5 cases following the rules above.