"""Email polling scheduler with preset and RRULE support."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from croniter import croniter
from dateutil.rrule import rrulestr


class EmailScheduler:
    """Scheduler for email polling with various schedule formats."""

    PRESETS = {
        "hourly": "0 * * * *",  # Every hour at minute 0
        "every_15_minutes": "*/15 * * * *",
        "every_30_minutes": "*/30 * * * *",
        "daily": "0 9 * * *",  # Daily at 9 AM
        "weekday": "0 9 * * 1-5",  # Weekdays at 9 AM
        "twice_daily": "0 9,17 * * *",  # 9 AM and 5 PM
    }

    MIN_INTERVAL_MINUTES = 15

    def __init__(self):
        """Initialize the scheduler."""
        self._schedule = None
        self._schedule_type = None

    def parse_schedule(self, schedule: str) -> bool:
        """
        Parse and validate a schedule expression.

        Args:
            schedule: Schedule expression (preset, cron, or RRULE)

        Returns:
            True if valid, False otherwise
        """
        # Check for preset
        if schedule.lower() in self.PRESETS:
            self._schedule = self.PRESETS[schedule.lower()]
            self._schedule_type = "cron"
            return True

        # Check for "every X minutes" format
        if match := re.match(r"every\s+(\d+)\s+minutes?", schedule.lower()):
            minutes = int(match.group(1))
            if minutes < self.MIN_INTERVAL_MINUTES:
                return False
            self._schedule = f"*/{minutes} * * * *"
            self._schedule_type = "cron"
            return True

        # Try to parse as cron
        try:
            croniter(schedule)
            self._schedule = schedule
            self._schedule_type = "cron"
            return True
        except (ValueError, TypeError):
            pass

        # Try to parse as RRULE
        try:
            rrulestr(schedule)
            self._schedule = schedule
            self._schedule_type = "rrule"
            return True
        except (ValueError, TypeError):
            pass

        return False

    def get_next_runs(
        self, schedule: str | None = None, count: int = 10, start_time: datetime | None = None
    ) -> list[datetime]:
        """
        Get the next scheduled run times.

        Args:
            schedule: Schedule expression (uses stored schedule if None)
            count: Number of future runs to return
            start_time: Start time for calculations (defaults to now)

        Returns:
            List of next run times
        """
        # Validate schedule
        if schedule is not None:
            if not self.parse_schedule(schedule):
                raise ValueError(f"Invalid schedule: {schedule}")
        elif self._schedule is None:
            raise ValueError("No schedule configured")

        if start_time is None:
            start_time = datetime.now()

        # Generate runs based on schedule type
        if self._schedule_type == "cron":
            return self._get_cron_runs(start_time, count)
        elif self._schedule_type == "rrule":
            return self._get_rrule_runs(start_time, count)

        return []

    def _get_cron_runs(self, start_time: datetime, count: int) -> list[datetime]:
        """Get next runs for cron schedule."""
        next_runs = []
        cron = croniter(self._schedule, start_time)
        for _ in range(count):
            next_runs.append(cron.get_next(datetime))
        return next_runs

    def _get_rrule_runs(self, start_time: datetime, count: int) -> list[datetime]:
        """Get next runs for RRULE schedule."""
        next_runs = []
        rule = rrulestr(self._schedule, dtstart=start_time)
        for dt in rule:
            if dt > start_time:
                next_runs.append(dt)
                if len(next_runs) >= count:
                    break
        return next_runs

    def validate_minimum_interval(self, schedule: str) -> bool:
        """
        Validate that the schedule respects the minimum interval.

        Args:
            schedule: Schedule expression

        Returns:
            True if interval is valid
        """
        try:
            next_runs = self.get_next_runs(schedule, count=2)
            if len(next_runs) < 2:
                return True

            interval = next_runs[1] - next_runs[0]
            return interval >= timedelta(minutes=self.MIN_INTERVAL_MINUTES)
        except Exception:
            return False

    def get_schedule_description(self, schedule: str) -> str:
        """
        Get a human-readable description of the schedule.

        Args:
            schedule: Schedule expression

        Returns:
            Human-readable description
        """
        # Check presets
        description = self._check_preset_description(schedule)
        if description:
            return description

        # Check "every X minutes"
        if match := re.match(r"every\s+(\d+)\s+minutes?", schedule.lower()):
            return f"Every {match.group(1)} minutes"

        # For cron expressions, try to generate description
        description = self._get_cron_description(schedule)
        if description:
            return description

        return schedule

    def _check_preset_description(self, schedule: str) -> str | None:
        """Check if schedule matches a preset."""
        for preset_name, preset_cron in self.PRESETS.items():
            if schedule.lower() == preset_name or schedule == preset_cron:
                descriptions = {
                    "hourly": "Every hour",
                    "every_15_minutes": "Every 15 minutes",
                    "every_30_minutes": "Every 30 minutes",
                    "daily": "Daily at 9:00 AM",
                    "weekday": "Weekdays at 9:00 AM",
                    "twice_daily": "Twice daily at 9:00 AM and 5:00 PM",
                }
                return descriptions.get(preset_name, preset_name.replace("_", " ").title())
        return None

    def _get_cron_description(self, schedule: str) -> str | None:
        """Generate description for cron expression."""
        if not (self.parse_schedule(schedule) and self._schedule_type == "cron"):
            return None

        try:
            parts = self._schedule.split()
            if len(parts) == 5:
                minute, hour, _, _, weekday = parts

                # Simple patterns
                if minute == "0" and hour == "*":
                    return "Every hour"
                elif minute == "0" and hour.isdigit():
                    return f"Daily at {int(hour):02d}:00"
                elif minute.startswith("*/"):
                    interval = minute[2:]
                    return f"Every {interval} minutes"
                elif minute == "0" and weekday == "1-5":
                    return f"Weekdays at {hour}:00"
        except Exception:
            pass

        return None
