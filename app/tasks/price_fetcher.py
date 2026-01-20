import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.client.deribit_client import DeribitClient
from app.config import settings
from app.db.crud import PriceRepository
from celery_app import celery_app

logger = logging.getLogger(__name__)


def create_session_maker():
    """Создать async sessionmaker для использования в Celery задаче."""
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@celery_app.task(name="app.tasks.price_fetcher.fetch_and_save_prices")
def fetch_and_save_prices() -> dict:
    """
    Получить цены BTC_USD и ETH_USD и сохранить в БД.

    Returns:
        Словарь с результатами выполнения
    """
    import asyncio

    async def _fetch_and_save():
        """Внутренняя async функция для выполнения задачи."""
        client = DeribitClient()
        tickers = ["BTC_USD", "ETH_USD"]
        results = {"success": [], "failed": []}
        current_timestamp = int(time.time())

        session_maker = create_session_maker()
        async with session_maker() as async_session:
            repository = PriceRepository(async_session)

            for ticker in tickers:
                try:
                    price = await client.get_index_price(ticker)
                    if price is not None:
                        await repository.create(ticker, price, current_timestamp)
                        results["success"].append({"ticker": ticker, "price": price})
                        logger.info(f"Successfully saved price for {ticker}: {price}")
                    else:
                        results["failed"].append({"ticker": ticker, "reason": "Price is None"})
                        logger.warning(f"Failed to get price for {ticker}: price is None")
                except Exception as e:
                    error_msg = str(e)
                    results["failed"].append({"ticker": ticker, "reason": error_msg})
                    logger.error(f"Unexpected error fetching price for {ticker}: {e}", exc_info=True)

            try:
                await async_session.commit()
            except Exception as e:
                await async_session.rollback()
                logger.error(f"Database error: {e}")
                raise

        return results

    # Запуск async функции в синхронном контексте Celery
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_fetch_and_save())
