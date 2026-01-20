from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, field_serializer
from pydantic import ConfigDict


class PriceResponse(BaseModel):
    """Схема ответа с данными о цене."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    price: Decimal
    timestamp: int
    created_at: datetime

    @field_serializer('price')
    def serialize_price(self, value: Decimal) -> str:
        """Сериализация цены в строку."""
        return str(value)


class PriceListResponse(BaseModel):
    """Схема ответа со списком цен."""

    ticker: str
    count: int
    prices: List[PriceResponse]


class PriceLatestResponse(BaseModel):
    """Схема ответа с последней ценой."""

    ticker: str
    price: Optional[PriceResponse] = None


class TickerQuery(BaseModel):
    """Схема для валидации query параметра ticker."""

    ticker: str = Field(..., description="Тикер валюты (BTC_USD или ETH_USD)")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Валидация тикера."""
        valid_tickers = {"BTC_USD", "ETH_USD"}
        ticker_upper = v.upper()
        if ticker_upper not in valid_tickers:
            raise ValueError(f"Ticker must be one of {valid_tickers}")
        return ticker_upper


class DateFilterQuery(TickerQuery):
    """Схема для валидации query параметров с фильтром по дате."""

    date: Optional[str] = Field(None, description="Дата в формате ISO 8601 или UNIX timestamp")
    start_date: Optional[str] = Field(None, description="Начальная дата в формате ISO 8601 или UNIX timestamp")
    end_date: Optional[str] = Field(None, description="Конечная дата в формате ISO 8601 или UNIX timestamp")
