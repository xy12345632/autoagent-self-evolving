from typing import Dict, List, Optional, Tuple
from apscheduler.triggers.cron import CronTrigger as APSchedulerCronTrigger
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class CronTrigger:
    SECOND = 0
    MINUTE = 1
    HOUR = 2
    DAY = 3
    MONTH = 4
    WEEKDAY = 5
    YEAR = 6

    FIELD_NAMES = ["second", "minute", "hour", "day", "month", "day_of_week", "year"]

    def __init__(self, expr: Optional[str] = None, **kwargs):
        self._fields: Dict[str, str] = {}
        if expr:
            self.parse_cron_expression(expr)
        for key, value in kwargs.items():
            if key in self.FIELD_NAMES:
                self._fields[key] = str(value)

    def parse_cron_expression(self, expr: str) -> Dict[str, str]:
        parts = expr.strip().split()
        if len(parts) < 5 or len(parts) > 7:
            raise ValueError(f"Invalid cron expression: {expr}")

        defaults = {
            "second": "0",
            "minute": "*",
            "hour": "*",
            "day": "*",
            "month": "*",
            "day_of_week": "*",
            "year": "*"
        }

        field_mapping = [
            ("second", 0),
            ("minute", 1),
            ("hour", 2),
            ("day", 3),
            ("month", 4),
            ("day_of_week", 5),
            ("year", 6)
        ]

        for field_name, idx in field_mapping:
            if idx < len(parts):
                self._fields[field_name] = parts[idx]
            else:
                self._fields[field_name] = defaults[field_name]

        if not self.validate_cron(expr):
            raise ValueError(f"Invalid cron expression: {expr}")

        return self._fields

    def validate_cron(self, expr: str) -> bool:
        try:
            parts = expr.strip().split()
            if len(parts) < 5 or len(parts) > 7:
                return False

            second_validator = r"^(\*|[0-9]|[1-5][0-9])(/[0-9]+)?$"
            minute_validator = r"^(\*|[0-9]|[1-5][0-9])(/[0-9]+)?$"
            hour_validator = r"^(\*|[0-9]|1[0-9]|2[0-3])(/[0-9]+)?$"
            day_validator = r"^(\*|\?|L|W|[1-9]|[12][0-9]|3[01])(/[0-9]+)?$"
            month_validator = r"^(\*|[1-9]|1[0-2])(/[0-9]+)?$"
            dow_validator = r"^(\*|\?|L|[0-6])(-[0-6])?(/[0-9]+)?$"
            year_validator = r"^(\*|[0-9]{4})(/[0-9]+)?$"

            validators = [
                second_validator,
                minute_validator,
                hour_validator,
                day_validator,
                month_validator,
                dow_validator
            ]

            if len(parts) == 7:
                validators.append(year_validator)

            for i, part in enumerate(parts[:min(len(parts), 7)]):
                if not re.match(validators[i], part):
                    logger.warning(f"Invalid cron field at index {i}: {part}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Cron validation error: {e}")
            return False

    def get_next_fire_time(self, expr: str, from_time: Optional[datetime] = None) -> Optional[datetime]:
        try:
            trigger = self._create_apscheduler_trigger(expr)
            base_time = from_time or datetime.now()
            return trigger.get_next_fire_time(base_time, None)
        except Exception as e:
            logger.error(f"Failed to calculate next fire time: {e}")
            return None

    def _create_apscheduler_trigger(self, expr: str) -> APSchedulerCronTrigger:
        parts = expr.strip().split()

        cron_kwargs = {}
        field_map = {
            0: ("second", "second"),
            1: ("minute", "minute"),
            2: ("hour", "hour"),
            3: ("day", "day"),
            4: ("month", "month"),
            5: ("day_of_week", "day_of_week"),
            6: ("year", "year")
        }

        for idx, (field_name, _) in field_map.items():
            if idx < len(parts):
                value = parts[idx]
                if field_name == "day_of_week" and value == "?":
                    continue
                cron_kwargs[field_name] = value

        return APSchedulerCronTrigger(**cron_kwargs)

    def to_apscheduler_trigger(self) -> APSchedulerCronTrigger:
        return self._create_apscheduler_trigger(" ".join(self._fields.values()))

    @classmethod
    def from_apscheduler_trigger(cls, trigger: APSchedulerCronTrigger) -> "CronTrigger":
        fields = {
            "second": str(trigger.second) if trigger.second != "*" else "*",
            "minute": str(trigger.minute) if trigger.minute != "*" else "*",
            "hour": str(trigger.hour) if trigger.hour != "*" else "*",
            "day": str(trigger.day) if trigger.day != "*" else "*",
            "month": str(trigger.month) if trigger.month != "*" else "*",
            "day_of_week": str(trigger.day_of_week) if trigger.day_of_week != "*" else "*",
            "year": str(trigger.year) if hasattr(trigger, "year") and trigger.year != "*" else "*"
        }
        expr = " ".join([fields[f] for f in cls.FIELD_NAMES])
        return cls(expr=expr)

    def __str__(self) -> str:
        return " ".join([self._fields.get(f, "*") for f in self.FIELD_NAMES])

    def __repr__(self) -> str:
        return f"CronTrigger({self.__str__()})"
