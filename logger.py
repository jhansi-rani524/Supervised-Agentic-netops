import json
from datetime import datetime
from zoneinfo import ZoneInfo

LOG_FILE = "network_log.jsonl"

def log_event(script, host, status, details=""):
    entry = {
        "timestamp": datetime.now(ZoneInfo("America/Chicago")).isoformat(),
        "script": script,
        "host": host,
        "status": status,
        "details": details
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")