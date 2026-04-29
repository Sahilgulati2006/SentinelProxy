import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def record(self, event: dict[str, Any]) -> None:
        safe_event = {
            **event,
            "recorded_at": int(time.time()),
        }

        try:
            with self.log_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(safe_event) + "\n")
        except Exception:
            logger.warning("Failed to write audit log.", exc_info=True)