import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaProducer


DEFAULT_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MODERATION_TOPIC = os.getenv("KAFKA_MODERATION_TOPIC", "moderation")
DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", "moderation_dlq")


@dataclass
class KafkaModerationClient:

    bootstrap_servers: str = DEFAULT_BOOTSTRAP_SERVERS
    moderation_topic: str = MODERATION_TOPIC
    dlq_topic: str = DLQ_TOPIC

    _producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        if self._producer is None:
            self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def send_moderation_request(self, item_id: int, task_id: int) -> None:
        assert self._producer is not None

        payload = {
            "item_id": item_id,
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        value = json.dumps(payload).encode("utf-8")
        await self._producer.send_and_wait(self.moderation_topic, value=value)

    async def send_to_dlq(self, message: dict, error: str, retry_count: int = 0) -> None:
        assert self._producer is not None

        payload = {
            "original_message": message,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retry_count": retry_count,
        }
        value = json.dumps(payload).encode("utf-8")
        await self._producer.send_and_wait(self.dlq_topic, value=value)


