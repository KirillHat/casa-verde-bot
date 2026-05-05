"""Request correlation + lightweight in-process HTTP metrics."""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class _Metric:
    count: int = 0
    total_seconds: float = 0.0


class MetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[tuple[str, str, str], _Metric] = {}

    def observe(self, *, method: str, path: str, status: int, duration_seconds: float) -> None:
        key = (method.upper(), path, str(status))
        with self._lock:
            metric = self._data.setdefault(key, _Metric())
            metric.count += 1
            metric.total_seconds += duration_seconds

    def render_prometheus(self) -> str:
        lines = [
            "# HELP app_http_requests_total Total HTTP requests by method/path/status.",
            "# TYPE app_http_requests_total counter",
            "# HELP app_http_request_duration_seconds_sum Total request duration by method/path/status.",
            "# TYPE app_http_request_duration_seconds_sum counter",
        ]
        with self._lock:
            for (method, path, status), metric in sorted(self._data.items()):
                labels = f'method="{method}",path="{path}",status="{status}"'
                lines.append(f"app_http_requests_total{{{labels}}} {metric.count}")
                lines.append(
                    "app_http_request_duration_seconds_sum"
                    f"{{{labels}}} {metric.total_seconds:.6f}"
                )
        return "\n".join(lines) + "\n"
