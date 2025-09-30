import json
import os
import re
from pathlib import Path


LOG_ROOT = Path(__file__).resolve().parent / "logs_batch_run_cu_0930"
OUTPUT_DIR = Path(__file__).resolve().parent / "analyze_log"


KEYWORD_TO_ERROR = [
    (re.compile(r"\bFATAL\b", re.IGNORECASE), ("FATAL", "Fatal Error")),
    (re.compile(r"\bERROR\b", re.IGNORECASE), ("ERROR", "Error")),
    (re.compile(r"Assertion", re.IGNORECASE), ("ERROR", "Assertion Error")),
    (re.compile(r"Segmentation fault|crash", re.IGNORECASE), ("FATAL", "Crash")),
    (re.compile(r"(failed|failure)", re.IGNORECASE), ("ERROR", "Failure")),
    (re.compile(r"(timeout|timed out)", re.IGNORECASE), ("ERROR", "Timeout")),
    (re.compile(r"(could not|cannot|can't|not found|no such file)", re.IGNORECASE), ("WARN", "Missing/Not Found")),
    (re.compile(r"(reject|rejected|denied)", re.IGNORECASE), ("WARN", "Rejected/Denied")),
]


def classify_log_line(message: str):
    level = None
    error_short = None
    for pattern, (lvl, err) in KEYWORD_TO_ERROR:
        if pattern.search(message):
            level = lvl
            error_short = err
            break
    # Try to read explicit level if present like [ERROR] or similar
    if level is None:
        m = re.search(r"\[(FATAL|ERROR|WARN|WARNING|INFO|DEBUG)\]", message, re.IGNORECASE)
        if m:
            lvl = m.group(1).upper()
            # map WARNING to WARN
            level = "WARN" if lvl == "WARNING" else lvl
            # Only consider as error if ERROR/FATAL
            if level in ("ERROR", "FATAL"):
                error_short = "Error" if level == "ERROR" else "Fatal Error"
    return level, error_short


def infer_unit_from_key(key: str) -> str:
    key_upper = key.upper()
    if "CU" in key_upper:
        return "CU"
    if "DU" in key_upper:
        return "DU"
    if "UE" in key_upper:
        return "UE"
    return key


def summarize_event(message: str) -> str:
    # Strip ANSI codes for clarity
    msg_clean = re.sub(r"\x1b\[[0-9;]*m", "", message).strip()
    # Heuristic summarization: take bracketed tag and a concise reason
    m = re.search(r"\[(?P<tag>[A-Z_]+)\]\s+(?P<body>.*)", msg_clean)
    if m:
        tag = m.group("tag")
        body = m.group("body")
        # Compress long bodies
        body = re.sub(r"\s+", " ", body)
        if len(body) > 160:
            body = body[:157] + "..."
        return f"{tag}: {body}"
    return msg_clean[:160] + ("..." if len(msg_clean) > 160 else "")


def analyze_tail100_file(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [{
            "Unit": "N/A",
            "Error": "Read Error",
            "Log Level": "ERROR",
            "Message": f"Failed to read {path.name}: {e}",
            "Event Description": "Could not parse tail100_summary.json"
        }]

    results = []
    for key, lines in data.items():
        unit = infer_unit_from_key(key)
        for raw in lines:
            if not raw or not isinstance(raw, str):
                continue
            level, error_short = classify_log_line(raw)
            # Only include entries that indicate an error (ERROR/FATAL) or clear failure heuristics
            if level in ("ERROR", "FATAL") or error_short in ("Assertion Error", "Failure", "Timeout", "Crash"):
                msg_clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)
                results.append({
                    "Unit": unit,
                    "Error": error_short or ("Fatal Error" if level == "FATAL" else "Error"),
                    "Log Level": level or "ERROR",
                    "Message": msg_clean.strip(),
                    "Event Description": summarize_event(msg_clean),
                })
            # Include some warnings that are clearly error-like (missing/not found)
            elif error_short == "Missing/Not Found":
                msg_clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)
                results.append({
                    "Unit": unit,
                    "Error": error_short,
                    "Log Level": level or "WARN",
                    "Message": msg_clean.strip(),
                    "Event Description": summarize_event(msg_clean),
                })
    return results


def collect_runs(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        if "tail100_summary.json" in filenames:
            run_dir = Path(dirpath)
            yield run_dir, run_dir / "tail100_summary.json"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    any_written = False
    for run_dir, json_path in collect_runs(LOG_ROOT):
        results = analyze_tail100_file(json_path)
        # Skip empty results as instructed
        if not results:
            continue
        # Name output by run folder name
        out_name = f"{run_dir.name}.json"
        out_path = OUTPUT_DIR / out_name
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        any_written = True
    if not any_written:
        # Write a summary marker so users know script ran
        marker = OUTPUT_DIR / "_no_errors_found.txt"
        marker.write_text("No error-like entries found in any tail100_summary.json.", encoding="utf-8")


if __name__ == "__main__":
    main()


