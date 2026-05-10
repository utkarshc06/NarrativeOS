import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
        self._buffer: list[dict[str, Any]] = []
        self._client = httpx.Client(timeout=30)

    def emit(self, event: dict[str, Any]) -> None:
        self._buffer.append(event)
        logger.info("Event buffered: %s — %s", event.get("id"), event.get("title", "")[:60])

    def flush(self) -> list[dict[str, Any]]:
        batch = list(self._buffer)
        self._buffer.clear()
        if not batch:
            return batch
        if self.webhook_url:
            try:
                payload = {"events": batch, "trigger": "webhook"}
                resp = self._client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                logger.info("Flushed %d events → %s", len(batch), self.webhook_url)
            except Exception as e:
                logger.warning("Webhook flush failed (%s), keeping buffer: %s", self.webhook_url, e)
                self._buffer = batch + self._buffer
        return batch

    def close(self) -> None:
        self.flush()
        self._client.close()
