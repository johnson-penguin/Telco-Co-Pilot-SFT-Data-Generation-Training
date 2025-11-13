#!/usr/bin/env python3
import os
import re
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _strip_comments(text: str) -> str:
    # Remove // comments
    text = re.sub(r"//.*", "", text)
    # Remove # comments at end-of-line
    text = re.sub(r"#[^\n]*", "", text)
    return text


def _first_block(text: str, name: str) -> Optional[str]:
    # Locate the start of the named block and return balanced-brace body of the first object
    m = re.search(rf"{re.escape(name)}\s*(=|:)\s*", text)
    if not m:
        return None
    idx = m.end()
    # Skip optional parentheses wrapper
    while idx < len(text) and text[idx].isspace():
        idx += 1
    if idx < len(text) and text[idx] == '(':
        # advance to first '{' after parentheses start
        paren = 1
        idx += 1
        while idx < len(text) and paren > 0:
            if text[idx] == '(':
                paren += 1
            elif text[idx] == ')':
                paren -= 1
            if text[idx] == '{':
                break
            idx += 1
    # Move to first '{'
    while idx < len(text) and text[idx] != '{':
        idx += 1
    if idx >= len(text) or text[idx] != '{':
        return None
    # Extract balanced body inside this '{...}'
    start = idx + 1
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '"':
            # skip quoted strings
            i += 1
            while i < len(text):
                if text[i] == '"' and text[i-1] != '\\':
                    i += 1
                    break
                i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        i += 1
    end = i - 1
    if depth != 0 or end <= start:
        return None
    return text[start:end]


def _find_value(block: str, key: str) -> Optional[str]:
    # Match: key = value[;]? — stop at ';' or newline or '}'
    m = re.search(rf"{re.escape(key)}\s*=\s*([^;\n\r}}]+)", block)
    if not m:
        return None
    return m.group(1).strip()


def _find_tuple(block: str, key: str) -> Optional[List[str]]:
    # Match: key = (a, b, c) or key = [a, b]
    m = re.search(rf"{re.escape(key)}\s*=\s*\(([^\)]*)\)", block)
    if not m:
        m = re.search(rf"{re.escape(key)}\s*=\s*\[([^\]]*)\]", block)
        if not m:
            return None
    inside = m.group(1).strip()
    if not inside:
        return []
    return [item.strip().strip('"') for item in inside.split(',')]


def _to_int_or_str(raw: Optional[str]) -> Optional[Any]:
    if raw is None:
        return None
    s = raw.strip()
    # remove a possible trailing comma captured from lines like: key = 1,
    if s.endswith(','):
        s = s[:-1].strip()
    # Quoted string
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # Hex numbers
    if re.fullmatch(r"0x[0-9a-fA-F]+", s):
        return s
    # Integers
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            return s
    # Fallback
    return s.strip('"')


def parse_cu_gnb(gnb_block: str) -> Dict[str, Any]:
    # PLMN list
    plmn_m = re.search(r"plmn_list\s*=\s*\(\s*\{([\s\S]*?)\}\s*\)", gnb_block)
    plmn = None
    if plmn_m:
        plmn_block = plmn_m.group(1)
        # snssaiList inside plmn
        snssai_m = re.search(r"snssaiList\s*=\s*\(\s*\{([\s\S]*?)\}\s*\)", plmn_block)
        snssai_list = []
        if snssai_m:
            snssai_block = snssai_m.group(1)
            snssai_list.append(
                {"sst": _to_int_or_str(_find_value(snssai_block, "sst"))}
            )

        plmn = {
            "mcc": _to_int_or_str(_find_value(plmn_block, "mcc")),
            "mnc": _to_int_or_str(_find_value(plmn_block, "mnc")),
            "mnc_length": _to_int_or_str(_find_value(plmn_block, "mnc_length")),
            "snssaiList": snssai_list,
        }

    # SCTP
    sctp_block = _first_block(gnb_block, "SCTP")
    sctp = None
    if sctp_block:
        sctp = {
            "SCTP_INSTREAMS": _to_int_or_str(_find_value(sctp_block, "SCTP_INSTREAMS")),
            "SCTP_OUTSTREAMS": _to_int_or_str(_find_value(sctp_block, "SCTP_OUTSTREAMS")),
        }

    # AMF IP Address
    amf_ip_address = {}
    amf_m = re.search(r"amf_ip_address\s*=\s*\(\s*\{([\s\S]*?)\}\s*\)", gnb_block)
    if amf_m:
        amf_block = amf_m.group(1)
        amf_ip_address = {"ipv4": _to_int_or_str(_find_value(amf_block, "ipv4"))}

    # NETWORK_INTERFACES
    net_block = _first_block(gnb_block, "NETWORK_INTERFACES")
    network_interfaces = None
    if net_block:
        network_interfaces = {
            "GNB_IPV4_ADDRESS_FOR_NG_AMF": _to_int_or_str(_find_value(net_block, "GNB_IPV4_ADDRESS_FOR_NG_AMF")),
            "GNB_IPV4_ADDRESS_FOR_NGU": _to_int_or_str(_find_value(net_block, "GNB_IPV4_ADDRESS_FOR_NGU")),
            "GNB_PORT_FOR_S1U": _to_int_or_str(_find_value(net_block, "GNB_PORT_FOR_S1U")),
        }

    gnb_obj = {
        "gNB_ID": _to_int_or_str(_find_value(gnb_block, "gNB_ID")),
        "gNB_name": _to_int_or_str(_find_value(gnb_block, "gNB_name")),
        "tracking_area_code": _to_int_or_str(_find_value(gnb_block, "tracking_area_code")),
        "plmn_list": [plmn] if plmn else [],
        "nr_cellid": _to_int_or_str(_find_value(gnb_block, "nr_cellid")),
        "tr_s_preference": _to_int_or_str(_find_value(gnb_block, "tr_s_preference")),
        "local_s_if_name": _to_int_or_str(_find_value(gnb_block, "local_s_if_name")),
        "local_s_address": _to_int_or_str(_find_value(gnb_block, "local_s_address")),
        "remote_s_address": _to_int_or_str(_find_value(gnb_block, "remote_s_address")),
        "local_s_portc": _to_int_or_str(_find_value(gnb_block, "local_s_portc")),
        "local_s_portd": _to_int_or_str(_find_value(gnb_block, "local_s_portd")),
        "remote_s_portc": _to_int_or_str(_find_value(gnb_block, "remote_s_portc")),
        "remote_s_portd": _to_int_or_str(_find_value(gnb_block, "remote_s_portd")),
        "SCTP": sctp or {},
        "amf_ip_address": amf_ip_address or {},
        "NETWORK_INTERFACES": network_interfaces or {},
    }
    return gnb_obj


def parse_security(block: str) -> Dict[str, Any]:
    return {
        "ciphering_algorithms": _find_tuple(block, "ciphering_algorithms") or [],
        "integrity_algorithms": _find_tuple(block, "integrity_algorithms") or [],
        "drb_ciphering": _to_int_or_str(_find_value(block, "drb_ciphering")),
        "drb_integrity": _to_int_or_str(_find_value(block, "drb_integrity")),
    }


def parse_log_config(block: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    log_levels = [
        "global_log_level", "hw_log_level", "phy_log_level", "mac_log_level",
        "rlc_log_level", "pdcp_log_level", "rrc_log_level", "ngap_log_level", "f1ap_log_level"
    ]
    for key in log_levels:
        value = _to_int_or_str(_find_value(block, key))
        if value is not None:
            result[key] = value
    return result


def parse_conf_to_json(conf_text: str) -> Dict[str, Any]:
    text = _strip_comments(conf_text)

    # Top-level simple keys
    active_gnbs_tuple = _find_tuple(text, "Active_gNBs") or []
    asn1_verbosity = _to_int_or_str(_find_value(text, "Asn1_verbosity"))
    num_threads_pusch = _to_int_or_str(_find_value(text, "Num_Threads_PUSCH"))

    # Blocks
    gnbs_outer = _first_block(text, "gNBs") or ""
    security_outer = _first_block(text, "security") or ""
    logcfg_outer = _first_block(text, "log_config") or ""

    result: Dict[str, Any] = {
        "Active_gNBs": active_gnbs_tuple,
        "Asn1_verbosity": asn1_verbosity,
        "Num_Threads_PUSCH": num_threads_pusch,
        "gNBs": [],
        "security": {},
        "log_config": {},
    }

    if gnbs_outer:
        result["gNBs"].append(parse_cu_gnb(gnbs_outer))
    if security_outer:
        result["security"] = parse_security(security_outer)
    if logcfg_outer:
        result["log_config"] = parse_log_config(logcfg_outer)

    return result


def convert_file(input_path: str, output_path: str) -> None:
    print(f"Converting: {input_path} -> {output_path}")
    conf_text = read_text(input_path)
    data = parse_conf_to_json(conf_text)
    write_json(output_path, data)
    print(f"Successfully converted {os.path.basename(input_path)}.")


def main() -> None:
    BASE_DIR = Path(__file__).resolve().parent
    # 專案根目錄：從 BASE_DIR 往上退兩層
    # C:\Users\wasd0\Desktop\Telco-Co-Pilot-SFT-Data-Generation-Training\1_confgen_workspace\1_to_2_cu_conf_to_json.py
    PROJECT_ROOT = BASE_DIR.parent
    # print("--------------------------------")
    # print(f"BASE_DIR: {BASE_DIR}")
    # print("--------------------------------")


    DEFAULT_INPUT = PROJECT_ROOT / "1_confgen_workspace" / "1_conf" / "cu_conf_1001_200" / "error_conf"
    DEFAULT_OUTPUT = PROJECT_ROOT / "1_confgen_workspace" / "2_json" / "cu_conf_1001_200_json"

    parser = argparse.ArgumentParser(description="Convert CU .conf to JSON matching baseline structure")
    parser.add_argument("--input", help="Input .conf file or directory", required=False, default=DEFAULT_INPUT)
    parser.add_argument("--output", help="Output .json file or directory", required=False, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    # Fallback to workspace-relative paths if absolute defaults are not present
    # Adjust relative paths for a typical CU setup
    if not os.path.exists(args.input):
        print(f"Warning: Default input path not found: {args.input}")
        rel_input = os.path.join("1_confgen_workspace", "1_conf", "cu_conf_default", "conf")
        if os.path.exists(rel_input):
            print(f"Falling back to relative path: {rel_input}")
            args.input = rel_input
        else:
            print(f"Error: Could not find fallback path either: {rel_input}")
            return

    if os.path.isdir(args.input):
        in_dir = args.input
        out_dir = args.output
        os.makedirs(out_dir, exist_ok=True)
        print(f"Processing directory: {in_dir} -> {out_dir}")
        for name in sorted(os.listdir(in_dir)):
            if not name.endswith(".conf"):
                continue
            in_path = os.path.join(in_dir, name)
            out_name = os.path.splitext(name)[0] + ".json"
            out_path = os.path.join(out_dir, out_name)
            convert_file(in_path, out_path)
        print("\nDirectory processing complete.")
        return

    # Single file
    convert_file(args.input, args.output)
    print("\nFile conversion complete.")


if __name__ == "__main__":
    main()