import json
from collections import Counter
from pathlib import Path
from typing import Any


class AuditStatsService:
    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)

    def get_stats(self) -> dict[str, Any]:
        if not self.log_path.exists():
            return self._empty_stats()

        total_events = 0
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        total_redactions = 0
        total_tokens = 0
        high_risk_requests = 0

        status_counts: Counter[str] = Counter()
        provider_counts: Counter[str] = Counter()
        entity_counts: Counter[str] = Counter()
        error_counts: Counter[str] = Counter()

        recent_events: list[dict[str, Any]] = []

        with self.log_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total_events += 1

                status = event.get("status", "unknown")
                status_counts[status] += 1

                provider = event.get("provider_used")
                if provider:
                    provider_counts[provider] += 1

                if status == "success":
                    total_requests += 1
                    successful_requests += 1

                    redactions = int(event.get("redactions_applied", 0) or 0)
                    total_redactions += redactions

                    risk_score = float(event.get("risk_score", 0) or 0)
                    if risk_score >= 0.7:
                        high_risk_requests += 1

                    usage = event.get("usage", {}) or {}
                    total_tokens += int(usage.get("total_tokens", 0) or 0)

                    for entity_type, count in (event.get("entity_counts", {}) or {}).items():
                        entity_counts[entity_type] += int(count or 0)
                else:
                    failed_requests += 1
                    error_type = event.get("error_type")
                    if error_type:
                        error_counts[error_type] += 1

                recent_events.append(self._safe_recent_event(event))
                recent_events = recent_events[-10:]

        return {
            "total_events": total_events,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_redactions": total_redactions,
            "total_tokens": total_tokens,
            "high_risk_requests": high_risk_requests,
            "status_counts": dict(status_counts),
            "provider_counts": dict(provider_counts),
            "entity_counts": dict(entity_counts),
            "error_counts": dict(error_counts),
            "recent_events": recent_events,
        }

    def _safe_recent_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "request_id": event.get("request_id"),
            "user_id": event.get("user_id"),
            "api_key_prefix": event.get("api_key_prefix"),
            "provider_used": event.get("provider_used"),
            "model": event.get("model"),
            "status": event.get("status"),
            "latency_ms": event.get("latency_ms"),
            "redactions_applied": event.get("redactions_applied"),
            "risk_score": event.get("risk_score"),
            "entity_counts": event.get("entity_counts", {}),
            "usage": event.get("usage", {}),
            "error_type": event.get("error_type"),
            "recorded_at": event.get("recorded_at"),
        }

    def _empty_stats(self) -> dict[str, Any]:
        return {
            "total_events": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_redactions": 0,
            "total_tokens": 0,
            "high_risk_requests": 0,
            "status_counts": {},
            "provider_counts": {},
            "entity_counts": {},
            "error_counts": {},
            "recent_events": [],
        }