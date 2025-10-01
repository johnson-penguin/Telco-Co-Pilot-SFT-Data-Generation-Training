#!/usr/bin/env python3
"""
Generate additional DU error-case JSONs to reach a total of 200 cases.
It appends new cases (du_case_26.json .. du_case_200.json) into du_output/json/
and updates du_output/json/cases_delta.json accordingly.

Each case modifies exactly one key (single-key error) and includes:
- filename, modified_key, original_value, error_value, error_type, explanation_zh
"""

import json
import os
from typing import Any, Dict, List, Tuple

BASELINE_JSON_PATH = os.path.join("baseline_conf_json", "du_gnb.json")
JSON_DIR = os.path.join("du_output", "json")
CASES_DELTA_PATH = os.path.join(JSON_DIR, "cases_delta.json")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_dirs() -> None:
    os.makedirs(JSON_DIR, exist_ok=True)


def get_original_value_by_path(root: Dict[str, Any], path: str) -> Any:
    cur: Any = root
    # Supports patterns like: gNBs[0].plmn_list[0].snssaiList[0].sd
    for part in path.split('.'):
        if '[' in part:
            key = part.split('[')[0]
            idx = int(part.split('[')[1].split(']')[0])
            cur = cur[key][idx]
        else:
            cur = cur[part]
    return cur


def next_case_index(existing: List[Dict[str, Any]]) -> int:
    if not existing:
        return 1
    nums = []
    for c in existing:
        name = c.get("filename", "")
        if name.startswith("du_case_"):
            try:
                nums.append(int(name.replace("du_case_", "").replace(".json", "")))
            except Exception:
                pass
    return (max(nums) + 1) if nums else 1


def build_error_catalog() -> List[Tuple[str, List[Dict[str, Any]]]]:
    def v(err_val: Any, err_type: str, zh: str) -> Dict[str, Any]:
        return {"error_value": err_val, "error_type": err_type, "explanation_zh": zh}

    catalog: List[Tuple[str, List[Dict[str, Any]]]] = []

    # Common DU keys
    numeric_keys = [
        "gNBs[0].nr_cellid",
        "gNBs[0].pdsch_AntennaPorts_XP",
        "gNBs[0].pdsch_AntennaPorts_N1",
        "gNBs[0].pusch_AntennaPorts",
        "gNBs[0].maxMIMO_layers",
        "gNBs[0].min_rxtxtime",
        "gNBs[0].sib1_tda",
        "gNBs[0].servingCellConfigCommon[0].absoluteFrequencySSB",
        "gNBs[0].servingCellConfigCommon[0].dl_carrierBandwidth",
        "gNBs[0].servingCellConfigCommon[0].ul_carrierBandwidth",
        "gNBs[0].servingCellConfigCommon[0].prach_ConfigurationIndex",
        "gNBs[0].servingCellConfigCommon[0].preambleTransMax",
        "gNBs[0].servingCellConfigCommon[0].hoppingId",
        "gNBs[0].servingCellConfigCommon[0].nrofDownlinkSlots",
        "gNBs[0].SCTP.SCTP_INSTREAMS",
        "gNBs[0].SCTP.SCTP_OUTSTREAMS",
        "MACRLCs[0].local_n_portc",
        "MACRLCs[0].local_n_portd",
        "MACRLCs[0].remote_n_portc",
        "MACRLCs[0].remote_n_portd",
        "RUs[0].nb_tx",
        "RUs[0].nb_rx",
        "RUs[0].max_rxgain",
        "fhi_72.system_core",
        "fhi_72.io_core",
        "fhi_72.mtu",
    ]
    for key in numeric_keys:
        catalog.append((key, [
            v(-1, "out_of_range", f"將 {key} 設為負值，違反規範導致配置檢查失敗。"),
            v(9999999, "out_of_range", f"將 {key} 設為過大，超出規格限制。"),
            v("invalid_string", "wrong_type", f"將 {key} 類型改為字串，解析失敗。"),
        ]))

    enum_keys = [
        "Asn1_verbosity",
        "gNBs[0].servingCellConfigCommon[0].dl_subcarrierSpacing",
        "gNBs[0].servingCellConfigCommon[0].ul_subcarrierSpacing",
        "gNBs[0].servingCellConfigCommon[0].prach_msg1_FDM",
        "gNBs[0].servingCellConfigCommon[0].restrictedSetConfig",
        "gNBs[0].servingCellConfigCommon[0].pucchGroupHopping",
        "log_config.global_log_level",
        "rfsimulator.modelname",
    ]
    for key in enum_keys:
        catalog.append((key, [
            v("invalid_enum_value", "invalid_enum", f"將 {key} 設為無效枚舉，導致模組初始化失敗。"),
            v(None, "missing_value", f"缺少 {key}，導致策略或流程未定義。"),
            v(123, "wrong_type", f"將 {key} 類型改為數值，造成解析錯誤。"),
        ]))

    ip_keys = [
        "MACRLCs[0].local_n_address",
        "MACRLCs[0].remote_n_address",
    ]
    for key in ip_keys:
        catalog.append((key, [
            v("999.999.999.999", "invalid_format", f"將 {key} 設為無效 IPv4 格式，網路堆疊拒絕。"),
            v("abc.def.ghi.jkl", "invalid_format", f"將 {key} 設為非 IP 字串，地址解析失敗。"),
            v("", "invalid_format", f"將 {key} 設為空字串，無法綁定或連線。"),
        ]))

    array_keys = [
        "RUs[0].bands[0]",
        "fhi_72.fh_config[0].T1a_cp_dl[0]",
        "fhi_72.fh_config[0].T1a_cp_ul[0]",
        "fhi_72.fh_config[0].T1a_up[0]",
        "fhi_72.fh_config[0].Ta4[0]",
    ]
    for key in array_keys:
        catalog.append((key, [
            v(0, "out_of_range", f"將 {key} 設為 0 或異常值，破壞時間配置。"),
            v("", "invalid_format", f"將 {key} 設為空，導致解析錯誤。"),
            v("text", "wrong_type", f"將 {key} 類型改為字串，格式不符。"),
        ]))

    return catalog


def main() -> None:
    ensure_dirs()
    baseline = read_json(BASELINE_JSON_PATH)
    existing: List[Dict[str, Any]] = read_json(CASES_DELTA_PATH)

    start_idx = next_case_index(existing)
    target_total = 200
    to_create = max(0, target_total - (start_idx - 1))
    if to_create == 0:
        print("Nothing to do: already have 200 or more cases.")
        return

    catalog = build_error_catalog()

    new_cases: List[Dict[str, Any]] = []
    cat_i = 0
    case_num = start_idx
    while len(new_cases) < to_create:
        modified_key, variants = catalog[cat_i % len(catalog)]
        variant = variants[(cat_i // len(catalog)) % len(variants)]

        try:
            original_value = get_original_value_by_path(baseline, modified_key)
        except Exception:
            cat_i += 1
            continue

        filename = f"du_case_{case_num:02d}.json"
        case_obj: Dict[str, Any] = {
            "filename": filename,
            "modified_key": modified_key,
            "original_value": original_value,
            "error_value": variant["error_value"],
            "error_type": variant["error_type"],
            "explanation_zh": variant["explanation_zh"],
        }

        write_json(os.path.join(JSON_DIR, filename), case_obj)
        new_cases.append(case_obj)

        case_num += 1
        cat_i += 1

    updated = existing + new_cases
    write_json(CASES_DELTA_PATH, updated)

    print(f"Generated {len(new_cases)} new DU cases. Total: {len(updated)}")
    for c in new_cases[:10]:
        print(f"  + {c['filename']}: {c['modified_key']} -> {c['error_value']} ({c['error_type']})")


if __name__ == "__main__":
    main()


