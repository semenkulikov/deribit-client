import logging
from typing import Optional
import aiohttp
from aiohttp import ClientError, ClientTimeout

from app.config import settings

logger = logging.getLogger(__name__)


class DeribitClient:
    """Клиент для получения данных из Deribit API."""

    def __init__(self, base_url: Optional[str] = None):
        """Инициализация клиента."""
        self.base_url = base_url or settings.deribit_api_base_url
        self.timeout = ClientTimeout(total=10)

    async def get_index_price(self, ticker: str) -> Optional[float]:
        """
        Получить индексную цену для указанного тикера.

        Args:
            ticker: Тикер валюты (например, 'BTC_USD' или 'ETH_USD')

        Returns:
            Цена или None в случае ошибки
        """
        url = f"{self.base_url}/public/get_index_price"
        params = {"index_name": ticker}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Deribit API может возвращать данные в разных форматах
                        # Проверяем наличие result или прямого ответа
                        if "result" in data:
                            result = data.get("result", {})
                            index_price = result.get("index_price")
                        else:
                            # Если result нет, возможно данные в корне
                            index_price = data.get("index_price")
                        
                        if index_price is not None:
                            return float(index_price)
                        else:
                            logger.warning(f"Index price not found in response for {ticker}. Response: {data}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching price for {ticker}: HTTP {response.status}, Response: {error_text}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error fetching price for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {ticker}: {e}", exc_info=True)
            return None
