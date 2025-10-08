#!/usr/bin/env python3
"""
Generate 600 DU error-case JSONs and corresponding .conf files
into 1_confgen_workspace/du_conf_1002_400/{json,error_conf}.

This rebuilds cases from scratch when --rebuild is provided, numbering
du_case_01..du_case_600. Uses DU baseline JSON and conf, and a catalog
of DU keys and error variants similar to du_generate_more_cases.py.
"""

import json
import os
import re
import sys
import shutil
from typing import Any, Dict, List, Tuple

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Inputs (prefer 0_required_inputs; fallback to legacy)
BASELINE_JSON_PATH = os.path.join(WORKSPACE_ROOT, "0_required_inputs", "baseline_conf_json", "du_gnb.json")
if not os.path.exists(BASELINE_JSON_PATH):
    BASELINE_JSON_PATH = os.path.join(WORKSPACE_ROOT, "baseline_conf_json", "du_gnb.json")

BASELINE_CONF_PATH = os.path.join(WORKSPACE_ROOT, "0_required_inputs", "baseline_conf", "du_gnb.conf")
if not os.path.exists(BASELINE_CONF_PATH):
    BASELINE_CONF_PATH = os.path.join(WORKSPACE_ROOT, "baseline_conf", "du_gnb.conf")

# Outputs
OUT_ROOT = os.path.join(WORKSPACE_ROOT, "1_confgen_workspace", "du_conf_1002_400")
JSON_DIR = os.path.join(OUT_ROOT, "json")
CONF_DIR = os.path.join(OUT_ROOT, "error_conf")
CASES_PATH = os.path.join(JSON_DIR, "cases_delta.json")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_by_path(root: Dict[str, Any], path: str) -> Any:
    cur: Any = root
    # Supports patterns like gNBs[0].plmn_list[0].snssaiList[0].sd
    for part in path.split('.'):
        if '[' in part and ']' in part:
            key = part.split('[')[0]
            idx = int(part.split('[')[1].split(']')[0])
            cur = cur[key][idx]
        else:
            cur = cur[part]
    return cur


def build_catalog() -> Tuple[Dict[str, List[Tuple[Any, str, str]]], List[str]]:
    variants_catalog: Dict[str, List[Tuple[Any, str, str]]] = {
        "numeric": [
            (-1, "out_of_range", "將數值設為負值，違反規範導致配置檢查失敗。"),
            (9999999, "out_of_range", "將數值設為過大，超出規格限制。"),
            ("invalid_string", "wrong_type", "將數值改為字串，解析失敗。"),
        ],
        "enum": [
            ("invalid_enum_value", "invalid_enum", "無效枚舉，導致模組初始化失敗。"),
            (None, "missing_value", "缺少配置項，導致策略或流程未定義。"),
            (123, "wrong_type", "將枚舉型別改為數值，造成解析錯誤。"),
        ],
        "ip": [
            ("999.999.999.999", "invalid_format", "無效 IPv4 格式，網路堆疊拒絕。"),
            ("abc.def.ghi.jkl", "invalid_format", "非 IP 字串，地址解析失敗。"),
            ("", "invalid_format", "空字串，無法綁定或連線。"),
        ],
        "array": [
            (0, "out_of_range", "將值設為 0 或異常，破壞時間/頻段配置。"),
            ("", "invalid_format", "空值導致解析錯誤。"),
            ("text", "wrong_type", "型別不符，格式錯誤。"),
        ],
    }

    keys: List[str] = []
    def add(xs: List[str]) -> None:
        keys.extend(xs)

    # Numeric
    add([
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
    ])
    # Enum
    add([
        "Asn1_verbosity",
        "gNBs[0].servingCellConfigCommon[0].dl_subcarrierSpacing",
        "gNBs[0].servingCellConfigCommon[0].ul_subcarrierSpacing",
        "gNBs[0].servingCellConfigCommon[0].prach_msg1_FDM",
        "gNBs[0].servingCellConfigCommon[0].restrictedSetConfig",
        "gNBs[0].servingCellConfigCommon[0].pucchGroupHopping",
        "log_config.global_log_level",
        "rfsimulator.modelname",
    ])
    # IP
    add([
        "MACRLCs[0].local_n_address",
        "MACRLCs[0].remote_n_address",
    ])
    # Arrays / timings
    add([
        "RUs[0].bands[0]",
        "fhi_72.fh_config[0].T1a_cp_dl[0]",
        "fhi_72.fh_config[0].T1a_cp_ul[0]",
        "fhi_72.fh_config[0].T1a_up[0]",
        "fhi_72.fh_config[0].Ta4[0]",
    ])

    return variants_catalog, keys


def classify_key(key: str) -> str:
    if any(s in key for s in ["local_n_address", "remote_n_address"]):
        return "ip"
    if any(s in key for s in ["bands[", "T1a_", "Ta4["]):
        return "array"
    if any(s in key for s in ["verbosity", "subcarrierSpacing", "prach_msg1_FDM", "restrictedSetConfig", "pucchGroupHopping", "modelname", "global_log_level"]):
        return "enum"
    return "numeric"


def apply_change(conf_text: str, modified_key: str, error_value: Any) -> str:
    # Handle nested array block pattern like plmn_list[0].mnc_length if needed (rare in DU set)
    if "[" in modified_key and "]" in modified_key and "." in modified_key.split("]")[-1]:
        block_name = modified_key.split("[")[0]
        index = int(modified_key.split("[")[-1].split("]")[0])
        subkey = modified_key.split("].")[-1]
        # Use concatenation to avoid f-string brace parsing issues
        pattern = r"(" + re.escape(block_name) + r"\s*=\s*\(\s*\{\s*.*?\}\s*\);)"
        matches = list(re.finditer(pattern, conf_text, flags=re.DOTALL))
        if not matches or index >= len(matches):
            return conf_text
        match = matches[index]
        block_text = match.group(1)
        sub_pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"
        def sub_replacer(m):
            if isinstance(error_value, str) and not error_value.startswith("0x"):
                new_val = f'"{error_value}"'
            else:
                new_val = str(error_value)
            return f"{m.group(1)}{new_val}{m.group(3)}"
        new_block, _ = re.subn(sub_pattern, sub_replacer, block_text)
        return conf_text[:match.start()] + new_block + conf_text[match.end():]

    # Handle array item like key[index]
    if "[" in modified_key and "]" in modified_key:
        key = modified_key.split(".")[-1].split("[")[0].strip()
        index = int(modified_key.split("[")[-1].split("]")[0])
        pattern = rf"({key}\s*=\s*\()(.*?)(\);)"
        def replacer(match):
            items = [v.strip() for v in match.group(2).split(",")]
            if 0 <= index < len(items):
                if isinstance(error_value, str) and not error_value.startswith("0x"):
                    new_val = f'"{error_value}"'
                else:
                    new_val = str(error_value)
                items[index] = new_val
                return f"{match.group(1)}{', '.join(items)}{match.group(3)}"
            return match.group(0)
        new_conf, _ = re.subn(pattern, replacer, conf_text, flags=re.DOTALL)
        return new_conf

    # Plain key = value;
    key = modified_key.split(".")[-1]
    pattern = rf"({key}\s*=\s*)([^;]+)(;)"
    if isinstance(error_value, str) and not error_value.startswith("0x"):
        formatted_value = f'"{error_value}"'
    else:
        formatted_value = str(error_value)
    def replacer(match):
        return f"{match.group(1)}{formatted_value}{match.group(3)}"
    new_conf, _ = re.subn(pattern, replacer, conf_text)
    return new_conf


def _clear_directory(dir_path: str) -> None:
    if os.path.isdir(dir_path):
        for name in os.listdir(dir_path):
            fp = os.path.join(dir_path, name)
            if os.path.isfile(fp) or os.path.islink(fp):
                os.remove(fp)
            elif os.path.isdir(fp):
                shutil.rmtree(fp)


def main() -> None:
    rebuild = "--rebuild" in sys.argv
    render_all = "--render-all" in sys.argv
    os.makedirs(JSON_DIR, exist_ok=True)
    os.makedirs(CONF_DIR, exist_ok=True)
    if rebuild:
        _clear_directory(JSON_DIR)
        _clear_directory(CONF_DIR)

    baseline = read_json(BASELINE_JSON_PATH)
    with open(BASELINE_CONF_PATH, "r", encoding="utf-8") as f:
        baseline_conf_text = f.read()

    cases: List[Dict[str, Any]]
    if not rebuild and os.path.exists(CASES_PATH):
        # Load existing cases and only render confs
        cases = read_json(CASES_PATH)
    else:
        variants_catalog, keys = build_catalog()
        target_total = 600
        cases = []
        i = 0
        while len(cases) < target_total:
            key = keys[i % len(keys)]
            group = classify_key(key)
            variants = variants_catalog[group]
            variant = variants[(i // len(keys)) % len(variants)]
            try:
                original_value = get_by_path(baseline, key)
            except Exception:
                i += 1
                continue
            filename = f"du_case_{len(cases) + 1:02d}.json"
            cases.append({
                "filename": filename,
                "modified_key": key,
                "original_value": original_value,
                "error_value": variant[0],
                "error_type": variant[1],
                "explanation_zh": variant[2],
            })
            i += 1

        # Write aggregate and per-case JSONs
        write_json(CASES_PATH, cases)
        for c in cases:
            write_json(os.path.join(JSON_DIR, c["filename"]), c)

    # Render confs
    render_cases = cases if render_all else cases[:400]
    for c in render_cases:
        conf_text = apply_change(baseline_conf_text, c["modified_key"], c["error_value"])
        out_conf = os.path.join(CONF_DIR, c["filename"].replace(".json", ".conf"))
        os.makedirs(os.path.dirname(out_conf), exist_ok=True)
        with open(out_conf, "w", encoding="utf-8") as f:
            f.write(conf_text)

    print(f"JSON cases available: {len(cases)} -> {JSON_DIR}")
    print(f"CONF files written: {len(os.listdir(CONF_DIR))} -> {CONF_DIR}")


if __name__ == "__main__":
    main()


