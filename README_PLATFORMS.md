# 🌐 Руководство по платформам Tax Lien Scraper

## 📚 Оглавление
1. [Обзор](#обзор)
2. [Существующие платформы](#существующие-платформы)
3. [Новые платформы](#новые-платформы)
4. [Быстрый старт](#быстрый-старт)
5. [Конфигурация](#конфигурация)

---

## 🔍 Обзор

Tax Lien Scraper поддерживает множество платформ для сбора данных о налоговых залогах и недвижимости.

**Архитектура:**
```
taxlien-scraper-python/
├── celery_app.py          # Celery application
├── functions.py           # Общие функции
├── tasks.py              # Celery tasks и chains
└── platforms/            # Платформы
    ├── qpublic/         # ✅ QPublic (Schneider Corp)
    ├── beacon/          # 🆕 Beacon (расширение QPublic)
    ├── tyler_technologies/ # 🆕 Tyler Tech (iasWorld)
    └── bid4assets/      # 🆕 Аукционная платформа
```

---

## ✅ Существующие платформы

### 1. QPublic (Schneider Corp)
**Статус:** ✅ Работает  
**Округа:** 3 (Dixie, Alachua, Clay - Florida)  
**Метод:** LOOP (кнопка Next)

**Запуск:**
```python
from tasks import qpublic_main_chain
qpublic_main_chain.apply_async()
```

**Конфигурация:**
```python
# platforms/qpublic/qpublic_functions.py
# Добавить новый округ:
config_new_county = {
    'county': 'new_county_fl',
    'url': 'https://qpublic.schneidercorp.com/...',
    'start_parcel': '...',
}
```

---

### 2. GIS Property Appraiser (floridapa.com)
**Статус:** ✅ Работает  
**Округа:** 6 (Bradford, Columbia, Lafayette, Okeechobee, Suwannee, Union)  
**Метод:** LOOP через iframe

**Особенности:**
- Использует iframe: `recordSearchContent_1_iframe`
- Навигация через кнопки Next/Prev
- PIN-based идентификация

---

### 3. GovernMax Tax Collector
**Статус:** ✅ Работает  
**Округа:** 1 (Dixie - Florida)  
**Метод:** CSV file input

---

## 🆕 Новые платформы

### 1. Beacon by Schneider ⭐
**Статус:** 🆕 Готов к тестированию  
**Файл:** `platforms/beacon/beacon_functions.py`  
**Потенциал:** 300+ округов по США

**Преимущества:**
- Похож на QPublic (легкая адаптация)
- Больше данных на страницу
- Крупные округа (Maricopa AZ, King WA, etc.)

**Запуск:**
```python
from platforms.beacon.beacon_functions import (
    beacon_scrape_counties_urls_task,
    beacon_get_all_parcels_urls_task,
    beacon_parse_single_html_task,
    BEACON_CONFIGS
)

# Пример для Maricopa County, AZ
config = BEACON_CONFIGS['maricopa_county_az']
counties = beacon_scrape_counties_urls_task.apply_async(
    args=[config['base_url']]
).get()

parcels = beacon_get_all_parcels_urls_task.apply_async(
    args=[counties]
).get()
```

**Доступные округа:**
```python
BEACON_CONFIGS = {
    'maricopa_county_az': {...},      # Phoenix, 4.5M pop
    'king_county_wa': {...},          # Seattle, 2.3M pop
    'hillsborough_county_fl': {...},  # Tampa, 1.5M pop
    'pinellas_county_fl': {...},      # St. Pete, 980K pop
}
```

---

### 2. Tyler Technologies (iasWorld) ⭐⭐⭐
**Статус:** 🆕 Готов к тестированию  
**Файл:** `platforms/tyler_technologies/tyler_functions.py`  
**Потенциал:** 1000+ округов по США

**Преимущества:**
- Крупнейший vendor (10,000+ муниципалитетов)
- Богатые данные (50+ полей)
- Texas, North Carolina, Arizona и др.

**Запуск:**
```python
from platforms.tyler_technologies.tyler_functions import (
    tyler_search_by_criteria,
    tyler_parse_single_html_task,
    tyler_scrape_all_parcels_by_letter,
    TYLER_CONFIGS
)

# Пример для Harris County, TX
config = TYLER_CONFIGS['harris_county_tx']

# Поиск по критериям
parcels = tyler_search_by_criteria.apply_async(
    args=[config['search_url'], {'owner_name': 'Smith'}]
).get()

# Или полный сбор по буквам (A-Z)
all_parcels = tyler_scrape_all_parcels_by_letter.apply_async(
    args=[config['search_url'], config['county']]
).get()
```

**Доступные округа:**
```python
TYLER_CONFIGS = {
    'harris_county_tx': {...},   # Houston, 4.7M pop
    'wake_county_nc': {...},     # Raleigh, 1.1M pop
    'pima_county_az': {...},     # Tucson, 1M pop
}
```

**Особенности:**
- ASPX ViewState handling
- Поиск по owner name, address, parcel
- Batch scraping (A-Z)

---

### 3. Bid4Assets 💎
**Статус:** 🆕 Готов к тестированию  
**Файл:** `platforms/bid4assets/bid4assets_functions.py`  
**Потенциал:** 1500+ муниципалитетов

**Преимущества:**
- Аукционные данные в реальном времени
- Календарь предстоящих аукционов
- Bidding информация
- Property details + images

**Запуск:**
```python
from platforms.bid4assets.bid4assets_functions import (
    bid4assets_get_auction_calendar,
    bid4assets_scrape_full_auction
)

# 1. Получить календарь аукционов
calendar = bid4assets_get_auction_calendar.apply_async().get()

# 2. Выбрать аукцион
auction_url = calendar['Florida']['Miami-Dade']['auction_url']

# 3. Скрапить весь аукцион
result = bid4assets_scrape_full_auction.apply_async(
    args=[auction_url, 'miami_dade_fl']
).get()

print(f"Scraped {result['total_properties']} properties")
```

**Собираемые данные:**
- Current bid / Opening bid
- Number of bidders
- Auction end time
- Property details (photos, legal description)
- Tax information
- Redemption period

---

## 🚀 Быстрый старт

### Установка

1. **Установить зависимости:**
```bash
cd taxlien-scraper-python
pip install -r requirements.txt
```

2. **Запустить Redis:**
```bash
redis-server
```

3. **Запустить Celery worker:**
```bash
celery -A celery_app worker --loglevel=info
```

4. **Запустить Celery beat (для периодических задач):**
```bash
celery -A celery_app beat --loglevel=info
```

5. **Flower (мониторинг):**
```bash
celery -A celery_app flower
# Открыть http://localhost:5555
```

---

### Тестирование новой платформы

#### Пример: Beacon (Maricopa County, AZ)

```python
# test_beacon.py
from platforms.beacon.beacon_functions import (
    beacon_scrape_counties_urls_task,
    beacon_parse_single_html_task
)
from functions import scrape_single_url

# 1. Тест парсинга одной страницы
test_url = "https://mcassessor.maricopa.gov/..."
html = scrape_single_url(test_url)
data = beacon_parse_single_html_task(html)

print(f"Parcel ID: {data.get('parcel_id')}")
print(f"Owner: {data.get('owner')}")
print(f"Assessed Value: {data.get('assessed_value')}")

# 2. Тест получения списка округов
base_url = "https://mcassessor.maricopa.gov"
counties = beacon_scrape_counties_urls_task.apply_async(
    args=[base_url]
).get()

print(f"Found {len(counties)} counties")
```

**Запуск:**
```bash
python test_beacon.py
```

---

### Добавление нового округа

#### Шаг 1: Найти URL pattern
```python
# Пример для нового QPublic округа
# URL: https://qpublic.schneidercorp.com/Application.aspx?AppID=999&LayerID=...

# Определить:
# - AppID
# - LayerID
# - PageTypeID
# - PageID
```

#### Шаг 2: Создать конфигурацию
```python
# platforms/qpublic/qpublic_functions.py

config_new_county_fl = {
    'county': 'new_county_fl',
    'results_path': '../../taxlien_db/res/parcel_new_county_fl/',
    'url': lambda id: f'https://qpublic.schneidercorp.com/Application.aspx?AppID=999&KeyValue={id}',
    'start': '00-00-00-0000-0000-0000',
    'next_button_selectors': ["#ToolBar1_btnNextRecord > span"],
    'parcel_text_selectors': ["#ctlBodyPane_ctl00_ctl01_lblParcelID"],
    'agree_button_selectors': ['#appBody > div.modal.in > div > div > div.modal-focus-target > div.modal-footer > a.btn.btn-primary.button-1'],
}
```

#### Шаг 3: Добавить в tasks.py
```python
# tasks.py

@app.task
def new_county_chain():
    url = get_platforms_urls()["qpublic"]
    counties_urls = {"New County": "https://..."}
    
    all_parcels_urls = qpublic_get_all_parcels_urls_task.s(
        counties_urls
    ).apply_async().get()
    
    group(qpublic_single_url_chain.s(url) for url in all_parcels_urls)()
```

#### Шаг 4: Тестировать
```bash
python run_test_qpublic_chain.py
```

---

## ⚙️ Конфигурация

### Celery Settings

```python
# celery_app.py

app.conf.update(
    timezone='Europe/Moscow',
    enable_utc=True,
    result_backend='redis://localhost:6379/0',
    result_expires=3600 * 24 * 30,  # 30 days
    task_annotations={
        '*': {'rate_limit': '5/m'}  # 5 tasks per minute
    }
)
```

**Изменить rate limit:**
```python
# Для более быстрого скрапинга
task_annotations={'*': {'rate_limit': '20/m'}}

# Для более медленного (избежать бана)
task_annotations={'*': {'rate_limit': '2/m'}}
```

---

### Proxy Configuration

```python
# functions.py

def scrape_single_url(url: str, proxy: dict = None):
    if proxy is None:
        proxy = {'host': 'socks5://localhost', 'port': '10808'}
    
    # ... использовать proxy
```

**Ротация прокси:**
```python
PROXY_POOL = [
    {'host': 'socks5://localhost', 'port': '10808'},
    {'host': 'socks5://localhost', 'port': '10809'},
    {'host': 'socks5://localhost', 'port': '10810'},
]

import random
proxy = random.choice(PROXY_POOL)
```

---

### Storage Configuration

```python
# functions.py

# Изменить путь сохранения
STORAGE_BASE = './storage'  # default
STORAGE_BASE = '/mnt/data/taxlien'  # custom

def save_html(html: str, platform: str, name: str) -> str:
    file_path = f'{STORAGE_BASE}/{platform}/{name}.html'
    # ...
```

---

## 📊 Мониторинг

### Flower Dashboard
```bash
celery -A celery_app flower
# http://localhost:5555
```

**Возможности:**
- Активные задачи
- Завершенные задачи
- Failed tasks
- Workers status
- Task stats

---

### Logs

```python
# tasks.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="tasks.log",
    filemode="a"
)

logger = logging.getLogger(__name__)
logger.info("Task started")
logger.error("Task failed", exc_info=True)
```

**Просмотр логов:**
```bash
tail -f tasks.log
```

---

### Database Stats

```sql
-- Количество properties по платформам
SELECT data_source, COUNT(*) as count
FROM properties
GROUP BY data_source;

-- Количество по штатам
SELECT state, COUNT(*) as count
FROM properties
GROUP BY state
ORDER BY count DESC;

-- Последние scraped
SELECT data_source, MAX(last_scraped) as last_run
FROM properties
GROUP BY data_source;
```

---

## 🐛 Troubleshooting

### Проблема: Cloudflare блокирует
**Решение:**
```python
# Увеличить задержку
scraper_pass_challenge(sb)
sb.sleep(5)  # вместо 2

# Использовать undetected-chromedriver
with SB(uc=True, headless=False) as sb:
    ...
```

---

### Проблема: Элементы не находятся
**Решение:**
```python
# Увеличить timeout
element = sb.find_element(selector, timeout=60)

# Попробовать разные селекторы
selectors = [
    "#element1",
    ".element-class",
    "xpath://div[@id='element']"
]

for selector in selectors:
    try:
        element = sb.find_element(selector)
        break
    except:
        continue
```

---

### Проблема: Задачи не выполняются
**Проверить:**
```bash
# Redis работает?
redis-cli ping
# Должно вернуть: PONG

# Celery workers запущены?
celery -A celery_app inspect active

# Очередь задач
celery -A celery_app inspect reserved
```

---

## 📚 Дополнительные ресурсы

- [PLATFORM_ANALYSIS.md](../PLATFORM_ANALYSIS.md) - Анализ всех платформ
- [DATABASE_SCHEMA_EXTENDED.sql](../DATABASE_SCHEMA_EXTENDED.sql) - Схема БД
- [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md) - Дорожная карта

---

## 🤝 Contributing

При добавлении новой платформы:

1. Создать папку `platforms/new_platform/`
2. Добавить `__init__.py` и `new_platform_functions.py`
3. Реализовать минимум 3 функции:
   - `scrape_counties_urls_task()`
   - `get_all_parcels_urls_task()`
   - `parse_single_html_task()`
4. Добавить конфигурации
5. Обновить этот README
6. Написать тесты

---

**Последнее обновление:** 17 октября 2025  
**Версия:** 2.0

