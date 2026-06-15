"""Celery worker per task asincroni: reminder, automazioni, batch."""

import logging
import time

from app.core.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("workflow.worker")


def main() -> None:
    logger.info("WorkFlow Worker avviato — in attesa di job...")
    # TODO: integrare Celery con Redis come broker
    # from app.worker.celery_app import celery_app
    # celery_app.worker_main(["worker", "--loglevel=info"])
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
