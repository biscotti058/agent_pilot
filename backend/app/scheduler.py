"""Scheduler per workflow ricorrenti (report settimanali, reminder, ecc.)."""

import logging
import time

from app.core.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("workflow.scheduler")


def main() -> None:
    logger.info("WorkFlow Scheduler avviato — in attesa di cron job...")
    # TODO: integrare APScheduler o Celery Beat
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
