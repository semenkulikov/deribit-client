import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.db.models import Base, Price
from app.db.database import get_db


# Тестовая база данных
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/deribit_test_db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Переопределение зависимости get_db для тестов."""
    from tests.test_api import _test_db_session
    yield _test_db_session


# Глобальная переменная для хранения сессии из фикстуры
_test_db_session = None

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Фикстура для создания тестовой сессии БД."""
    global _test_db_session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        _test_db_session = session
        yield session
        _test_db_session = None

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Фикстура для создания тестового клиента."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_prices(db_session):
    """Фикстура для создания тестовых данных."""
    now = int(datetime.now().timestamp())
    prices = [
        Price(
            ticker="BTC_USD",
            price=Decimal("45000.50"),
            timestamp=now - 120,
            created_at=datetime.utcnow() - timedelta(minutes=2),
        ),
        Price(
            ticker="BTC_USD",
            price=Decimal("45100.75"),
            timestamp=now - 60,
            created_at=datetime.utcnow() - timedelta(minutes=1),
        ),
        Price(
            ticker="BTC_USD",
            price=Decimal("45200.00"),
            timestamp=now,
            created_at=datetime.utcnow(),
        ),
        Price(
            ticker="ETH_USD",
            price=Decimal("2500.25"),
            timestamp=now,
            created_at=datetime.utcnow(),
        ),
    ]
    db_session.add_all(prices)
    await db_session.commit()
    return prices


@pytest.mark.asyncio
async def test_get_all_prices(client, db_session, sample_prices):
    """Тест получения всех цен."""
    response = await client.get("/api/prices/all?ticker=BTC_USD")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "BTC_USD"
    assert data["count"] == 3
    assert len(data["prices"]) == 3


@pytest.mark.asyncio
async def test_get_all_prices_invalid_ticker(client):
    """Тест получения всех цен с невалидным тикером."""
    response = await client.get("/api/prices/all?ticker=INVALID")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_latest_price(client, db_session, sample_prices):
    """Тест получения последней цены."""
    response = await client.get("/api/prices/latest?ticker=BTC_USD")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "BTC_USD"
    assert data["price"] is not None
    assert float(data["price"]["price"]) == 45200.00


@pytest.mark.asyncio
async def test_get_latest_price_not_found(client, db_session):
    """Тест получения последней цены, когда данных нет."""
    response = await client.get("/api/prices/latest?ticker=BTC_USD")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "BTC_USD"
    assert data["price"] is None


@pytest.mark.asyncio
async def test_get_prices_by_date(client, db_session, sample_prices):
    """Тест получения цен с фильтром по дате."""
    now = int(datetime.now().timestamp())
    start_timestamp = now - 90
    response = await client.get(
        f"/api/prices/filter?ticker=BTC_USD&start_date={start_timestamp}&end_date={now}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "BTC_USD"
    assert data["count"] >= 1


@pytest.mark.asyncio
async def test_get_prices_by_date_invalid_format(client):
    """Тест получения цен с невалидным форматом даты."""
    response = await client.get("/api/prices/filter?ticker=BTC_USD&date=invalid-date")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_prices_by_date_invalid_range(client):
    """Тест получения цен с невалидным диапазоном дат."""
    now = int(datetime.now().timestamp())
    start_timestamp = now + 100
    end_timestamp = now
    response = await client.get(
        f"/api/prices/filter?ticker=BTC_USD&start_date={start_timestamp}&end_date={end_timestamp}"
    )
    assert response.status_code == 400
