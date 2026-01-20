import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import time

from app.tasks.price_fetcher import fetch_and_save_prices
from app.client.deribit_client import DeribitClient


@pytest.fixture
def mock_db_session():
    """Мок сессии БД."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_price_repository(mock_db_session):
    """Мок репозитория цен."""
    repository = MagicMock()
    repository.create = AsyncMock()
    return repository


@patch("app.tasks.price_fetcher.create_session_maker")
@patch("app.tasks.price_fetcher.PriceRepository")
@patch("app.tasks.price_fetcher.DeribitClient")
def test_fetch_and_save_prices_success(
    mock_client_class,
    mock_repository_class,
    mock_create_session_maker,
    mock_db_session,
    mock_price_repository,
):
    """Тест успешного получения и сохранения цен."""
    # Настройка моков
    mock_client = MagicMock()
    mock_client.get_index_price = AsyncMock(side_effect=[45000.50, 2500.25])
    mock_client_class.return_value = mock_client

    # Мокируем sessionmaker и его вызов как async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_db_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_session_maker = MagicMock(return_value=mock_context_manager)
    mock_create_session_maker.return_value = mock_session_maker
    mock_repository_class.return_value = mock_price_repository

    # Выполнение задачи
    result = fetch_and_save_prices()

    # Проверки
    assert "success" in result
    assert "failed" in result
    assert len(result["success"]) == 2
    assert len(result["failed"]) == 0
    assert mock_client.get_index_price.call_count == 2


@patch("app.tasks.price_fetcher.create_session_maker")
@patch("app.tasks.price_fetcher.PriceRepository")
@patch("app.tasks.price_fetcher.DeribitClient")
def test_fetch_and_save_prices_partial_failure(
    mock_client_class,
    mock_repository_class,
    mock_create_session_maker,
    mock_db_session,
    mock_price_repository,
):
    """Тест частичного сбоя при получении цен."""
    # Настройка моков
    mock_client = MagicMock()
    mock_client.get_index_price = AsyncMock(side_effect=[45000.50, None])
    mock_client_class.return_value = mock_client

    # Мокируем sessionmaker и его вызов как async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_db_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_session_maker = MagicMock(return_value=mock_context_manager)
    mock_create_session_maker.return_value = mock_session_maker
    mock_repository_class.return_value = mock_price_repository

    # Выполнение задачи
    result = fetch_and_save_prices()

    # Проверки
    assert len(result["success"]) == 1
    assert len(result["failed"]) == 1
    assert result["failed"][0]["ticker"] in ["BTC_USD", "ETH_USD"]


@patch("app.tasks.price_fetcher.create_session_maker")
@patch("app.tasks.price_fetcher.PriceRepository")
@patch("app.tasks.price_fetcher.DeribitClient")
def test_fetch_and_save_prices_client_error(
    mock_client_class,
    mock_repository_class,
    mock_create_session_maker,
    mock_db_session,
    mock_price_repository,
):
    """Тест обработки ошибки клиента."""
    # Настройка моков
    mock_client = MagicMock()
    mock_client.get_index_price = AsyncMock(side_effect=Exception("API Error"))
    mock_client_class.return_value = mock_client

    # Мокируем sessionmaker и его вызов как async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_db_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_session_maker = MagicMock(return_value=mock_context_manager)
    mock_create_session_maker.return_value = mock_session_maker
    mock_repository_class.return_value = mock_price_repository

    # Выполнение задачи
    result = fetch_and_save_prices()

    # Проверки
    assert len(result["failed"]) >= 1
