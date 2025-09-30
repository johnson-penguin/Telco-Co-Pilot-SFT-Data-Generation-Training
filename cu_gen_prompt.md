You are a 5G gNodeB configuration fuzz-test expert. Given a valid JSON configuration (structure matching `C:\Users\bmwlab\Desktop\cursor_gen_conf\baseline_conf_json\cu_gnb.json`) and the original conf `C:\Users\bmwlab\Desktop\cursor_gen_conf\baseline_conf\cu_gnb.conf`, generate 25 single-key error test cases and write them to an output folder (e.g. `C:\Users\bmwlab\Desktop\cursor_gen_conf\cu_output\json`). Follow the rules and output schema below.

## Rules

1. Modify exactly one key per case (single-key error). Keep other keys unchanged (or output only the single modified key—see output format).
2. Produce 25 distinct cases, covering different error categories.
3. Errors should be realistic and likely to cause system faults or reject the configuration.
4. Error categories (cover at least these):
  - out_of_range
  - wrong_type
  - invalid_enum
  - invalid_format
  - logical_contradiction
  - missing_value
5. Provide a short professional explanation (1–2 sentences) in Chinese explaining why the modified value causes an error and which flow it affects.
6. Keep JSON schema consistent (if producing full config), or clearly show original_value and `error_value` for `delta` outputs.
7. Name files `cu_case_01.json` … `cu_case_n.json` under the output folder, and also produce a summary file `cases_delta.json.`
8. Optional flags: --seed <int> for reproducibility; --format full|delta.
9. If schema constraints exist for the key (e.g., allowed enum), generate errors that violate those constraints.
c
Example delta output
[
  {
    "filename": "case_01.json",
    "modified_key": "security.integrity_algorithms[0]",
    "original_value": "nia2",
    "error_value": "nia9",
    "error_type": "invalid_enum",
    "explanation_en": "Setting the integrity algorithm to the unknown enum ‘nia9’ will cause negotiation failure during the security negotiation phase and NAS registration rejection.",
    "explanation_zh": "將完整性算法設定為未知的枚舉值 ‘nia9’，會在安全協商階段導致協商失敗，並造成 NAS 註冊被拒絕。"
  }
]

## Return

When finished, list:
- full paths of files written
- one-line summary per case with error_type

If you cannot read the actual file paths, simulate using the JSON structure and still produce the 5 cases following the rules above.