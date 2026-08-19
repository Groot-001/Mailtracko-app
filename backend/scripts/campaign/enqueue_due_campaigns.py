"""Enqueue due Campaign jobs once; suitable for a one-minute cron entry."""

from src.modules.campaign.infrastructure.background_tasks.campaign_tasks import (
    enqueue_due_campaigns,
)


if __name__ == "__main__":
    enqueue_due_campaigns.send()
    print("Due Campaign scan queued")
