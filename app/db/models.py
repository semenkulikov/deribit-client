from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Price(Base):
    """Модель для хранения цен криптовалют."""

    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    price = Column(Numeric(20, 8), nullable=False)
    timestamp = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_ticker_timestamp", "ticker", "timestamp"),
    )
