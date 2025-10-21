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
                # don't break; we want first '{' within too
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
    # Hex numbers should often be represented as strings for IDs/SD
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


def _to_int_list(items: List[str]) -> List[int]:
    result: List[int] = []
    for token in items:
        t = token.strip().strip('"').strip()
        if not t:
            continue
        # remove trailing commas if any
        if t.endswith(','):
            t = t[:-1].strip()
        if re.fullmatch(r"-?\d+", t):
            try:
                result.append(int(t))
            except ValueError:
                continue
    return result


def parse_gnbs(gnb_block: str) -> Dict[str, Any]:
    # gNB_ID, gNB_DU_ID as strings (hex in config)
    gnb_id = _find_value(gnb_block, "gNB_ID")
    gnb_du_id = _find_value(gnb_block, "gNB_DU_ID")
    gnb_name = _find_value(gnb_block, "gNB_name")
    tracking_area_code = _to_int_or_str(_find_value(gnb_block, "tracking_area_code"))
    nr_cellid = _to_int_or_str(_find_value(gnb_block, "nr_cellid"))
    pdsch_XP = _to_int_or_str(_find_value(gnb_block, "pdsch_AntennaPorts_XP"))
    pdsch_N1 = _to_int_or_str(_find_value(gnb_block, "pdsch_AntennaPorts_N1"))
    pusch_ports = _to_int_or_str(_find_value(gnb_block, "pusch_AntennaPorts"))
    do_csirs = _to_int_or_str(_find_value(gnb_block, "do_CSIRS"))
    max_mimo_layers = _to_int_or_str(_find_value(gnb_block, "maxMIMO_layers"))
    do_srs = _to_int_or_str(_find_value(gnb_block, "do_SRS"))
    min_rxtxtime = _to_int_or_str(_find_value(gnb_block, "min_rxtxtime"))
    force_256qam_off = _to_int_or_str(_find_value(gnb_block, "force_256qam_off"))
    sib1_tda = _to_int_or_str(_find_value(gnb_block, "sib1_tda"))

    # pdcch_ConfigSIB1
    pdcch_block = _first_block(gnb_block, "pdcch_ConfigSIB1")
    pdcch = None
    if pdcch_block:
        pdcch = {
            "controlResourceSetZero": _to_int_or_str(_find_value(pdcch_block, "controlResourceSetZero")),
            "searchSpaceZero": _to_int_or_str(_find_value(pdcch_block, "searchSpaceZero")),
        }

    # servingCellConfigCommon (single object in list)
    sccc_block = _first_block(gnb_block, "servingCellConfigCommon")
    sccc = None
    if sccc_block:
        sccc = {
            "physCellId": _to_int_or_str(_find_value(sccc_block, "physCellId")),
            "absoluteFrequencySSB": _to_int_or_str(_find_value(sccc_block, "absoluteFrequencySSB")),
            "dl_frequencyBand": _to_int_or_str(_find_value(sccc_block, "dl_frequencyBand")),
            "dl_absoluteFrequencyPointA": _to_int_or_str(_find_value(sccc_block, "dl_absoluteFrequencyPointA")),
            "dl_offstToCarrier": _to_int_or_str(_find_value(sccc_block, "dl_offstToCarrier")),
            "dl_subcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "dl_subcarrierSpacing")),
            "dl_carrierBandwidth": _to_int_or_str(_find_value(sccc_block, "dl_carrierBandwidth")),
            "initialDLBWPlocationAndBandwidth": _to_int_or_str(_find_value(sccc_block, "initialDLBWPlocationAndBandwidth")),
            "initialDLBWPsubcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "initialDLBWPsubcarrierSpacing")),
            "initialDLBWPcontrolResourceSetZero": _to_int_or_str(_find_value(sccc_block, "initialDLBWPcontrolResourceSetZero")),
            "initialDLBWPsearchSpaceZero": _to_int_or_str(_find_value(sccc_block, "initialDLBWPsearchSpaceZero")),
            "ul_frequencyBand": _to_int_or_str(_find_value(sccc_block, "ul_frequencyBand")),
            "ul_offstToCarrier": _to_int_or_str(_find_value(sccc_block, "ul_offstToCarrier")),
            "ul_subcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "ul_subcarrierSpacing")),
            "ul_carrierBandwidth": _to_int_or_str(_find_value(sccc_block, "ul_carrierBandwidth")),
            "pMax": _to_int_or_str(_find_value(sccc_block, "pMax")),
            "initialULBWPlocationAndBandwidth": _to_int_or_str(_find_value(sccc_block, "initialULBWPlocationAndBandwidth")),
            "initialULBWPsubcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "initialULBWPsubcarrierSpacing")),
            "prach_ConfigurationIndex": _to_int_or_str(_find_value(sccc_block, "prach_ConfigurationIndex")),
            "prach_msg1_FDM": _to_int_or_str(_find_value(sccc_block, "prach_msg1_FDM")),
            "prach_msg1_FrequencyStart": _to_int_or_str(_find_value(sccc_block, "prach_msg1_FrequencyStart")),
            "zeroCorrelationZoneConfig": _to_int_or_str(_find_value(sccc_block, "zeroCorrelationZoneConfig")),
            "preambleReceivedTargetPower": _to_int_or_str(_find_value(sccc_block, "preambleReceivedTargetPower")),
            "preambleTransMax": _to_int_or_str(_find_value(sccc_block, "preambleTransMax")),
            "powerRampingStep": _to_int_or_str(_find_value(sccc_block, "powerRampingStep")),
            "ra_ResponseWindow": _to_int_or_str(_find_value(sccc_block, "ra_ResponseWindow")),
            "ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR": _to_int_or_str(_find_value(sccc_block, "ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR")),
            "ssb_perRACH_OccasionAndCB_PreamblesPerSSB": _to_int_or_str(_find_value(sccc_block, "ssb_perRACH_OccasionAndCB_PreamblesPerSSB")),
            "ra_ContentionResolutionTimer": _to_int_or_str(_find_value(sccc_block, "ra_ContentionResolutionTimer")),
            "rsrp_ThresholdSSB": _to_int_or_str(_find_value(sccc_block, "rsrp_ThresholdSSB")),
            "prach_RootSequenceIndex_PR": _to_int_or_str(_find_value(sccc_block, "prach_RootSequenceIndex_PR")),
            "prach_RootSequenceIndex": _to_int_or_str(_find_value(sccc_block, "prach_RootSequenceIndex")),
            "msg1_SubcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "msg1_SubcarrierSpacing")),
            "restrictedSetConfig": _to_int_or_str(_find_value(sccc_block, "restrictedSetConfig")),
            "msg3_DeltaPreamble": _to_int_or_str(_find_value(sccc_block, "msg3_DeltaPreamble")),
            "p0_NominalWithGrant": _to_int_or_str(_find_value(sccc_block, "p0_NominalWithGrant")),
            "pucchGroupHopping": _to_int_or_str(_find_value(sccc_block, "pucchGroupHopping")),
            "hoppingId": _to_int_or_str(_find_value(sccc_block, "hoppingId")),
            "p0_nominal": _to_int_or_str(_find_value(sccc_block, "p0_nominal")),
            "ssb_PositionsInBurst_Bitmap": _to_int_or_str(_find_value(sccc_block, "ssb_PositionsInBurst_Bitmap")),
            "ssb_periodicityServingCell": _to_int_or_str(_find_value(sccc_block, "ssb_periodicityServingCell")),
            "dmrs_TypeA_Position": _to_int_or_str(_find_value(sccc_block, "dmrs_TypeA_Position")),
            "subcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "subcarrierSpacing")),
            "referenceSubcarrierSpacing": _to_int_or_str(_find_value(sccc_block, "referenceSubcarrierSpacing")),
            "dl_UL_TransmissionPeriodicity": _to_int_or_str(_find_value(sccc_block, "dl_UL_TransmissionPeriodicity")),
            "nrofDownlinkSlots": _to_int_or_str(_find_value(sccc_block, "nrofDownlinkSlots")),
            "nrofDownlinkSymbols": _to_int_or_str(_find_value(sccc_block, "nrofDownlinkSymbols")),
            "nrofUplinkSlots": _to_int_or_str(_find_value(sccc_block, "nrofUplinkSlots")),
            "nrofUplinkSymbols": _to_int_or_str(_find_value(sccc_block, "nrofUplinkSymbols")),
            "ssPBCH_BlockPower": _to_int_or_str(_find_value(sccc_block, "ssPBCH_BlockPower")),
        }

    # PLMN list (first entry only as baseline)
    plmn_m = re.search(r"plmn_list\s*=\s*\(\s*\{([\s\S]*?)\}\s*\)\s*;", gnb_block)
    plmn = None
    if plmn_m:
        plmn_block = plmn_m.group(1)
        plmn = {
            "mcc": _to_int_or_str(_find_value(plmn_block, "mcc")),
            "mnc": _to_int_or_str(_find_value(plmn_block, "mnc")),
            "mnc_length": _to_int_or_str(_find_value(plmn_block, "mnc_length")),
            "snssaiList": [
                {
                    "sst": _to_int_or_str(_find_value(plmn_block, "sst")),
                    "sd": _to_int_or_str(_find_value(plmn_block, "sd")),
                }
            ],
        }

    # SCTP
    sctp_block = _first_block(gnb_block, "SCTP")
    sctp = None
    if sctp_block:
        sctp = {
            "SCTP_INSTREAMS": _to_int_or_str(_find_value(sctp_block, "SCTP_INSTREAMS")),
            "SCTP_OUTSTREAMS": _to_int_or_str(_find_value(sctp_block, "SCTP_OUTSTREAMS")),
        }

    gnb_obj = {
        "gNB_ID": _to_int_or_str(gnb_id),
        "gNB_DU_ID": _to_int_or_str(gnb_du_id),
        "gNB_name": _to_int_or_str(gnb_name),
        "tracking_area_code": tracking_area_code,
        "plmn_list": [plmn] if plmn else [],
        "nr_cellid": nr_cellid,
        "pdsch_AntennaPorts_XP": pdsch_XP,
        "pdsch_AntennaPorts_N1": pdsch_N1,
        "pusch_AntennaPorts": pusch_ports,
        "do_CSIRS": do_csirs,
        "maxMIMO_layers": max_mimo_layers,
        "do_SRS": do_srs,
        "min_rxtxtime": min_rxtxtime,
        "force_256qam_off": force_256qam_off,
        "sib1_tda": sib1_tda,
        "pdcch_ConfigSIB1": [pdcch] if pdcch else [],
        "servingCellConfigCommon": [sccc] if sccc else [],
        "SCTP": sctp or {},
    }
    return gnb_obj


def parse_macrlc(block: str) -> Dict[str, Any]:
    return {
        "num_cc": _to_int_or_str(_find_value(block, "num_cc")),
        "tr_s_preference": _to_int_or_str(_find_value(block, "tr_s_preference")),
        "tr_n_preference": _to_int_or_str(_find_value(block, "tr_n_preference")),
        "local_n_address": _to_int_or_str(_find_value(block, "local_n_address")),
        "remote_n_address": _to_int_or_str(_find_value(block, "remote_n_address")),
        "local_n_portc": _to_int_or_str(_find_value(block, "local_n_portc")),
        "local_n_portd": _to_int_or_str(_find_value(block, "local_n_portd")),
        "remote_n_portc": _to_int_or_str(_find_value(block, "remote_n_portc")),
        "remote_n_portd": _to_int_or_str(_find_value(block, "remote_n_portd")),
    }


def parse_l1s(block: str) -> Dict[str, Any]:
    return {
        "num_cc": _to_int_or_str(_find_value(block, "num_cc")),
        "tr_n_preference": _to_int_or_str(_find_value(block, "tr_n_preference")),
        "prach_dtx_threshold": _to_int_or_str(_find_value(block, "prach_dtx_threshold")),
        "pucch0_dtx_threshold": _to_int_or_str(_find_value(block, "pucch0_dtx_threshold")),
        "ofdm_offset_divisor": _to_int_or_str(_find_value(block, "ofdm_offset_divisor")),
    }


def parse_rus(block: str) -> Dict[str, Any]:
    bands = _find_tuple(block, "bands") or []
    worker = {
        "local_rf": _to_int_or_str(_find_value(block, "local_rf")),
        "nb_tx": _to_int_or_str(_find_value(block, "nb_tx")),
        "nb_rx": _to_int_or_str(_find_value(block, "nb_rx")),
        "att_tx": _to_int_or_str(_find_value(block, "att_tx")),
        "att_rx": _to_int_or_str(_find_value(block, "att_rx")),
        "bands": [int(x) if x.isdigit() else x for x in bands],
        "max_pdschReferenceSignalPower": _to_int_or_str(_find_value(block, "max_pdschReferenceSignalPower")),
        "max_rxgain": _to_int_or_str(_find_value(block, "max_rxgain")),
        "sf_extension": _to_int_or_str(_find_value(block, "sf_extension")),
        "eNB_instances": [
            int(x) if x.isdigit() else x for x in (_find_tuple(block, "eNB_instances") or [])
        ],
        "clock_src": _to_int_or_str(_find_value(block, "clock_src")),
        "ru_thread_core": _to_int_or_str(_find_value(block, "ru_thread_core")),
        "sl_ahead": _to_int_or_str(_find_value(block, "sl_ahead")),
        "do_precoding": _to_int_or_str(_find_value(block, "do_precoding")),
    }
    return worker


def parse_rfsimulator(block: str) -> Dict[str, Any]:
    options = _find_tuple(block, "options") or []
    return {
        "serveraddr": _to_int_or_str(_find_value(block, "serveraddr")),
        "serverport": _to_int_or_str(_find_value(block, "serverport")),
        "options": options,
        "modelname": _to_int_or_str(_find_value(block, "modelname")),
        "IQfile": _to_int_or_str(_find_value(block, "IQfile")),
    }


def parse_log_config(block: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for k in [
        "global_log_level",
        "hw_log_level",
        "phy_log_level",
        "mac_log_level",
    ]:
        v = _to_int_or_str(_find_value(block, k))
        if v is not None:
            result[k] = v
    return result


def parse_fhi72(block: str) -> Dict[str, Any]:
    dpdk_devices = _find_tuple(block, "dpdk_devices") or []
    worker_cores = _find_tuple(block, "worker_cores") or []
    ru_addr = _find_tuple(block, "ru_addr") or []
    fh_conf_block = _first_block(block, "fh_config")

    fh_item: Optional[Dict[str, Any]] = None
    if fh_conf_block:
        fh_item = {
            "T1a_cp_dl": _to_int_list(_find_tuple(fh_conf_block, "T1a_cp_dl") or []),
            "T1a_cp_ul": _to_int_list(_find_tuple(fh_conf_block, "T1a_cp_ul") or []),
            "T1a_up": _to_int_list(_find_tuple(fh_conf_block, "T1a_up") or []),
            "Ta4": _to_int_list(_find_tuple(fh_conf_block, "Ta4") or []),
            "ru_config": {
                "iq_width": _to_int_or_str(_find_value(fh_conf_block, "iq_width")),
                "iq_width_prach": _to_int_or_str(_find_value(fh_conf_block, "iq_width_prach")),
            },
            "prach_config": {
                "kbar": _to_int_or_str(_find_value(fh_conf_block, "kbar")),
            },
        }

    return {
        "dpdk_devices": dpdk_devices,
        "system_core": _to_int_or_str(_find_value(block, "system_core")),
        "io_core": _to_int_or_str(_find_value(block, "io_core")),
        "worker_cores": [int(x) if str(x).isdigit() else x for x in worker_cores],
        "ru_addr": ru_addr,
        "mtu": _to_int_or_str(_find_value(block, "mtu")),
        "fh_config": [fh_item] if fh_item else [],
    }


def parse_conf_to_json(conf_text: str) -> Dict[str, Any]:
    text = _strip_comments(conf_text)

    # Top-level simple keys
    active_gnbs_tuple = _find_tuple(text, "Active_gNBs") or []
    asn1_verbosity = _to_int_or_str(_find_value(text, "Asn1_verbosity"))

    # Blocks
    gnbs_outer = _first_block(text, "gNBs") or ""
    macrlc_outer = _first_block(text, "MACRLCs") or ""
    l1s_outer = _first_block(text, "L1s") or ""
    rus_outer = _first_block(text, "RUs") or ""
    rfsim_outer = _first_block(text, "rfsimulator") or ""
    logcfg_outer = _first_block(text, "log_config") or ""
    fhi_outer = _first_block(text, "fhi_72") or ""

    result: Dict[str, Any] = {
        "Active_gNBs": active_gnbs_tuple,
        "Asn1_verbosity": asn1_verbosity,
        "gNBs": [],
        "MACRLCs": [],
        "L1s": [],
        "RUs": [],
        "rfsimulator": {},
        "log_config": {},
        "fhi_72": {},
    }

    if gnbs_outer:
        result["gNBs"].append(parse_gnbs(gnbs_outer))
    if macrlc_outer:
        result["MACRLCs"].append(parse_macrlc(macrlc_outer))
    if l1s_outer:
        result["L1s"].append(parse_l1s(l1s_outer))
    if rus_outer:
        result["RUs"].append(parse_rus(rus_outer))
    if rfsim_outer:
        result["rfsimulator"] = parse_rfsimulator(rfsim_outer)
    if logcfg_outer:
        result["log_config"] = parse_log_config(logcfg_outer)
    if fhi_outer:
        result["fhi_72"] = parse_fhi72(fhi_outer)

    return result


def convert_file(input_path: str, output_path: str) -> None:
    print(f"Converting: {input_path} -> {output_path}")
    conf_text = read_text(input_path)
    data = parse_conf_to_json(conf_text)
    write_json(output_path, data)
    print(f"Successfully converted {os.path.basename(input_path)}.")


def main() -> None:
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent
    # print("--------------------------------")
    # print(f"BASE_DIR: {BASE_DIR}")
    # print("--------------------------------")

    DEFAULT_INPUT = PROJECT_ROOT / "1_confgen_workspace" / "1_conf" / "du_conf_1001_200" / "error_conf"
    DEFAULT_OUTPUT = PROJECT_ROOT / "1_confgen_workspace" / "2_json" / "du_conf_1001_200_json"

    parser = argparse.ArgumentParser(description="Convert DU .conf to JSON matching baseline structure")
    parser.add_argument("--input", help="Input .conf file or directory", required=False, default=DEFAULT_INPUT)
    parser.add_argument("--output", help="Output .json file or directory", required=False, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    # Fallback to workspace-relative paths if absolute defaults are not present
    if not os.path.exists(args.input):
        print(f"Warning: Default input path not found: {args.input}")
        rel_input = os.path.join("1_confgen_workspace", "1_conf", "du_conf_default", "conf")
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


