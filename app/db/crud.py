from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Price


class PriceRepository:
    """Репозиторий для работы с ценами."""

    def __init__(self, session: AsyncSession):
        """Инициализация репозитория."""
        self.session = session

    async def create(self, ticker: str, price: float, timestamp: int) -> Price:
        """Создать новую запись о цене."""
        price_obj = Price(
            ticker=ticker.upper(),
            price=price,
            timestamp=timestamp,
        )
        self.session.add(price_obj)
        await self.session.commit()
        await self.session.refresh(price_obj)
        return price_obj

    async def get_all_by_ticker(self, ticker: str, limit: Optional[int] = None, offset: int = 0) -> List[Price]:
        """Получить все записи по тикеру."""
        query = select(Price).where(Price.ticker == ticker.upper()).order_by(desc(Price.timestamp))
        if limit:
            query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_ticker(self, ticker: str) -> Optional[Price]:
        """Получить последнюю цену по тикеру."""
        query = (
            select(Price)
            .where(Price.ticker == ticker.upper())
            .order_by(desc(Price.timestamp))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ticker_and_date_range(
        self,
        ticker: str,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
    ) -> List[Price]:
        """Получить цены по тикеру в диапазоне дат."""
        query = select(Price).where(Price.ticker == ticker.upper())

        if start_timestamp:
            query = query.where(Price.timestamp >= start_timestamp)
        if end_timestamp:
            query = query.where(Price.timestamp <= end_timestamp)

        query = query.order_by(desc(Price.timestamp))
        result = await self.session.execute(query)
        return list(result.scalars().all())
