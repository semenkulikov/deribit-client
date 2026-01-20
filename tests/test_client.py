import pytest
from unittest.mock import AsyncMock, patch
from aiohttp import ClientResponse

from app.client.deribit_client import DeribitClient


@pytest.mark.asyncio
async def test_get_index_price_success():
    """Тест успешного получения цены."""
    client = DeribitClient()
    mock_response_data = {
        "jsonrpc": "2.0",
        "result": {
            "index_price": 45000.50,
            "index_name": "BTC_USD",
        },
        "usIn": 1234567890,
        "usOut": 1234567891,
        "usDiff": 1,
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        price = await client.get_index_price("BTC_USD")

        assert price == 45000.50
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_index_price_not_found():
    """Тест случая, когда цена не найдена в ответе."""
    client = DeribitClient()
    mock_response_data = {
        "jsonrpc": "2.0",
        "result": {},
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        price = await client.get_index_price("BTC_USD")

        assert price is None


@pytest.mark.asyncio
async def test_get_index_price_http_error():
    """Тест обработки HTTP ошибки."""
    client = DeribitClient()

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        price = await client.get_index_price("BTC_USD")

        assert price is None


@pytest.mark.asyncio
async def test_get_index_price_client_error():
    """Тест обработки ошибки клиента."""
    client = DeribitClient()

    with patch("aiohttp.ClientSession.get", side_effect=Exception("Connection error")):
        price = await client.get_index_price("BTC_USD")

        assert price is None
