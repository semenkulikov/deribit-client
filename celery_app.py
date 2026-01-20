from celery import Celery
from app.config import settings

celery_app = Celery(
    "deribit_client",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.price_fetcher"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "fetch-prices-every-minute": {
            "task": "app.tasks.price_fetcher.fetch_and_save_prices",
            "schedule": 60.0,  # каждую минуту
        },
    },
)
