"""Continuously enqueue due Campaign batches for the Dramatiq worker."""

import os
import time

from src.modules.campaign.infrastructure.background_tasks.campaign_tasks import (
    enqueue_due_campaigns,
)


INTERVAL_SECONDS = max(int(os.getenv("CAMPAIGN_SCHEDULER_INTERVAL_SECONDS", "30")), 5)


if __name__ == "__main__":
    print(f"Campaign scheduler started (interval={INTERVAL_SECONDS}s)")
    while True:
        enqueue_due_campaigns.send()
        time.sleep(INTERVAL_SECONDS)
