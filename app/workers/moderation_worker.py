import asyncio
import json
import logging
from typing import Any, Dict

from aiokafka import AIOKafkaConsumer

from db import close_db, get_connection, init_db
from model import get_or_train_model
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from repositories.users import UserRepository
from schemas.models import AdRequest
from services.moderation import prepare_features
from app.clients.kafka import KafkaModerationClient, MODERATION_TOPIC


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def handle_message(message: Dict[str, Any], model) -> None:
    item_id = int(message["item_id"])
    task_id = int(message["task_id"])

    await init_db()

    async with get_connection() as conn:
        ad_repo = AdRepository(conn)
        user_repo = UserRepository(conn)
        mod_repo = ModerationResultRepository(conn)

        kafka_client = KafkaModerationClient()
        await kafka_client.start()

        try:
            ad = await ad_repo.get(item_id)
            if ad is None:
                raise ValueError(f"Ad with id={item_id} not found")

            user = await user_repo.get(ad.seller_id)
            if user is None:
                raise ValueError(f"User with id={ad.seller_id} not found")

            ad_request = AdRequest(
                seller_id=user.id,
                is_verified_seller=user.is_verified_seller,
                item_id=ad.id,
                name=ad.title,
                description=ad.description,
                category=ad.category,
                images_qty=ad.images_qty,
            )

            features = prepare_features(ad_request)
            probability = float(model.predict_proba(features)[0][1])
            is_violation = probability > 0.5

            await mod_repo.update_result(
                task_id,
                status="completed",
                is_violation=is_violation,
                probability=probability,
                error_message=None,
            )

            logger.info(
                "Moderation completed: task_id=%s, item_id=%s, is_violation=%s, probability=%s",
                task_id,
                item_id,
                is_violation,
                probability,
            )
        except Exception as exc:
            error_msg = str(exc)
            logger.exception("Error while processing moderation task %s: %s", task_id, error_msg)

            await mod_repo.update_result(
                task_id,
                status="failed",
                is_violation=None,
                probability=None,
                error_message=error_msg,
            )

            await kafka_client.send_to_dlq(message, error_msg, retry_count=0)
        finally:
            await kafka_client.stop()


async def main() -> None:
    logger.info("Starting moderation worker...")

    # один раз при старте воркера
    model = get_or_train_model()

    consumer = AIOKafkaConsumer(
        MODERATION_TOPIC,
        bootstrap_servers="localhost:9092",
        group_id="moderation-workers",
        enable_auto_commit=True,
    )

    await init_db()
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                payload = json.loads(msg.value.decode("utf-8"))
                logger.info("Received message from Kafka: %s", payload)
                await handle_message(payload, model)
            except json.JSONDecodeError:
                logger.exception("Failed to decode Kafka message: %s", msg.value)
    finally:
        await consumer.stop()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())





