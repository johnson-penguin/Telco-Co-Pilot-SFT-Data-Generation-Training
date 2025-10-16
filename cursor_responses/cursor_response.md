Generated 500 CU delta error cases at `1_confgen_workspace/1_conf/cu_conf_1014_600/json/cases_delta.json` based on baseline `0_required_inputs/baseline_conf_json/cu_gnb.json`, modifying `gNBs.remote_s_address` (original `127.0.0.3`) to test-net/unroutable IPs. Structure mirrors DU `cases_delta.json` with fields: filename, modified_key, original_value, error_value, error_type, explanation.
Generated 500 erroneous CU conf files into `1_confgen_workspace/1_conf/cu_conf_1014_600` based on `0_required_inputs/baseline_conf_json/cu_gnb.json` and referenced DU cases at `1_confgen_workspace/1_conf/du_conf_1014_2_1000/json/cases_delta.json`.

2025-10-14: min_rxtxtime replacement fix

- Issue: `gNBs[0].min_rxtxtime` not replaced due to inner `);` prematurely ending block match.
- Fixes:
  - Added balanced-parentheses `_find_block_span` to capture full `gNBs = ( ... );`.
  - If subkey still not found in targeted block, fallback to a global `key = value;` replacement with the same bilingual comment.
- Result: `min_rxtxtime` now updates; warnings downgraded to informative with fallback.

2025-10-14: DU generator warning suppression for missing subkey with global fallback

- Issue: `[WARN] 子參數 'min_rxtxtime' 未在 gNBs[0] 中找到 ...` printed even when a global key match exists.
- Fixes in `1_confgen_workspace/tool/du_generate_error_confs.py`:
  - In `gNBs[0].servingCellConfigCommon[0].<subkey>` handler, added quiet global fallback to `<key> = ...;` when inner subkey not found; warn only if no global match.
  - In generic `block[index].subkey` handler, removed warning on fallback; now warn only when neither block nor global matches exist.
- Outcome: No warning emitted when a successful global fallback updates the value (e.g., `min_rxtxtime`).

---

2025-10-14: du_generate_error_confs.py – Functionality Overview (no edits made)

- Purpose: Generate erroneous DU `.conf` files from a baseline `du_gnb.conf` using a cases JSON (e.g., `cases_delta.json`), and annotate each modified line with bilingual comments.
- Defaults:
  - `--baseline`: `1_confgen_workspace/../0_required_inputs/baseline_conf/du_gnb.conf`
  - `--cases`: `1_confgen_workspace/1_conf/du_conf_1014_2_1000/json/cases_delta.json`
  - `--output`: `1_confgen_workspace/1_conf/du_conf_1014_2_1000/conf`
- CLI:
  ```bash
  python 1_confgen_workspace/tool/du_generate_error_confs.py \
    --baseline 0_required_inputs/baseline_conf/du_gnb.conf \
    --cases 1_confgen_workspace/1_conf/du_conf_1014_800/json/cases_delta.json \
    --output 1_confgen_workspace/1_conf/du_conf_1014_800/conf
  ```
- Core flow:
  1) Read baseline conf and the cases array from JSON. 2) For each case `{filename, modified_key, error_value, original_value?}`, apply a targeted replacement to the baseline text. 3) Write the resulting `.conf` to the output directory and print a short summary.
- Replacement logic (`replace_key_value`):
  - Special handling for nested keys flattened in the conf:
    - `gNBs[0].servingCellConfigCommon[0].<subkey>` → replace `<subkey> = ...;` in the `servingCellConfigCommon` area.
    - `fhi_72.fh_config[0].<subkey>` → replace `<subkey> = ...;` inside `fhi_72.fh_config`.
  - Block element subkeys like `blockName[index].subkey` (e.g., `plmn_list[0].mnc_length`): find the Nth occurrence of the block and update the subkey value.
  - Indexed arrays like `key[index]`: update the indexed element inside `key = ( ... );`.
  - Fallback: plain `key = value;` assignment.
  - Strings are quoted unless they look like hex (start with `0x`). Each change appends a bilingual comment indicating the original and error values.
- Warnings: If a targeted block/subkey is not found or an index is out of range, a warning is printed and the baseline text is left unchanged for that case.
- Output: One `.conf` per case (filename derived from case JSON), placed in the `--output` directory.

Key references:
```20:44:1_confgen_workspace/tool/du_generate_error_confs.py
def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """
    根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解
    支援:
      - 普通 key = value;
      - 陣列元素 key[index]
      - 巢狀結構 key[index].subkey
      - 特殊處理: gNBs[0].servingCellConfigCommon[0].subkey -> servingCellConfigCommon.subkey
      - 特殊處理: fhi_72.fh_config[0].subkey -> fhi_72.fh_config.subkey
    """
```
```144:149:1_confgen_workspace/tool/du_generate_error_confs.py
def parse_args():
    parser = argparse.ArgumentParser(description="Generate erroneous DU conf files from baseline using cases JSON")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE_CONF, help="Path to baseline du_gnb.conf")
    parser.add_argument("--cases", default=DEFAULT_ERROR_CASES_JSON, help="Path to error cases JSON (cases_delta.json)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory to write generated .conf files")
    return parser.parse_args()
```
```152:183:1_confgen_workspace/tool/du_generate_error_confs.py
def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline_text = f.read()
    with open(args.cases, "r", encoding="utf-8") as f:
        cases = json.load(f)
    for case in cases:
        filename = case["filename"].replace(".json", ".conf")
        modified_key = case["modified_key"]
        error_value = case["error_value"]
        original_value = case.get("original_value", None)
        new_conf = replace_key_value(baseline_text, modified_key, error_value, original_value)
        output_path = os.path.join(args.output, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_conf)
        print(f"[OK] {filename} 已生成 / Generated")
        print(f"   參數修改: {modified_key} → {error_value}")
        print(f"   Parameter modified: {modified_key} → {error_value}")
        print("-" * 60)
```

What I did:
- Added `1_confgen_workspace/tool/cu_generate_error_confs_1014_600.py` to synthesize CU error cases using CU-relevant keys and DU error values.
- Fixed regex and path issues; ensured no overwrite by uniquifying filenames.
- Ran the generator and confirmed `Total generated: 500` and files exist `cu_case_0001.conf` ... `cu_case_0500.conf`.

Notes:
- Values are intentionally erroneous (e.g., using random IP-like strings for various fields) to create failure scenarios.
- If you need different error distributions or to target a subset of keys, specify and I can adjust the generator.
Updated filenames in DU 1014_2 cases:
- "du2_case_003.json" -> "du_case_003.json"
- "du2_case_005.json" -> "du_case_005.json"
Generated 500 DU cases (non-overlapping with 1014_800) focusing on:
- IP range conflicts (overlapping subnets)
- Frequency misalignment (SSB/PRACH/UL-DL mismatches)
- Timing misalignment (T1a/Ta4/min_rxtxtime/ofdm_offset)
- Unreachable routing (remote_n_address to non-routable ranges)

Output written to:
`C:\Users\bmwlab\Desktop\cursor_gen_conf\1_confgen_workspace\1_conf\du_conf_1014_2\json\cases_delta.json`

Method: Parsed baseline `du_gnb.json`, ensured uniqueness versus `du_conf_1014_800/json/cases_delta.json`, and deterministically synthesized 500 entries.
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


---

2025-10-14: Display file `0_required_inputs/baseline_conf/du_gnb.conf`

```conf
Active_gNBs = ( "gNB-Eurecom-DU");
# Asn1_verbosity, choice in: none, info, annoying
Asn1_verbosity = "annoying";

gNBs =
(
 {
    ////////// Identification parameters:
    gNB_ID = 0xe00;
    gNB_DU_ID = 0xe00;

#     cell_type =  "CELL_MACRO_GNB";

    gNB_name  =  "gNB-Eurecom-DU";

    // Tracking area code, 0x0000 and 0xfffe are reserved values
    tracking_area_code  =  1;
    plmn_list = ({ 
                mcc = 001; 
                mnc = 01; 
                mnc_length = 2; 
                snssaiList = ( 
                  { 
                  sst = 1;
                  sd = 0x010203;
                  }
                  )
                });
    nr_cellid = 1;

    ////////// Physical parameters:
    pdsch_AntennaPorts_XP = 2; 
    pdsch_AntennaPorts_N1 = 2; 
    pusch_AntennaPorts    = 4; 
    do_CSIRS              = 0;
    maxMIMO_layers        = 1;
    do_SRS                = 0;
    min_rxtxtime                                              = 6;
    force_256qam_off = 1;
    sib1_tda			  = 15;

    pdcch_ConfigSIB1 = (
      {
        controlResourceSetZero = 11;
        searchSpaceZero = 0;
      }
    );

    servingCellConfigCommon = (
    {
 #spCellConfigCommon

      physCellId                                                    = 0;

#  downlinkConfigCommon
    #frequencyInfoDL
      # this is 3600 MHz + 43 PRBs@30kHz SCS (same as initial BWP)
      absoluteFrequencySSB                                          = 641280;
      dl_frequencyBand                                                 = 78;
      # this is 3600 MHz
      dl_absoluteFrequencyPointA                                       = 640008;
      #scs-SpecificCarrierList
        dl_offstToCarrier                                              = 0;
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120  
        dl_subcarrierSpacing                                           = 1;
        dl_carrierBandwidth                                            = 106;
     #initialDownlinkBWP
      #genericParameters
        # this is RBstart=27,L=48 (275*(L-1))+RBstart
        initialDLBWPlocationAndBandwidth                               = 28875; # 6366 12925 12956 28875 12952
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120  
        initialDLBWPsubcarrierSpacing                                           = 1;
      #pdcch-ConfigCommon
        initialDLBWPcontrolResourceSetZero                              = 12;
        initialDLBWPsearchSpaceZero                                      = 0;

  #uplinkConfigCommon 
     #frequencyInfoUL
      ul_frequencyBand                                                 = 78;
      #scs-SpecificCarrierList
      ul_offstToCarrier                                              = 0;
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120  
      ul_subcarrierSpacing                                           = 1;
      ul_carrierBandwidth                                            = 106;
      pMax                                                          = 20;
     #initialUplinkBWP
      #genericParameters
        initialULBWPlocationAndBandwidth                            = 28875;
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120  
        initialULBWPsubcarrierSpacing                                           = 1;
      #rach-ConfigCommon
        #rach-ConfigGeneric
          prach_ConfigurationIndex                                  = 98;
#prach_msg1_FDM
#0 = one, 1=two, 2=four, 3=eight
          prach_msg1_FDM                                            = 0;
          prach_msg1_FrequencyStart                                 = 0;
          zeroCorrelationZoneConfig                                 = 13;
          preambleReceivedTargetPower                               = -96;
#preamblTransMax (0...10) = (3,4,5,6,7,8,10,20,50,100,200)
          preambleTransMax                                          = 6;
#powerRampingStep
# 0=dB0,1=dB2,2=dB4,3=dB6
        powerRampingStep                                            = 1;
#ra_ReponseWindow
#1,2,4,8,10,20,40,80
        ra_ResponseWindow                                           = 4;
#ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR
#1=oneeighth,2=onefourth,3=half,4=one,5=two,6=four,7=eight,8=sixteen
        ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR                = 4;
#oneHalf (0..15) 4,8,12,16,...60,64
        ssb_perRACH_OccasionAndCB_PreamblesPerSSB                   = 15;
#ra_ContentionResolutionTimer
#(0..7) 8,16,24,32,40,48,56,64
        ra_ContentionResolutionTimer                                = 7;
        rsrp_ThresholdSSB                                           = 19;
#prach-RootSequenceIndex_PR
#1 = 839, 2 = 139
        prach_RootSequenceIndex_PR                                  = 2;
        prach_RootSequenceIndex                                     = 1;
        # SCS for msg1, can only be 15 for 30 kHz < 6 GHz, takes precendence over the one derived from prach-ConfigIndex
        #  
        msg1_SubcarrierSpacing                                      = 1,
# restrictedSetConfig
# 0=unrestricted, 1=restricted type A, 2=restricted type B
        restrictedSetConfig                                         = 0,

        msg3_DeltaPreamble                                          = 1;
        p0_NominalWithGrant                                         =-90;

# pucch-ConfigCommon setup :
# pucchGroupHopping
# 0 = neither, 1= group hopping, 2=sequence hopping
        pucchGroupHopping                                           = 0;
        hoppingId                                                   = 40;
        p0_nominal                                                  = -90;

      ssb_PositionsInBurst_Bitmap                                   = 1;

# ssb_periodicityServingCell
# 0 = ms5, 1=ms10, 2=ms20, 3=ms40, 4=ms80, 5=ms160, 6=spare2, 7=spare1 
      ssb_periodicityServingCell                                    = 2;

# dmrs_TypeA_position
# 0 = pos2, 1 = pos3
      dmrs_TypeA_Position                                           = 0;

# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120  
      subcarrierSpacing                                             = 1;


  #tdd-UL-DL-ConfigurationCommon
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120  
      referenceSubcarrierSpacing                                    = 1;
      # pattern1 
      # dl_UL_TransmissionPeriodicity
      # 0=ms0p5, 1=ms0p625, 2=ms1, 3=ms1p25, 4=ms2, 5=ms2p5, 6=ms5, 7=ms10
      dl_UL_TransmissionPeriodicity                                 = 6;
      nrofDownlinkSlots                                             = 7;
      nrofDownlinkSymbols                                           = 6;
      nrofUplinkSlots                                               = 2;
      nrofUplinkSymbols                                             = 4;

      ssPBCH_BlockPower                                             = -25;
     }

  );


    # ------- SCTP definitions
    SCTP :
    {
        # Number of streams to use in input/output
        SCTP_INSTREAMS  = 2;
        SCTP_OUTSTREAMS = 2;
    };
  }
);

MACRLCs = (
  {
    num_cc           = 1;
    tr_s_preference  = "local_L1";
    tr_n_preference  = "f1";
    local_n_address = "127.0.0.3";
    remote_n_address = "127.0.0.5";
    local_n_portc   = 500;
    local_n_portd   = 2152;
    remote_n_portc  = 501;
    remote_n_portd  = 2152;

  }
);

L1s = (
{
  num_cc = 1;
  tr_n_preference = "local_mac";
  prach_dtx_threshold = 120;
  pucch0_dtx_threshold = 150;
  ofdm_offset_divisor = 8; #set this to UINT_MAX for offset 0
}
);

RUs = (
    {		  
       local_rf       = "yes"
         nb_tx          = 4
         nb_rx          = 4
         att_tx         = 0
         att_rx         = 0
         bands          = [78];
         max_pdschReferenceSignalPower = -27;
         max_rxgain                    = 114;
         sf_extension                  = 0;
         eNB_instances  = [0];
         clock_src = "internal";
         ru_thread_core = 6;
         sl_ahead       = 5;
         do_precoding   = 0; # needs to match O-RU configuration
    }
);  

rfsimulator: {
serveraddr = "server";
    serverport = 4043;
    options = (); #("saviq"); or/and "chanmod"
    modelname = "AWGN";
    IQfile = "/tmp/rfsimulator.iqs"
}

     log_config :
     {
       global_log_level                      ="info";
       hw_log_level                          ="info";
       phy_log_level                         ="info";
       mac_log_level                         ="info";
      #  rlc_log_level                         ="info";
      #  pdcp_log_level                        ="info";
      #  rrc_log_level                         ="info";
      #  f1ap_log_level                        ="info";
      #  ngap_log_level                        ="info";
    };


fhi_72 = {
  dpdk_devices = ("0000:ca:02.0", "0000:ca:02.1"); # one VF can be used as well
  system_core = 0;
  io_core = 4;
  worker_cores = (2);
  ru_addr = ("e8:c7:4f:25:80:ed", "e8:c7:4f:25:80:ed");
  #old 
  # ru_addr = ("00:aa:ff:bb:ff:cc", "00:aa:ff:bb:ff:cc");
  mtu = 9000; # check if xran uses this properly
  fh_config = ({
    T1a_cp_dl = (285, 429);
    T1a_cp_ul = (285, 429);
    T1a_up = (96, 196);
    Ta4 = (110, 180);
    ru_config = {
      iq_width = 9;
      iq_width_prach = 9;
    };
    prach_config = {
      kbar = 0;
    };
  });
};
```
2025-10-14: Updated DU generator baseline path

- Changed `BASELINE_CONF` in `1_confgen_workspace/tool/du_generate_error_confs.py` to absolute path `C:\Users\bmwlab\Desktop\cursor_gen_conf\0_required_inputs\baseline_conf\du_gnb.conf`.

2025-10-14: Refactored DU generator paths and added CLI

- `1_confgen_workspace/tool/du_generate_error_confs.py` now uses repo-relative defaults and argparse.
- Defaults:
  - `--baseline`: `1_confgen_workspace/../0_required_inputs/baseline_conf/du_gnb.conf`
  - `--cases`: `1_confgen_workspace/1_conf/du_conf_1014_2_1000/json/cases_delta.json`
  - `--output`: `1_confgen_workspace/1_conf/du_conf_1014_2_1000/conf`
- Usage examples:
  - `python 1_confgen_workspace/tool/du_generate_error_confs.py`
  - `python 1_confgen_workspace/tool/du_generate_error_confs.py --baseline 0_required_inputs/baseline_conf/du_gnb.conf --cases 1_confgen_workspace/1_conf/du_conf_1014_800/json/cases_delta.json --output 1_confgen_workspace/1_conf/du_conf_1014_800/conf`

2025-10-14: Fixed DU block matching and subkey parsing

- Corrected block regex to non-greedily match `(<block> = ( ... ));` so `gNBs[0].min_rxtxtime` and similar keys are found inside the `gNBs` block.
- Fixed a typo in `subkey` extraction (`split("].")`).
- File: `1_confgen_workspace/tool/du_generate_error_confs.py`.

2025-10-14: Updated DU baseline JSON `min_rxtxtime`

- Set `min_rxtxtime` to `399` in `0_required_inputs/baseline_conf_json/du_gnb.json` so modifications targeting this key are reflected when generating error configs.