# Deribit Client

Клиент для криптобиржи Deribit с периодическим получением цен BTC/USD и ETH/USD и REST API для доступа к сохраненным данным.

## Описание

Приложение состоит из следующих компонентов:

- **Клиент Deribit**: Периодически (каждую минуту) получает индексные цены BTC/USD и ETH/USD через Deribit API
- **База данных**: PostgreSQL для хранения тикера, цены и UNIX timestamp
- **Фоновая задача**: Celery с Redis брокером для периодического получения цен
- **REST API**: FastAPI с тремя эндпоинтами для доступа к данным

## Структура проекта

```
deribit-client/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение
│   ├── config.py               # Конфигурация (Pydantic Settings)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # API эндпоинты
│   │   └── schemas.py          # Pydantic схемы для валидации
│   ├── client/
│   │   ├── __init__.py
│   │   └── deribit_client.py   # aiohttp клиент для Deribit
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy модели
│   │   ├── database.py         # Подключение к БД (async)
│   │   └── crud.py             # CRUD операции
│   └── tasks/
│       ├── __init__.py
│       └── price_fetcher.py    # Celery задачи
├── celery_app.py               # Celery приложение
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_client.py
│   └── test_tasks.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

## Требования

- Python 3.12+
- PostgreSQL 15+
- Redis (для Celery брокера)
- Docker и Docker Compose (для контейнеризации)

## Установка и запуск

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd deribit-client
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Настройте переменные окружения в `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/deribit_db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
DERIBIT_API_BASE_URL=https://www.deribit.com/api/v2
```

6. Убедитесь, что PostgreSQL и Redis запущены локально.

7. Инициализируйте базу данных (таблицы создадутся автоматически при первом запуске).

8. Запустите FastAPI сервер:
```bash
uvicorn app.main:app --reload
```

9. В отдельном терминале запустите Celery worker:
```bash
# На Windows используйте -P solo для избежания проблем с multiprocessing
celery -A celery_app worker --loglevel=info -P solo

# На Linux/Mac можно использовать без -P solo
celery -A celery_app worker --loglevel=info
```

10. В еще одном терминале запустите Celery beat:
```bash
celery -A celery_app beat --loglevel=info
```

### Запуск через Docker

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd deribit-client
```

2. Создайте файл `.env` (опционально, можно использовать значения по умолчанию):
```bash
cp .env.example .env
```

3. Запустите все сервисы через Docker Compose:
```bash
cd docker
docker-compose up -d
```

4. Проверьте статус контейнеров:
```bash
docker-compose ps
```

5. Просмотрите логи:
```bash
docker-compose logs -f app
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

## API Документация

После запуска приложения API документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Эндпоинты

Все эндпоинты требуют обязательный query-параметр `ticker` (BTC_USD или ETH_USD).

#### 1. GET /api/prices/all

Получить все сохраненные данные по указанной валюте.

**Параметры:**
- `ticker` (обязательный): Тикер валюты (BTC_USD или ETH_USD)
- `limit` (опциональный): Максимальное количество записей (1-1000)
- `offset` (опциональный): Смещение для пагинации (по умолчанию 0)

**Пример запроса:**
```bash
curl "http://localhost:8000/api/prices/all?ticker=BTC_USD&limit=10"
```

**Пример ответа:**
```json
{
  "ticker": "BTC_USD",
  "count": 10,
  "prices": [
    {
      "id": 1,
      "ticker": "BTC_USD",
      "price": "45000.50",
      "timestamp": 1704067200,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

#### 2. GET /api/prices/latest

Получить последнюю цену валюты.

**Параметры:**
- `ticker` (обязательный): Тикер валюты (BTC_USD или ETH_USD)

**Пример запроса:**
```bash
curl "http://localhost:8000/api/prices/latest?ticker=BTC_USD"
```

**Пример ответа:**
```json
{
  "ticker": "BTC_USD",
  "price": {
    "id": 100,
    "ticker": "BTC_USD",
    "price": "45200.00",
    "timestamp": 1704153600,
    "created_at": "2024-01-02T00:00:00"
  }
}
```

#### 3. GET /api/prices/filter

Получить цены валюты с фильтром по дате.

**Параметры:**
- `ticker` (обязательный): Тикер валюты (BTC_USD или ETH_USD)
- `date` (опциональный): Конкретная дата в формате ISO 8601 или UNIX timestamp
- `start_date` (опциональный): Начальная дата диапазона (ISO 8601 или UNIX timestamp)
- `end_date` (опциональный): Конечная дата диапазона (ISO 8601 или UNIX timestamp)

**Примеры запросов:**
```bash
# Фильтр по конкретной дате
curl "http://localhost:8000/api/prices/filter?ticker=BTC_USD&date=2024-01-01T00:00:00"

# Фильтр по диапазону дат (UNIX timestamp)
curl "http://localhost:8000/api/prices/filter?ticker=BTC_USD&start_date=1704067200&end_date=1704153600"
```

## Тестирование

Для запуска тестов:

```bash
pytest tests/ -v
```

Для запуска с покрытием:

```bash
pytest tests/ --cov=app --cov-report=html
```
