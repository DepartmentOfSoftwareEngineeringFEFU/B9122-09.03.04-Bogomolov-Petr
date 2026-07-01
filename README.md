# School Manager

Система управления школой: расписание, замены, успеваемость.
Веб-интерфейс (Django) + Telegram бот + REST API.

## Стек

- Python 3.11+, Django 5+, Django REST Framework
- SQLite
- python-telegram-bot 20.x

## Быстрый запуск

```powershell
# 1. Клонировать и перейти в папку
git clone <repo-url>
cd school-manager

# 2. Создать .env из шаблона
cp .env.example .env

# 3. Создать виртуальное окружение и установить зависимости
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt -r bot\requirements.txt

# 4. Миграции БД
python backend\manage.py migrate

# 5. Загрузить тестовые данные
python backend\scripts\seed_data.py

# 6. Запустить сервер
python backend\manage.py runserver
```

Открыть http://localhost:8000

## Тестовые учётные записи

### Веб-интерфейс

| Роль | Логин | Пароль | ФИО |
|------|-------|--------|-----|
| Администратор | `admin` | `admin` | Иванов Иван Иванович |
| Преподаватель | `ivanova` | `teacher1` | Иванова Мария Петровна |
| Преподаватель | `petrov` | `teacher2` | Петров Сергей Владимирович |
| Учащийся | `alekseev` | `student` | Алексеев Дмитрий (10А) |
| Учащийся | `belova` | `student` | Белова Анна (10А) |
| Учащийся | `vasilev` | `student` | Васильев Иван (10А) |
| Учащийся | `grigorev` | `student` | Григорьев Максим (10Б) |
| Учащийся | `dmitrieva` | `student` | Дмитриева Ольга (10Б) |
| Учащийся | `egorov` | `student` | Егоров Артём (10Б) |

### Telegram бот

Чтобы привязать Telegram ID к пользователю:
1. Найди в Боте свой `chat_id` (бот напишет его при `/start`)
2. Через админ-панель `/admin/` → Пользователи → выбери пользователя → укажи Telegram ID

Либо через API:

```bash
curl -X PATCH -u admin:admin \
  http://localhost:8000/api/users/1/link_telegram/ \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789}'
```

## Запуск Telegram бота

В `.env` укажи `TELEGRAM_BOT_TOKEN` и запусти:

```powershell
python bot\bot.py
```

Команды бота:

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/my_schedule` | Моё расписание |
| `/my_grades` | Мои оценки |
| `/substitutions` | Замены (админ) |
| `/reports` | Отчёты (админ) |
| `/schedule` | Управление расписанием (админ) |
| `/users` | Пользователи (админ) |
| `/grade` | Выставление оценок (преподаватель) |

## Структура проекта

```
school-manager/
├── backend/                     # Django проект
│   ├── config/                  # Настройки, urls, wsgi/asgi
│   ├── accounts/                # Пользователи (кастомная модель User)
│   ├── school/                  # Классы и дисциплины
│   ├── schedule/                # Расписание + генератор (CSP solver)
│   ├── substitutions/           # Замены преподавателей
│   ├── grades/                  # Оценки учащихся
│   ├── reports/                 # Отчёты (нагрузка, успеваемость и т.д.)
│   ├── templates/               # HTML-шаблоны (admin, teacher, student)
│   └── scripts/seed_data.py     # Заполнение тестовыми данными
├── bot/                         # Telegram бот
│   ├── bot.py                   # Точка входа
│   ├── api_client.py            # Клиент REST API
│   ├── keyboards.py             # Клавиатуры
│   └── handlers/                # Обработчики команд
├── docs/                        # Диаграммы
├── .env.example                 # Шаблон конфигурации
└── start.ps1                    # Скрипт запуска (Windows)
```

## API Endpoints

Все эндпоинты требуют аутентификацию (Basic Auth или сессия).

| Метод | Endpoint | Описание |
|-------|----------|---------|
| GET | `/api/users/` | Список пользователей |
| POST | `/api/users/` | Создать пользователя (админ) |
| GET | `/api/users/{id}/` | Детали пользователя |
| PATCH | `/api/users/{id}/link_telegram/` | Привязать Telegram ID |
| GET | `/api/classes/` | Список классов |
| GET | `/api/subjects/` | Список дисциплин |
| GET | `/api/lessons/` | Расписание занятий |
| GET | `/api/grades/` | Оценки |
| GET | `/api/substitutions/` | Замены |
| GET | `/api/reports/workload/` | Отчёт по нагрузке (админ) |
| GET | `/api/reports/grades/` | Отчёт по оценкам (админ) |
| GET | `/api/reports/substitutions/` | Отчёт по заменам (админ) |
| GET | `/api/reports/attendance/` | Отчёт по посещаемости (админ) |

## Веб-интерфейс

| URL | Доступ | Описание |
|-----|--------|----------|
| `/login/` | Все | Вход |
| `/` | Все | Дашборд (разный для каждой роли) |
| `/admin/users/` | Админ | Управление пользователями |
| `/admin/classes/` | Админ | Классы |
| `/admin/schedule/` | Админ | Расписание |
| `/admin/schedule/generate/` | Админ | Авто-генерация расписания |
| `/admin/substitutions/` | Админ | Замены (подтверждение/отказ) |
| `/admin/reports/` | Админ | Отчёты |
| `/teacher/grades/` | Преподаватель | Оценки |
| `/teacher/grades/add/` | Преподаватель | Выставить оценку |
| `/teacher/substitution/request/` | Преподаватель | Запросить замену |
| `/student/schedule/` | Учащийся | Расписание |
| `/student/grades/` | Учащийся | Оценки |
| `/profile/` | Все | Редактирование профиля |
| `/admin/` | Админ | Django admin |

## Генератор расписания

Алгоритм в `backend/schedule/solver.py` использует CSP (Constraint Satisfaction Problem):
- C1: преподаватель не может вести два занятия одновременно
- C2: класс не может быть на двух занятиях одновременно
- C3: аудитория не может использоваться одновременно
- C4–C7: дополнительные ограничения

Запуск генерации: `/admin/schedule/generate/` (веб) или через API.
