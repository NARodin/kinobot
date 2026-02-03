# Кинобот для Telegram

Telegram-бот для поиска фильмов по настроению: комедия, триллер, драма, случайный фильм и поиск по названию. Данные с API КиноПоиска (kinopoisk.dev), история запросов сохраняется в SQLite.

## Возможности

- **Настроение** — 3 случайных фильма из топа жанра (комедия, триллер, драма): постер, название, описание, рейтинг.
- **Случайный фильм** — один фильм из базы.
- **Поиск по названию** — до 3 результатов по запросу.
- **Подробнее** — актёры, режиссёр, длительность.
- После выдачи фильмов или «Подробнее» бот показывает меню с кнопками снова.

## Стек

- Python 3.10+
- python-telegram-bot, httpx, python-dotenv
- API [kinopoisk.dev](https://kinopoisk.dev/) (v1.4)
- SQLite

## Структура проекта

```
кинобот/
├── .env.example
├── README.md
├── requirements.txt
├── config.py
├── main.py
├── bot/
│   ├── handlers.py
│   └── keyboards.py
├── kinopoisk/
│   └── client.py
└── db/
    └── database.py
```

## Установка и запуск

1. **Клонируй репозиторий** (или открой папку проекта).

2. **Виртуальное окружение:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Переменные окружения:**  
   Скопируй `.env.example` в `.env` и заполни:
   ```
   TELEGRAM_BOT_TOKEN=токен_от_BotFather
   KINOPOISK_API_KEY=ключ_с_kinopoisk.dev
   ```

5. **Запуск:**
   ```bash
   python main.py
   ```

Токен Telegram: [@BotFather](https://t.me/BotFather) → `/newbot`.  
Ключ КиноПоиска: [kinopoisk.dev](https://kinopoisk.dev/).

## Как залить проект на Git

1. **Убедись, что секреты не попадут в репозиторий**  
   В корне проекта должен быть файл **`.gitignore`** (он уже добавлен в репозиторий). В нём обязательно есть строка `.env` — так твой токен и ключ API не окажутся на GitHub/GitLab.

2. **Инициализируй репозиторий** (если ещё не инициализирован):
   ```bash
   cd "c:\Users\shurf\Desktop\вк тимс боты\кинобот"
   git init
   ```

3. **Добавь файлы и первый коммит:**
   ```bash
   git add .
   git status
   ```
   Проверь, что в списке **нет** файла `.env`. Если он есть — значит `.gitignore` не сработал или его нет; не коммить `.env`.
   ```bash
   git commit -m "Кинобот: поиск фильмов по настроению, случайный, поиск по названию, история в SQLite"
   ```

4. **Создай репозиторий на GitHub (или GitLab/Bitbucket):**
   - Зайди на [github.com](https://github.com) → New repository.
   - Имя, например, `kinobot`. Не добавляй README, .gitignore или лицензию — они уже есть локально.

5. **Подключи remote и запушь:**
   ```bash
   git remote add origin https://github.com/ТВОЙ_ЛОГИН/kinobot.git
   git branch -M main
   git push -u origin main
   ```
   Вместо `ТВОЙ_ЛОГИН/kinobot` подставь свой логин и имя репозитория. Если используешь SSH:
   ```bash
   git remote add origin git@github.com:ТВОЙ_ЛОГИН/kinobot.git
   ```

6. **Дальше:** после изменений:
   ```bash
   git add .
   git commit -m "Описание изменений"
   git push
   ```

**Важно:** никогда не коммить и не пушить файл `.env`. Все секреты только в нём, репозиторий — без них.
