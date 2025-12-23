import os
from google.cloud import pubsub_v1

from ..config import Settings
from ..logger import get_logger

settings = Settings()
logger = get_logger(__name__)


class PubSubPublisher:
    def __init__(self) -> None:
        if settings.pubsub_emulator_host:
            os.environ["PUBSUB_EMULATOR_HOST"] = settings.pubsub_emulator_host
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = settings.gcp_project
        self._ensure_topic(settings.pubsub_topic_ingestion)
        self._ensure_topic(settings.pubsub_topic_status)

    def publish_ingestion(self, message: dict) -> None:
        topic_path = self.publisher.topic_path(self.project_id, settings.pubsub_topic_ingestion)
        data = str(message).encode("utf-8")
        future = self.publisher.publish(topic_path, data=data, job_id=message.get("job_id", "").encode("utf-8"))
        future.add_done_callback(lambda x: logger.info("Published ingestion event", job_id=message.get("job_id")))

    def publish_status(self, message: dict) -> None:
        topic_path = self.publisher.topic_path(self.project_id, settings.pubsub_topic_status)
        data = str(message).encode("utf-8")
        self.publisher.publish(topic_path, data=data, job_id=message.get("job_id", "").encode("utf-8"))

    def _ensure_topic(self, topic_name: str) -> None:
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        try:
            self.publisher.create_topic(name=topic_path)
            logger.info("Created Pub/Sub topic", topic=topic_name)
        except Exception:
            # Assume already exists
            pass

