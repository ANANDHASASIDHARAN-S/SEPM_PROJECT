import asyncio
import os
import random
from datetime import datetime, timezone

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SIEM_API_KEY = os.getenv("SIEM_API_KEY", "local-dev-siem-key")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "25"))
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "1"))

SOURCES = ["SIEM", "EDR", "Firewall", "DNS", "WAF", "Identity Provider"]
EVENT_TYPES = [
    "Failed MFA Burst",
    "Impossible Travel Login",
    "Credential Stuffing Pattern",
    "Unusual Process Execution",
    "Data Exfiltration Signature",
    "Privilege Escalation Attempt",
    "Ransomware Behavior Chain",
]
ALERT_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def build_event() -> dict:
    level = random.choices(ALERT_LEVELS, weights=[30, 35, 25, 10], k=1)[0]
    return {
        "alert_level": level,
        "source": random.choice(SOURCES),
        "event_type": random.choice(EVENT_TYPES),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "OPEN",
        "details": f"Synthetic alert generated for load test. Level={level}",
    }


async def run() -> None:
    rate_per_minute = int(BATCH_SIZE * (60 / INTERVAL_SECONDS))
    print(f"Starting SIEM generator at ~{rate_per_minute} alerts/min")
    if rate_per_minute < 1000:
        print("Warning: current settings are below 1000 alerts/min")

    headers = {"X-API-Key": SIEM_API_KEY}
    endpoint = f"{BACKEND_URL}/siem/ingest"

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            payload = {"events": [build_event() for _ in range(BATCH_SIZE)]}
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                ingested = response.json().get("ingested", 0)
                print(f"{datetime.now().isoformat()} | Ingested batch: {ingested}")
            except Exception as exc:
                print(f"{datetime.now().isoformat()} | Ingest error: {exc}")
            await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
