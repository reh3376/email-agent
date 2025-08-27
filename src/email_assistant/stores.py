from __future__ import annotations

import datetime
import glob
import json
import os
from pathlib import Path
from typing import Any


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path))


class JsonStore:
    def __init__(self, path: str):
        self.path = _expand(path)

    def read(self) -> Any:
        if not self.path.exists():
            return None
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


class NdjsonStore:
    def __init__(self, dir_path: str):
        self.dir = _expand(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

    def append(self, obj: dict[str, Any], dt: datetime.date | None = None) -> Path:
        dt = dt or datetime.datetime.now().date()
        out = self.dir / f"{dt.isoformat()}.ndjson"
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj) + "\n")
        return out

    def scan(
        self,
        date: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Scan NDJSON files for records.

        Args:
            date: Specific date (YYYY-MM-DD) to filter by
            start: Start date (YYYY-MM-DD) for range filtering
            end: End date (YYYY-MM-DD) for range filtering
            limit: Maximum number of records to return

        Returns:
            List of decision records
        """
        files = self._get_files_to_scan(date, start, end)
        return self._read_files(files, limit)

    def _get_files_to_scan(self, date: str | None, start: str | None, end: str | None) -> list[str]:
        """Get list of files to scan based on filters."""
        if date:
            # Specific date filtering
            file_path = str(self.dir / f"{date}.ndjson")
            return [file_path] if os.path.exists(file_path) else []

        # Get all files
        files = sorted(glob.glob(str(self.dir / "*.ndjson")))

        # Apply date range filter if specified
        if start or end:
            return self._filter_files_by_date_range(files, start, end)

        return files

    def _filter_files_by_date_range(
        self, files: list[str], start: str | None, end: str | None
    ) -> list[str]:
        """Filter files by date range."""
        filtered_files = []

        for f in files:
            filename = os.path.basename(f)
            file_date = filename.replace(".ndjson", "")

            if start and file_date < start:
                continue
            if end and file_date > end:
                continue

            filtered_files.append(f)

        return filtered_files

    def _read_files(self, files: list[str], limit: int) -> list[dict[str, Any]]:
        """Read records from files up to limit."""
        rows: list[dict[str, Any]] = []

        for file_path in files:
            if not os.path.exists(file_path):
                continue

            rows.extend(self._read_file(file_path, limit - len(rows)))

            if len(rows) >= limit:
                break

        return rows

    def _read_file(self, file_path: str, max_records: int) -> list[dict[str, Any]]:
        """Read records from a single file."""
        records = []

        with open(file_path, encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                    if len(records) >= max_records:
                        break
                except Exception:
                    continue

        return records
