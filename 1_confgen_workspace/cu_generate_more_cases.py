#!/usr/bin/env python3
"""
Generate additional CU error-case JSONs to reach a total of 200 cases.
It appends new cases (cu_case_26.json .. cu_case_200.json) into cu_output/json/
and updates cu_output/json/cases_delta.json accordingly.

Each case modifies exactly one key (single-key error) and includes:
- filename, modified_key, original_value, error_value, error_type, explanation

Categories covered repeatedly: out_of_range, wrong_type, invalid_enum, invalid_format,
logical_contradiction, missing_value.
"""

import json
import os
from typing import Any, Dict, List, Tuple

BASELINE_JSON_PATH = os.path.join("baseline_conf_json", "cu_gnb.json")
JSON_DIR = os.path.join("cu_output", "json")
CASES_DELTA_PATH = os.path.join(JSON_DIR, "cases_delta.json")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_original_value_by_path(root: Dict[str, Any], path: str) -> Any:
    """Resolve a dotted path like 'gNBs.SCTP.SCTP_INSTREAMS' or 'security.ciphering_algorithms[0]'."""
    cur: Any = root
    parts = path.split('.')
    for part in parts:
        if '[' in part and ']' in part:
            key = part.split('[')[0]
            idx = int(part.split('[')[1].split(']')[0])
            cur = cur[key][idx]
        else:
            cur = cur[part]
    return cur


def ensure_dirs() -> None:
    os.makedirs(JSON_DIR, exist_ok=True)


def next_case_index(existing: List[Dict[str, Any]]) -> int:
    if not existing:
        return 1
    # filenames like cu_case_01.json
    nums = []
    for c in existing:
        try:
            name = c.get("filename", "")
            num = int(name.replace("cu_case_", "").replace(".json", ""))
            nums.append(num)
        except Exception:
            continue
    return (max(nums) + 1) if nums else 1


def build_error_catalog(baseline: Dict[str, Any]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """Return a list of (modified_key, variants[]) where variants are different error cases for that key."""
    catalog: List[Tuple[str, List[Dict[str, Any]]]] = []

    def v(err_val: Any, err_type: str, zh: str) -> Dict[str, Any]:
        return {"error_value": err_val, "error_type": err_type, "explanation": zh}

    # Numeric fields
    numeric_keys = [
        "Num_Threads_PUSCH",
        "gNBs.tracking_area_code",
        "gNBs.nr_cellid",
        "gNBs.local_s_portc",
        "gNBs.local_s_portd",
        "gNBs.remote_s_portc",
        "gNBs.remote_s_portd",
        "gNBs.SCTP.SCTP_INSTREAMS",
        "gNBs.SCTP.SCTP_OUTSTREAMS",
        "gNBs.NETWORK_INTERFACES.GNB_PORT_FOR_S1U",
        "gNBs.plmn_list.mcc",
        "gNBs.plmn_list.mnc",
        "gNBs.plmn_list.mnc_length",
        "gNBs.plmn_list.snssaiList.sst",
    ]
    for key in numeric_keys:
        catalog.append(
            (
                key,
                [
                    v(9999999, "out_of_range", f"將 {key} 設為超出範圍值，導致配置驗證失敗。"),
                    v(-1, "out_of_range", f"將 {key} 設為負值，違反協議或範圍限制。"),
                    v("invalid_string", "wrong_type", f"將 {key} 類型改為字串，導致解析錯誤。"),
                ],
            )
        )

    # IP fields
    ip_keys = [
        "gNBs.amf_ip_address.ipv4",
        "gNBs.NETWORK_INTERFACES.GNB_IPV4_ADDRESS_FOR_NG_AMF",
        "gNBs.NETWORK_INTERFACES.GNB_IPV4_ADDRESS_FOR_NGU",
        "gNBs.local_s_address",
        "gNBs.remote_s_address",
    ]
    for key in ip_keys:
        catalog.append(
            (
                key,
                [
                    v("999.999.999.999", "invalid_format", f"將 {key} 設為無效 IPv4 格式，導致連線建立失敗。"),
                    v("abc.def.ghi.jkl", "invalid_format", f"將 {key} 設為非 IP 字串，導致地址解析錯誤。"),
                    v("", "invalid_format", f"將 {key} 設為空字串，導致地址配置缺失。"),
                ],
            )
        )

    # Enum-like fields
    enum_keys = [
        "Asn1_verbosity",
        "gNBs.tr_s_preference",
        "security.drb_ciphering",
        "security.drb_integrity",
        "log_config.global_log_level",
        "log_config.hw_log_level",
        "log_config.phy_log_level",
        "log_config.mac_log_level",
        "log_config.rlc_log_level",
        "log_config.pdcp_log_level",
        "log_config.rrc_log_level",
        "log_config.ngap_log_level",
        "log_config.f1ap_log_level",
    ]
    for key in enum_keys:
        catalog.append(
            (
                key,
                [
                    v("invalid_enum_value", "invalid_enum", f"將 {key} 設為無效枚舉值，導致配置驗證失敗。"),
                    v(None, "missing_value", f"缺少 {key} 配置項，導致策略或日誌初始化錯誤。"),
                    v(123, "wrong_type", f"將 {key} 類型改為數值，導致解析錯誤。"),
                ],
            )
        )

    # Algorithm arrays
    array_keys = [
        "security.ciphering_algorithms[0]",
        "security.ciphering_algorithms[1]",
        "security.ciphering_algorithms[2]",
        "security.integrity_algorithms[0]",
        "security.integrity_algorithms[1]",
    ]
    for key in array_keys:
        catalog.append(
            (
                key,
                [
                    v("nea9" if "cipher" in key else "nia9", "invalid_enum", f"將 {key} 設為未知算法，導致安全協商失敗。"),
                    v(0, "wrong_type", f"將 {key} 類型改為數值，導致協商解析錯誤。"),
                    v("", "invalid_format", f"將 {key} 設為空字串，導致算法配置缺失。"),
                ],
            )
        )

    # Name/id string fields
    str_keys = [
        "gNBs.gNB_ID",
        "gNBs.gNB_name",
    ]
    for key in str_keys:
        catalog.append(
            (
                key,
                [
                    v("", "invalid_format", f"將 {key} 設為空，導致識別或註冊流程失敗。"),
                    v(None, "missing_value", f"缺少 {key}，導致系統初始化錯誤。"),
                    v(12345, "wrong_type", f"將 {key} 類型改為數值，導致解析失敗。"),
                ],
            )
        )

    return catalog


def main() -> None:
    ensure_dirs()
    baseline = read_json(BASELINE_JSON_PATH)

    # Load existing aggregate list (25 cases already present)
    existing: List[Dict[str, Any]] = read_json(CASES_DELTA_PATH)

    start_idx = next_case_index(existing)
    target_total = 200
    to_create = max(0, target_total - (start_idx - 1))
    if to_create == 0:
        print("Nothing to do: already have 200 or more cases.")
        return

    catalog = build_error_catalog(baseline)

    new_cases: List[Dict[str, Any]] = []
    cat_i = 0
    case_num = start_idx
    while len(new_cases) < to_create:
        modified_key, variants = catalog[cat_i % len(catalog)]
        variant = variants[(cat_i // len(catalog)) % len(variants)]

        # Determine original value from baseline (best-effort; if path is not present, skip)
        try:
            original_value = get_original_value_by_path(baseline, modified_key)
        except Exception:
            # Skip keys not present in baseline JSON representation
            cat_i += 1
            continue

        filename = f"cu_case_{case_num:02d}.json"
        case_obj = {
            "filename": filename,
            "modified_key": modified_key,
            "original_value": original_value,
            "error_value": variant["error_value"],
            "error_type": variant["error_type"],
            "explanation": variant["explanation"],
        }

        # Write per-case file
        write_json(os.path.join(JSON_DIR, filename), case_obj)
        new_cases.append(case_obj)

        case_num += 1
        cat_i += 1

    # Update aggregate list
    updated = existing + new_cases
    write_json(CASES_DELTA_PATH, updated)

    print(f"Generated {len(new_cases)} new cases. Total: {len(updated)}")
    for c in new_cases[:10]:
        print(f"  + {c['filename']}: {c['modified_key']} -> {c['error_value']} ({c['error_type']})")


if __name__ == "__main__":
    main()


