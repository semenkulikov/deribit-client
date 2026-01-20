import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    DateFilterQuery,
    PriceLatestResponse,
    PriceListResponse,
    TickerQuery,
)
from app.db.crud import PriceRepository
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prices", tags=["prices"])


def parse_timestamp(date_str: Optional[str]) -> Optional[int]:
    """
    Парсинг даты из строки в UNIX timestamp.

    Поддерживает:
    - ISO 8601 формат (например, "2024-01-01T00:00:00")
    - UNIX timestamp в секундах (например, "1704067200")
    """
    if not date_str:
        return None

    try:
        # Попытка парсинга как UNIX timestamp
        return int(date_str)
    except ValueError:
        pass

    try:
        # Попытка парсинга как ISO 8601
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Use ISO 8601 or UNIX timestamp",
        )


@router.get("/all", response_model=PriceListResponse)
async def get_all_prices(
    ticker: str = Query(..., description="Тикер валюты (BTC_USD или ETH_USD)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Лимит записей"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить все сохраненные данные по указанной валюте.

    Args:
        ticker: Тикер валюты (обязательный параметр)
        limit: Максимальное количество записей
        offset: Смещение для пагинации
        db: Сессия базы данных

    Returns:
        Список всех цен для указанного тикера
    """
    # Валидация тикера
    try:
        ticker_query = TickerQuery(ticker=ticker)
        validated_ticker = ticker_query.ticker
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    repository = PriceRepository(db)
    prices = await repository.get_all_by_ticker(validated_ticker, limit=limit, offset=offset)

    return PriceListResponse(
        ticker=validated_ticker,
        count=len(prices),
        prices=prices,
    )


@router.get("/latest", response_model=PriceLatestResponse)
async def get_latest_price(
    ticker: str = Query(..., description="Тикер валюты (BTC_USD или ETH_USD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить последнюю цену валюты.

    Args:
        ticker: Тикер валюты (обязательный параметр)
        db: Сессия базы данных

    Returns:
        Последняя цена для указанного тикера
    """
    # Валидация тикера
    try:
        ticker_query = TickerQuery(ticker=ticker)
        validated_ticker = ticker_query.ticker
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    repository = PriceRepository(db)
    latest_price = await repository.get_latest_by_ticker(validated_ticker)

    return PriceLatestResponse(
        ticker=validated_ticker,
        price=latest_price,
    )


@router.get("/filter", response_model=PriceListResponse)
async def get_prices_by_date(
    ticker: str = Query(..., description="Тикер валюты (BTC_USD или ETH_USD)"),
    date: Optional[str] = Query(None, description="Конкретная дата (ISO 8601 или UNIX timestamp)"),
    start_date: Optional[str] = Query(None, description="Начальная дата (ISO 8601 или UNIX timestamp)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (ISO 8601 или UNIX timestamp)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить цены валюты с фильтром по дате.

    Args:
        ticker: Тикер валюты (обязательный параметр)
        date: Конкретная дата для фильтрации
        start_date: Начальная дата диапазона
        end_date: Конечная дата диапазона
        db: Сессия базы данных

    Returns:
        Список цен, отфильтрованных по дате
    """
    # Валидация тикера
    try:
        ticker_query = TickerQuery(ticker=ticker)
        validated_ticker = ticker_query.ticker
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Парсинг дат
    start_timestamp = None
    end_timestamp = None

    if date:
        # Если указана конкретная дата, используем её как начало и конец дня
        date_timestamp = parse_timestamp(date)
        if date_timestamp:
            # Начало дня
            start_timestamp = date_timestamp
            # Конец дня (добавляем 86400 секунд = 24 часа)
            end_timestamp = date_timestamp + 86400
    else:
        if start_date:
            start_timestamp = parse_timestamp(start_date)
        if end_date:
            end_timestamp = parse_timestamp(end_date)

        if start_timestamp and end_timestamp and start_timestamp > end_timestamp:
            raise HTTPException(
                status_code=400,
                detail="start_date must be less than or equal to end_date",
            )

    repository = PriceRepository(db)
    prices = await repository.get_by_ticker_and_date_range(
        validated_ticker,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )

    return PriceListResponse(
        ticker=validated_ticker,
        count=len(prices),
        prices=prices,
    )
