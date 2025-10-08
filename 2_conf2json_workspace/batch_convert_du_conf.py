#!/usr/bin/env python3
"""
Batch Converter for DU Configuration Files
Converts all .conf files from DU error_conf directory to JSON format
"""

import os
import sys
import glob
from pathlib import Path
import json
import re


def parse_conf_to_json(conf_file_path):
    """Parse a DU .conf file and convert it to JSON format"""
    
    with open(conf_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove comments and clean up
    lines = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            lines.append(line)
    
    # Join lines and parse
    text = ' '.join(lines)
    
    result = {}
    
    # Parse Active_gNBs (DU format uses parentheses instead of brackets)
    active_gnbs_match = re.search(r'Active_gNBs\s*=\s*\(\s*"([^"]*)"\s*\)', text)
    if active_gnbs_match:
        result['Active_gNBs'] = [active_gnbs_match.group(1)]
    
    # Parse Asn1_verbosity
    asn1_match = re.search(r'Asn1_verbosity\s*=\s*"([^"]*)"', text)
    if asn1_match:
        result['Asn1_verbosity'] = asn1_match.group(1)
    
    # Parse gNBs section (DU has more complex structure)
    gnbs_section = {}
    
    # gNB_ID
    gnb_id_match = re.search(r'gNB_ID\s*=\s*(0x[0-9a-fA-F]+|\d+)', text)
    if gnb_id_match:
        gnbs_section['gNB_ID'] = gnb_id_match.group(1)
    
    # gNB_DU_ID (DU specific)
    gnb_du_id_match = re.search(r'gNB_DU_ID\s*=\s*(0x[0-9a-fA-F]+|\d+)', text)
    if gnb_du_id_match:
        gnbs_section['gNB_DU_ID'] = gnb_du_id_match.group(1)
    
    # gNB_name
    gnb_name_match = re.search(r'gNB_name\s*=\s*"([^"]*)"', text)
    if gnb_name_match:
        gnbs_section['gNB_name'] = gnb_name_match.group(1)
    
    # tracking_area_code
    tac_match = re.search(r'tracking_area_code\s*=\s*(\d+)', text)
    if tac_match:
        gnbs_section['tracking_area_code'] = int(tac_match.group(1))
    
    # plmn_list (DU format with arrays) - use a more robust approach
    plmn_list_match = re.search(r'plmn_list\s*=\s*\(\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\)', text)
    if plmn_list_match:
        plmn_content = plmn_list_match.group(1)
        plmn_data = {}
        
        mcc_match = re.search(r'mcc\s*=\s*(\d+)', plmn_content)
        if mcc_match:
            plmn_data['mcc'] = int(mcc_match.group(1))
        
        mnc_match = re.search(r'mnc\s*=\s*(\d+)', plmn_content)
        if mnc_match:
            plmn_data['mnc'] = int(mnc_match.group(1))
        
        mnc_length_match = re.search(r'mnc_length\s*=\s*(\d+)', plmn_content)
        if mnc_length_match:
            plmn_data['mnc_length'] = int(mnc_length_match.group(1))
        
        # snssaiList (DU format with sd field) - extract from the full text
        snssai_match = re.search(r'snssaiList\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', text)
        if snssai_match:
            snssai_content = snssai_match.group(1)
            snssai_data = {}
            
            sst_match = re.search(r'sst\s*=\s*(\d+)', snssai_content)
            if sst_match:
                snssai_data['sst'] = int(sst_match.group(1))
            
            sd_match = re.search(r'sd\s*=\s*(0x[0-9a-fA-F]+|\d+)', snssai_content)
            if sd_match:
                snssai_data['sd'] = sd_match.group(1)
            
            plmn_data['snssaiList'] = [snssai_data]
        
        gnbs_section['plmn_list'] = [plmn_data]
    
    # nr_cellid
    nr_cellid_match = re.search(r'nr_cellid\s*=\s*(\d+)', text)
    if nr_cellid_match:
        gnbs_section['nr_cellid'] = int(nr_cellid_match.group(1))
    
    # Physical parameters (DU specific)
    physical_params = [
        'pdsch_AntennaPorts_XP', 'pdsch_AntennaPorts_N1', 'pusch_AntennaPorts',
        'do_CSIRS', 'maxMIMO_layers', 'do_SRS', 'min_rxtxtime', 'force_256qam_off', 'sib1_tda'
    ]
    
    for param in physical_params:
        match = re.search(f'{param}\\s*=\\s*(\\d+)', text)
        if match:
            gnbs_section[param] = int(match.group(1))
    
    # pdcch_ConfigSIB1
    pdcch_match = re.search(r'pdcch_ConfigSIB1\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', text)
    if pdcch_match:
        pdcch_content = pdcch_match.group(1)
        pdcch_data = {}
        
        control_resource_match = re.search(r'controlResourceSetZero\s*=\s*(\d+)', pdcch_content)
        if control_resource_match:
            pdcch_data['controlResourceSetZero'] = int(control_resource_match.group(1))
        
        search_space_match = re.search(r'searchSpaceZero\s*=\s*(\d+)', pdcch_content)
        if search_space_match:
            pdcch_data['searchSpaceZero'] = int(search_space_match.group(1))
        
        gnbs_section['pdcch_ConfigSIB1'] = [pdcch_data]
    
    # servingCellConfigCommon (complex nested structure)
    serving_cell_match = re.search(r'servingCellConfigCommon\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', text)
    if serving_cell_match:
        serving_cell_content = serving_cell_match.group(1)
        serving_cell_data = {}
        
        # Parse all the serving cell parameters
        serving_cell_params = [
            'physCellId', 'absoluteFrequencySSB', 'dl_frequencyBand', 'dl_absoluteFrequencyPointA',
            'dl_offstToCarrier', 'dl_subcarrierSpacing', 'dl_carrierBandwidth',
            'initialDLBWPlocationAndBandwidth', 'initialDLBWPsubcarrierSpacing',
            'initialDLBWPcontrolResourceSetZero', 'initialDLBWPsearchSpaceZero',
            'ul_frequencyBand', 'ul_offstToCarrier', 'ul_subcarrierSpacing', 'ul_carrierBandwidth',
            'pMax', 'initialULBWPlocationAndBandwidth', 'initialULBWPsubcarrierSpacing',
            'prach_ConfigurationIndex', 'prach_msg1_FDM', 'prach_msg1_FrequencyStart',
            'zeroCorrelationZoneConfig', 'preambleReceivedTargetPower', 'preambleTransMax',
            'powerRampingStep', 'ra_ResponseWindow', 'ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR',
            'ssb_perRACH_OccasionAndCB_PreamblesPerSSB', 'ra_ContentionResolutionTimer',
            'rsrp_ThresholdSSB', 'prach_RootSequenceIndex_PR', 'prach_RootSequenceIndex',
            'msg1_SubcarrierSpacing', 'restrictedSetConfig', 'msg3_DeltaPreamble',
            'p0_NominalWithGrant', 'pucchGroupHopping', 'hoppingId', 'p0_nominal',
            'ssb_PositionsInBurst_Bitmap', 'ssb_periodicityServingCell', 'dmrs_TypeA_Position',
            'subcarrierSpacing', 'referenceSubcarrierSpacing', 'dl_UL_TransmissionPeriodicity',
            'nrofDownlinkSlots', 'nrofDownlinkSymbols', 'nrofUplinkSlots', 'nrofUplinkSymbols',
            'ssPBCH_BlockPower'
        ]
        
        for param in serving_cell_params:
            match = re.search(f'{param}\\s*=\\s*(-?\\d+)', serving_cell_content)
            if match:
                serving_cell_data[param] = int(match.group(1))
        
        gnbs_section['servingCellConfigCommon'] = [serving_cell_data]
    
    # SCTP section
    sctp_data = {}
    sctp_instreams_match = re.search(r'SCTP_INSTREAMS\s*=\s*(\d+)', text)
    if sctp_instreams_match:
        sctp_data['SCTP_INSTREAMS'] = int(sctp_instreams_match.group(1))
    
    sctp_outstreams_match = re.search(r'SCTP_OUTSTREAMS\s*=\s*(\d+)', text)
    if sctp_outstreams_match:
        sctp_data['SCTP_OUTSTREAMS'] = int(sctp_outstreams_match.group(1))
    
    if sctp_data:
        gnbs_section['SCTP'] = sctp_data
    
    if gnbs_section:
        result['gNBs'] = [gnbs_section]
    
    # MACRLCs section
    macrlc_match = re.search(r'MACRLCs\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', text)
    if macrlc_match:
        macrlc_content = macrlc_match.group(1)
        macrlc_data = {}
        
        macrlc_params = ['num_cc', 'tr_s_preference', 'tr_n_preference', 'local_n_address', 
                        'remote_n_address', 'local_n_portc', 'local_n_portd', 'remote_n_portc', 'remote_n_portd']
        
        for param in macrlc_params:
            if param in ['tr_s_preference', 'tr_n_preference', 'local_n_address', 'remote_n_address']:
                match = re.search(f'{param}\\s*=\\s*"([^"]*)"', macrlc_content)
                if match:
                    macrlc_data[param] = match.group(1)
            else:
                match = re.search(f'{param}\\s*=\\s*(\\d+)', macrlc_content)
                if match:
                    macrlc_data[param] = int(match.group(1))
        
        result['MACRLCs'] = [macrlc_data]
    
    # L1s section
    l1_match = re.search(r'L1s\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', text)
    if l1_match:
        l1_content = l1_match.group(1)
        l1_data = {}
        
        l1_params = ['num_cc', 'tr_n_preference', 'prach_dtx_threshold', 'pucch0_dtx_threshold', 'ofdm_offset_divisor']
        
        for param in l1_params:
            if param == 'tr_n_preference':
                match = re.search(f'{param}\\s*=\\s*"([^"]*)"', l1_content)
                if match:
                    l1_data[param] = match.group(1)
            else:
                match = re.search(f'{param}\\s*=\\s*(\\d+)', l1_content)
                if match:
                    l1_data[param] = int(match.group(1))
        
        result['L1s'] = [l1_data]
    
    # RUs section
    ru_match = re.search(r'RUs\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', text)
    if ru_match:
        ru_content = ru_match.group(1)
        ru_data = {}
        
        # Parse RU parameters
        ru_params = ['local_rf', 'nb_tx', 'nb_rx', 'att_tx', 'att_rx', 'bands', 'max_pdschReferenceSignalPower',
                    'max_rxgain', 'sf_extension', 'eNB_instances', 'clock_src', 'ru_thread_core', 'sl_ahead', 'do_precoding']
        
        for param in ru_params:
            if param in ['local_rf', 'clock_src']:
                match = re.search(f'{param}\\s*=\\s*"([^"]*)"', ru_content)
                if match:
                    ru_data[param] = match.group(1)
            elif param == 'bands':
                match = re.search(r'bands\s*=\s*\[(\d+)\]', ru_content)
                if match:
                    ru_data[param] = [int(match.group(1))]
            elif param == 'eNB_instances':
                match = re.search(r'eNB_instances\s*=\s*\[(\d+)\]', ru_content)
                if match:
                    ru_data[param] = [int(match.group(1))]
            else:
                match = re.search(f'{param}\\s*=\\s*(-?\\d+)', ru_content)
                if match:
                    ru_data[param] = int(match.group(1))
        
        result['RUs'] = [ru_data]
    
    # rfsimulator section
    rfsim_match = re.search(r'rfsimulator:\s*\{\s*([^}]+)\s*\}', text)
    if rfsim_match:
        rfsim_content = rfsim_match.group(1)
        rfsim_data = {}
        
        rfsim_params = ['serveraddr', 'serverport', 'options', 'modelname', 'IQfile']
        
        for param in rfsim_params:
            if param == 'options':
                match = re.search(r'options\s*=\s*\(\s*\)', rfsim_content)
                if match:
                    rfsim_data[param] = []
            elif param == 'serverport':
                match = re.search(f'{param}\\s*=\\s*(\\d+)', rfsim_content)
                if match:
                    rfsim_data[param] = int(match.group(1))
            else:
                match = re.search(f'{param}\\s*=\\s*"([^"]*)"', rfsim_content)
                if match:
                    rfsim_data[param] = match.group(1)
        
        result['rfsimulator'] = rfsim_data
    
    # Log config section
    log_data = {}
    log_levels = ['global_log_level', 'hw_log_level', 'phy_log_level', 'mac_log_level']
    
    for log_level in log_levels:
        match = re.search(f'{log_level}\\s*=\\s*"([^"]*)"', text)
        if match:
            log_data[log_level] = match.group(1)
    
    if log_data:
        result['log_config'] = log_data
    
    # fhi_72 section
    fhi_match = re.search(r'fhi_72\s*=\s*\{\s*([^}]+)\s*\}', text)
    if fhi_match:
        fhi_content = fhi_match.group(1)
        fhi_data = {}
        
        # Parse fhi_72 parameters
        dpdk_match = re.search(r'dpdk_devices\s*=\s*\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)', fhi_content)
        if dpdk_match:
            fhi_data['dpdk_devices'] = [dpdk_match.group(1), dpdk_match.group(2)]
        
        ru_addr_match = re.search(r'ru_addr\s*=\s*\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)', fhi_content)
        if ru_addr_match:
            fhi_data['ru_addr'] = [ru_addr_match.group(1), ru_addr_match.group(2)]
        
        worker_cores_match = re.search(r'worker_cores\s*=\s*\(\s*(\d+)\s*\)', fhi_content)
        if worker_cores_match:
            fhi_data['worker_cores'] = [int(worker_cores_match.group(1))]
        
        # Parse other fhi_72 parameters
        fhi_params = ['system_core', 'io_core', 'mtu']
        for param in fhi_params:
            match = re.search(f'{param}\\s*=\\s*(\\d+)', fhi_content)
            if match:
                fhi_data[param] = int(match.group(1))
        
        # Parse fh_config (simplified)
        fh_config_match = re.search(r'fh_config\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)', fhi_content)
        if fh_config_match:
            fh_config_content = fh_config_match.group(1)
            fh_config_data = {}
            
            # Parse fh_config parameters (simplified)
            fh_config_params = ['T1a_cp_dl', 'T1a_cp_ul', 'T1a_up', 'Ta4']
            for param in fh_config_params:
                match = re.search(f'{param}\\s*=\\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', fh_config_content)
                if match:
                    fh_config_data[param] = [int(match.group(1)), int(match.group(2))]
            
            # Parse ru_config and prach_config (simplified)
            ru_config_match = re.search(r'ru_config\s*=\s*\{\s*([^}]+)\s*\}', fh_config_content)
            if ru_config_match:
                ru_config_content = ru_config_match.group(1)
                ru_config_data = {}
                iq_width_match = re.search(r'iq_width\s*=\\s*(\\d+)', ru_config_content)
                if iq_width_match:
                    ru_config_data['iq_width'] = int(iq_width_match.group(1))
                iq_width_prach_match = re.search(r'iq_width_prach\s*=\\s*(\\d+)', ru_config_content)
                if iq_width_prach_match:
                    ru_config_data['iq_width_prach'] = int(iq_width_prach_match.group(1))
                fh_config_data['ru_config'] = ru_config_data
            
            prach_config_match = re.search(r'prach_config\s*=\s*\{\s*([^}]+)\s*\}', fh_config_content)
            if prach_config_match:
                prach_config_content = prach_config_match.group(1)
                prach_config_data = {}
                kbar_match = re.search(r'kbar\s*=\\s*(\\d+)', prach_config_content)
                if kbar_match:
                    prach_config_data['kbar'] = int(kbar_match.group(1))
                fh_config_data['prach_config'] = prach_config_data
            
            fhi_data['fh_config'] = [fh_config_data]
        
        result['fhi_72'] = fhi_data
    
    return result


def batch_convert_du_conf():
    """Convert all DU .conf files to JSON format"""
    
    # Source and target directories
    source_dir = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\du_conf\error_conf"
    target_dir = r"C:\Users\bmwlab\Desktop\cursor_gen_conf\2_conf2json_workspace\du_conf2json"
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Get all .conf files from source directory
    conf_files = glob.glob(os.path.join(source_dir, "*.conf"))
    
    print(f"Found {len(conf_files)} .conf files to convert")
    print(f"Source directory: {source_dir}")
    print(f"Target directory: {target_dir}")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    error_files = []
    
    for i, conf_file in enumerate(conf_files, 1):
        try:
            # Get the filename without extension
            filename = os.path.basename(conf_file)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Create output JSON file path
            json_file = os.path.join(target_dir, f"{name_without_ext}.json")
            
            print(f"[{i:3d}/{len(conf_files)}] Converting {filename}...", end=" ")
            
            # Parse the configuration file
            config_data = parse_conf_to_json(conf_file)
            
            # Write to JSON file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print("Success")
            success_count += 1
            
        except Exception as e:
            print(f"Error: {e}")
            error_count += 1
            error_files.append((filename, str(e)))
    
    print("-" * 50)
    print(f"Conversion completed!")
    print(f"Successfully converted: {success_count} files")
    print(f"Failed conversions: {error_count} files")
    
    if error_files:
        print("\nError details:")
        for filename, error in error_files:
            print(f"  - {filename}: {error}")
    
    return success_count, error_count, error_files


def main():
    """Main function"""
    print("DU Configuration Batch Converter")
    print("=" * 50)
    
    try:
        success_count, error_count, error_files = batch_convert_du_conf()
        
        if error_count == 0:
            print("\nAll files converted successfully!")
            return 0
        else:
            print(f"\n{error_count} files failed to convert")
            return 1
            
    except Exception as e:
        print(f"\nBatch conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
