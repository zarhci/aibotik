import subprocess
import time
import sys

CHECK_INTERVAL = 30  # секунд

while True:
    result = subprocess.run(
        ["python", "healthcheck.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if result.returncode != 0:
        print("❌ Healthcheck failed. Restarting container...")
        sys.exit(1)  # контейнер упадёт

    time.sleep(CHECK_INTERVAL)
