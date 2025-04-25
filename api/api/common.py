import logging
import os
from logging import INFO, getLevelNamesMapping

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

excluded_fields = {
    "args",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
    "thread",
}


def setup_sentry():
    if os.environ.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.environ.get("SENTRY_DSN"),
            environment=os.environ.get("ENV_NAME", "local"),
            release=os.environ.get("SENTRY_RELEASE", "local"),
            enable_tracing=True,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            integrations=[
                # Making sure warnings are sent to sentry
                LoggingIntegration(event_level=logging.WARNING),
                StarletteIntegration(),
                FastApiIntegration(),
            ],
        )


_logs_are_setup = False


def setup_logs() -> bool:
    json_logs = os.getenv("LOG_JSON", "true") == "true"

    global _logs_are_setup

    if _logs_are_setup:
        return json_logs
    _logs_are_setup = True

    setup_sentry()

    # Get the root logger
    logger = logging.getLogger()

    if json_logs:
        from core.utils.logs_json import CappedJsonFormatter

        logHandler = logging.StreamHandler()
        formatter = CappedJsonFormatter(max_length=1000)
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)

    level_name = os.getenv("LOG_LEVEL", "INFO")
    level = getLevelNamesMapping().get(level_name.upper())
    if not level:
        logger.warning("Invalid log level", extra={"level_name": level_name})
        level = INFO
    # Set root logger level to affect all loggers
    logger.setLevel(level)

    return json_logs


def setup_workflowai():
    import workflowai

    workflowai.init(default_version=os.getenv("WORKFLOWAI_ENV_FOR_INTERNAL_TASKS"))  # type: ignore


def setup() -> None:
    setup_logs()
    setup_workflowai()
