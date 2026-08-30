import time
from datetime import datetime


class ScanScheduler:
    def __init__(self, interval_seconds: int = 3600):
        self.interval_seconds = interval_seconds

    def run_every_interval(self, callback, max_runs: int = 1):
        runs = 0
        while runs < max_runs:
            timestamp = datetime.utcnow().isoformat(timespec='seconds')
            result = callback()
            runs += 1
            print(f"[{timestamp}] Scan run {runs} completed.")
            if runs >= max_runs:
                return result
            time.sleep(self.interval_seconds)
        return None


def scheduled_scan(callback, interval_seconds: int = 3600, max_runs: int = 1):
    scheduler = ScanScheduler(interval_seconds=interval_seconds)
    return scheduler.run_every_interval(callback, max_runs=max_runs)
