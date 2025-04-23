import logging
import os

from taskiq import ScheduleSource, TaskiqScheduler
from taskiq_redis import RedisScheduleSource

from api.broker import broker

_logger = logging.getLogger(__name__)

sources: list[ScheduleSource] = []
if os.environ.get("JOBS_BROKER_URL", "").startswith("redis"):
    sources: list[ScheduleSource] = [RedisScheduleSource(os.environ["JOBS_BROKER_URL"])]
else:
    _logger.warning("No schedule source configured, skipping scheduler")

scheduler = TaskiqScheduler(
    broker=broker,
    sources=sources,
)
