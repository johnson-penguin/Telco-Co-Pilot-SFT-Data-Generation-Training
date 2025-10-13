\n+## 1. Overall Context and Setup Assumptions
We analyze an OAI 5G NR SA setup with rfsim. Expected flow: CU init and NGAP with AMF → F1 setup with DU → DU PHY brings up cell (SSB/SS raster) → UE sync and PRACH → RRC attach and PDU session. We focus on TDD UL/DL pattern fields within `servingCellConfigCommon`: `dl_UL_TransmissionPeriodicity`, `nrofDownlinkSlots`, `nrofDownlinkSymbols`, `nrofUplinkSlots`, `nrofUplinkSymbols` and ensure consistency with numerology (mu) and slots-per-period.

Guided by `misconfigured_param = "nrofDownlinkSlots=15"`. Parsed DU config shows mu=1 behavior in logs (30 kHz numerology) and `dl_UL_TransmissionPeriodicity = 6` (5 ms). With mu=1, there are 2 slots per 1 ms, so within 5 ms there are 10 full slots. Therefore, `nrofDownlinkSlots=15` cannot fit: it exceeds the slots available in the DL/UL period, violating the TDD pattern constraints.

Key parsed params:
- DU `servingCellConfigCommon`: `dl_subcarrierSpacing=1`, `ul_subcarrierSpacing=1`, `initialDL/ULBWPsubcarrierSpacing=1`, `referenceSubcarrierSpacing=1`, `subcarrierSpacing=1`, `dl_UL_TransmissionPeriodicity=6` (5 ms), `nrofDownlinkSlots=15` (suspect), `nrofDownlinkSymbols=6`, `nrofUplinkSlots=2`, `nrofUplinkSymbols=4`, `absoluteFrequencySSB=641280` (3619.2 MHz), band 78. PRACH `msg1_SubcarrierSpacing=1`, `prach_ConfigurationIndex=98` (typical for n78+30kHz). RU local_rf yes; rfsim server binds and waits.
- CU: NGAP setup normal; F1 established with DU.
- UE: center freq 3619200000, BW 106 PRBs; repeated SSB sync failures.

Initial mismatch: DL/UL TDD allocation exceeds period capacity: `nrofDownlinkSlots=15` in a 5 ms period with mu=1 (10 slots available). This can lead to scheduling timeline inconsistencies at PHY, out-of-order Tx warnings, and no valid SSB transmissions in expected positions for the UE to detect.

## 2. Analyzing CU Logs
- SA mode, NGAP setup succeeds: NGSetupRequest/Response exchanged; CU indicates cell in service after F1 Setup with DU.
- F1AP started and the DU has completed F1 Setup; no CU-side anomaly. CU is ready and depends on DU PHY to broadcast SSB and serve UE.

Cross-reference: CU `NETWORK_INTERFACES` 192.168.8.43 aligns with GTPU logs; F1 loopback addresses 127.0.0.5/127.0.0.3 match DU.

## 3. Analyzing DU Logs
- DU starts F1, receives Setup Response, config update ack; RU runs as rfsim server and is ready. PHY prints mu=1, N_RB=106, sample_rate 61.44 Msps — typical for 30 kHz numerology.
- Critical anomalies:
  - `Not supported to send Tx out of order ...` warning from rfsim indicates timestamp ordering violations on transmit samples, consistent with an invalid TDD slot allocation that does not fit into the period definition.
  - Despite server up, an inconsistent TDD pattern can prevent correct SSB scheduling and DL bursts in expected slots.

Interpretation: With `dl_UL_TransmissionPeriodicity=6` (5 ms) and mu=1 (10 slots per 5 ms), setting `nrofDownlinkSlots=15` overflows the period and corrupts the slot timing model. OAI may not assert immediately but manifests as out-of-order Tx and absence of valid SSB symbols in their raster positions.

## 4. Analyzing UE Logs
- UE performs repeated initial synch: "Scanning GSCN: 0 ... SSB Freq: 0.000000" and "synch Failed" loops.
- This indicates no detectable SSB in the expected raster. Given DU’s TDD inconsistency, SSB is either not scheduled in a valid DL slot or timing is incoherent, so UE cannot lock.

## 5. Cross-Component Correlations and Root Cause Hypothesis
- CU–DU F1 is up; RU/rfsim server is up. UE connects to server but cannot find SSB; DU logs show Tx ordering issues. The only misconfig provided is `nrofDownlinkSlots=15`, which mathematically exceeds the number of slots available in the configured period for mu=1.
- Root cause: Invalid TDD UL/DL pattern — `nrofDownlinkSlots` exceeds the period capacity defined by `dl_UL_TransmissionPeriodicity` and numerology (mu=1 → 2 slots/ms; 5 ms → 10 slots). This yields inconsistent PHY scheduling, leading to out-of-order Tx and no valid SSB for UE synchronization.
- PRACH settings likely fine but never reached because UE cannot synchronize without SSB.

## 6. Recommendations for Fix and Further Analysis
Configuration fix (keep mu=1 and 5 ms periodicity, use a known-good OAI pattern): set `nrofDownlinkSlots` to a value that fits (e.g., 7) with existing `nrofDownlinkSymbols=6`, `nrofUplinkSlots=2`, `nrofUplinkSymbols=4`. This matches common OAI defaults and respects 10-slot capacity for 5 ms at mu=1.

Corrected snippets embedded in the network_config structure (comments explain changes):

```json
{
  "du_conf": {
    "gNBs": [
      {
        "servingCellConfigCommon": [
          {
            "dl_UL_TransmissionPeriodicity": 6,  // 5 ms period at mu=1 → 10 slots capacity
            "nrofDownlinkSlots": 7,              // was 15 → fits within 10 slots
            "nrofDownlinkSymbols": 6,            // unchanged
            "nrofUplinkSlots": 2,                // unchanged; DL 7 + UL 2 = 9 slots, remainder handled by symbols
            "nrofUplinkSymbols": 4               // unchanged
          }
        ]
      }
    ]
  },
  "ue_conf": {
    "uicc0": {
      "imsi": "001010000000001"
      // no changes required on UE for TDD pattern; UE just needs valid SSB/DL slots
    }
  }
}
```

Post-fix validation:
- DU logs should no longer show out-of-order Tx warnings; SSB/PBCH should be transmitted in valid DL slots.
- UE should detect SSB (GSCN computed from `absoluteFrequencySSB`), achieve sync, then proceed with PRACH.
- Monitor MAC/RRC: RA procedure (Msg1/Msg2/Msg3/Msg4), RRC Setup Complete, and F1/NGAP UEContext setup.
- If further issues: verify the mapping from `dl_UL_TransmissionPeriodicity` value to ms in your OAI version; ensure total DL+UL slots and partial-symbol allocations do not exceed period capacity for mu=1.

## 7. Limitations
- Logs are truncated and without timestamps, so precise ordering is inferred.
- Some band printouts (e.g., band 48) may be benign OAI mapping quirks; core issue is TDD slot overflow.
- Exact interpretation of `dl_UL_TransmissionPeriodicity` value may vary by OAI release; the capacity check remains valid: slots_per_period = (period_ms × slots_per_ms(mu)). Ensure DL/UL totals fit.
9