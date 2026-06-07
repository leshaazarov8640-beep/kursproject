# Курсовая работа: Система обнаружения вторжений (IDS) на основе машинного обучения

**Вариант 3** | **Технологии:** Python + scikit-learn + Go + PCAP

**Сетевая безопасность** — модуль анализа сетевого трафика в реальном времени. Захват пакетов (Go), извлечение признаков, классификация аномалий с помощью ML-моделей (Random Forest, MLP Neural Network, Isolation Forest). Визуализация атак, алерты в Telegram/Slack.

---

## Содержание

- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Структура проекта](#структура-проекта)
- [Установка и запуск](#установка-и-запуск)
- [Использование](#использование)
- [Тестирование](#тестирование)
- [Результаты детекции](#результаты-детекции)
- [Визуализация](#визуализация)
- [API](#api)
- [Безопасность](#безопасность)

---

## Архитектура

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  Go Packet       │────>│  Python ML Core      │────>│  Визуализация    │
│  Capture Module  │     │  (scikit-learn)       │     │  (matplotlib)    │
│  (gopacket)      │     │                      │     │                  │
│                  │     │  ┌────────────────┐   │     │  feature_*.png   │
│  live/file mode  │     │  │ Random Forest  │   │     │  anomaly_*.png   │
│  BPF filter      │     │  │ MLP Neural Net │   │     │  model_*.png     │
│  Flow features   │     │  │ IsolationForest│   │     └──────────────────┘
│  JSON output     │     │  └────────────────┘   │
└──────────────────┘     │                      │     ┌──────────────────┐
                         │  Ensemble voting     │────>│  Алерты          │
                         │  (>=2 models=attack) │     │  Telegram/Slack  │
                         │                      │     │  Console         │
                         │  API (FastAPI)       │     └──────────────────┘
                         └──────────────────────┘
```

### Компоненты

**Go-модуль (захват трафика):**
- Захват пакетов из сети (live mode) или из PCAP-файла (offline)
- Извлечение признаков потоков: IP, порты, протокол, TCP-флаги, размеры пакетов, TTL, окна
- Агрегация пакетов во временные окна (по умолчанию 60 секунд)
- Вывод в JSON

**Python-модуль (ML + алерты):**
- **Feature Parser** — загрузка JSON, подготовка признаков (19 фич)
- **ML Models** — ансамбль из трёх моделей:
  - Random Forest (100 деревьев, max_depth=15)
  - MLP Neural Network (64→32 нейрона)
  - Isolation Forest (unsupervised)
- **Ensemble Voting** — аномалия если ≥2 модели согласны
- **Alert Notifier** — Telegram / Slack / Console
- **Визуализация** — 3 вида графиков (matplotlib)
- **REST API** — FastAPI (8 эндпоинтов)

---

## Технологический стек

| Технология | Назначение |
|---|---|
| **Go 1.22** | Захват и анализ пакетов (gopacket) |
| **Python 3.11** | ML-модели, API, визуализация |
| **scikit-learn** | Random Forest, MLP, Isolation Forest |
| **FastAPI + uvicorn** | REST API |
| **pandas / numpy** | Обработка данных |
| **matplotlib** | Графики и визуализация |
| **joblib** | Сохранение/загрузка моделей |
| **requests** | Telegram/Slack алерты |
| **pytest** | Тестирование |
| **Docker** | Контейнеризация |

---

## Структура проекта

```
ids-project/
├── go-pcap/                      # Go-модуль захвата трафика
│   ├── capture/capture.go        # Захват пакетов (live + pcap)
│   ├── features/extract.go       # Извлечение признаков потоков
│   ├── output/output.go          # Вывод результатов (JSON/stdout)
│   ├── main.go                   # CLI-точка входа
│   ├── go.mod / go.sum           # Go-зависимости
│   └── output/                   # Директория вывода JSON
│
├── python-ml/                    # Python-модуль ML + алерты
│   ├── main.py                   # CLI + FastAPI точка входа
│   ├── features/parser.py        # Загрузка и подготовка признаков
│   ├── model/train.py            # Обучение моделей (3 модели)
│   ├── model/predict.py          # Предсказание + ensemble voting
│   ├── alerts/notifier.py        # Telegram / Slack / Console алерты
│   ├── visualization/dashboard.py# Графики (matplotlib)
│   ├── verify.py                 # Скрипт проверки (10 потоков)
│   ├── requirements.txt          # Python-зависимости
│   ├── models/                   # Сохранённые .pkl модели
│   ├── visualizations/           # Сгенерированные графики
│   ├── verify_results/           # Результаты верификации
│   └── tests/                    # 45 тестов (pytest)
│       ├── test_model.py         # 5 тестов (обучение, предсказание)
│       ├── test_parser.py        # 15 тестов (парсер признаков)
│       ├── test_alerts.py        # 9 тестов (алерты)
│       ├── test_visualization.py # 6 тестов (графики)
│       └── test_integration.py   # 10 тестов (полный цикл)
│
├── bin/ids-pcap.exe              # Предсобранный Go-бинарник
├── scripts/run.ps1               # PowerShell-скрипт запуска
├── docker-compose.yml            # Docker Compose
├── Dockerfile.go                 # Dockerfile для Go-модуля
├── Dockerfile.python             # Dockerfile для Python-модуля
├── .gitignore
└── README.md
```

---

## Установка и запуск

### Локальный запуск (Python)

```bash
cd python-ml
pip install -r requirements.txt

# Обучение моделей
python main.py train --samples 200

# Проверка на 10 тестовых потоках
python verify.py

# Запуск API-сервера
python main.py api --host 0.0.0.0 --port 8000
```

### Запуск Go-модуля

```bash
cd go-pcap
go mod tidy
go build -o ../bin/ids-pcap.exe .

# Просмотр интерфейсов
./bin/ids-pcap.exe --list

# Захват из PCAP-файла
./bin/ids-pcap.exe --mode file --file traffic.pcap --output features.json

# Live-захват
./bin/ids-pcap.exe --mode live --interface eth0 --filter "tcp port 80"
```

### Docker Compose

```bash
docker compose up --build
```

---

## Использование

### CLI-команды

```bash
# Обучение
python main.py train --samples 300 --model-dir models

# Предсказание (из файла)
python main.py predict --file test_data.json

# Предсказание (из stdin)
cat flows.json | python main.py predict

# Анализ с сохранением
python main.py analyze flows.json --output results.json

# API-сервер
python main.py api --host 0.0.0.0 --port 8000
```

### Алерты

```bash
# Telegram
python main.py --telegram-token TOKEN --telegram-chat-id CHAT_ID predict --file data.json

# Slack
python main.py --slack-webhook URL predict --file data.json
```

---

## Тестирование

```bash
cd python-ml
pytest tests/ -v
```

**Результат:** 45 тестов, 0 ошибок, 0 предупреждений

| Файл | Тестов | Проверяет |
|---|---|---|
| `tests/test_model.py` | 5 | Генерация данных, обучение, предсказание |
| `tests/test_parser.py` | 15 | Загрузка JSON/stdin, кодирование протоколов, missing columns |
| `tests/test_alerts.py` | 9 | Форматирование алертов, Telegram/Slack без токена |
| `tests/test_visualization.py` | 6 | Создание директории, 3 вида графиков, empty data |
| `tests/test_integration.py` | 10 | Полный pipeline, ensemble voting, структура результата |

---

## Результаты детекции

### Тестовые потоки (10 шт: 6 норма + 4 атаки)

```
Тип трафика                Статус     Оценка    RF    MLP   IF
--------------------------------------------------------------
1. HTTP (веб-сёрфинг)      НОРМА     0.0847    НЕТ   НЕТ   НЕТ
2. HTTPS (защищённый сайт) НОРМА     0.1322    НЕТ   НЕТ   ДА
3. SSH (удалённый доступ)  НОРМА     0.1253    НЕТ   НЕТ   НЕТ
4. DNS (запросы имён)      НОРМА     0.1624    НЕТ   НЕТ   НЕТ
5. FTP (скачивание файла)  НОРМА     0.1229    НЕТ   НЕТ   ДА
6. SMTP (отправка почты)   НОРМА     0.1296    НЕТ   НЕТ   НЕТ
7. SYN-FLOOD (атака)       АНОМАЛИЯ  0.7888    ДА   ДА    НЕТ   <<<
8. PORT SCAN (атака)       АНОМАЛИЯ  0.7697    ДА   ДА    НЕТ   <<<
9. DDoS (атака)            АНОМАЛИЯ  0.9537    ДА   ДА    ДА    <<<
10. DNS Amplification      АНОМАЛИЯ  0.4198    ДА   НЕТ   ДА    <<<

Итого: 6 норма / 4 аномалия
```

### Точность моделей

| Модель | Точность |
|---|---|
| Random Forest | 100.00% |
| MLP Neural Network | 100.00% |
| Isolation Forest | 59.58% |

### Тренировочные данные (6 типов трафика)

**Норма:** HTTP, HTTPS, SSH, DNS, FTP, SMTP
**Аномалии:** SYN Flood, Port Scan, DDoS, DNS Amplification

---

## Визуализация

Графики генерируются автоматически после `verify.py` или через API:

| График | Описание |
|---|---|
| `feature_comparison.png` | Сравнение ключевых признаков по потокам |
| `anomaly_scores.png` | Оценка аномальности + распределение (pie) |
| `model_comparison.png` | Сравнение трёх моделей |

Графики сохраняются в `python-ml/visualizations/`.

---

## API

Сервер запускается командой `python main.py api`.

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | Информация о сервисе |
| `GET` | `/health` | Health-check |
| `POST` | `/predict` | Классификация потоков трафика |
| `GET` | `/history` | История запросов |
| `GET` | `/history/{id}` | Конкретный запрос |
| `POST` | `/train` | Переобучить модели |
| `GET` | `/visualize` | Сгенерировать графики |
| `GET` | `/model` | Информация о моделях |
| `GET` | `/stats` | Статистика детектирования |
| `POST` | `/clear-history` | Очистить историю |

---

## Сравнение с аналогами

| Решение | Язык | ML | Бесплатно | Свой код |
|---|---|---|---|---|
| **Snort** | C | Правила | ✅ | ❌ |
| **Suricata** | C | + | ✅ | ❌ |
| **Zeek** | C++ | - | ✅ | ❌ |
| **Данный проект** | Go + Python | ✅ | ✅ | ✅ |

Ключевое отличие — полностью собственный код на Go и Python с ML-моделями, открытая архитектура.

---

## Состав репозитория

| Файл/каталог | Назначение |
|---|---|
| `go-pcap/` | Go-модуль захвата и анализа пакетов |
| `python-ml/` | Python-модуль: ML, алерты, визуализация, API |
| `python-ml/tests/` | 45 тестов (pytest) |
| `python-ml/models/` | Сохранённые ML-модели (.pkl) |
| `python-ml/visualizations/` | Сгенерированные графики |
| `scripts/` | Скрипты автоматизации |
| `bin/` | Предсобранный Go-бинарник |
| `Dockerfile.*` | Docker-образы |
| `docker-compose.yml` | Оркестрация контейнеров |
| `.gitignore` | Исключённые файлы |

---

**Разработчик:** Студент, группа 221331, Вариант 3
