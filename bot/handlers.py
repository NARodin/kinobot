import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import main_menu_keyboard, mood_keyboard, movie_details_keyboard
from config import KINOPOISK_API_KEY
from db.database import save_request
from kinopoisk.client import KinopoiskClient, MovieDetails, MovieSummary


WELCOME_TEXT = (
    "Привет! Я кинобот 🎬\n"
    "Выбери, что хочешь сделать:\n"
    "— Настроение (комедия, триллер, драма)\n"
    "— Случайный фильм\n"
    "— Поиск по названию"
)

client = KinopoiskClient(api_key=KINOPOISK_API_KEY)


def _format_movie_caption(movie: MovieSummary) -> str:
    rating = f"{movie.rating:.1f}" if movie.rating else "нет"
    year = f"{movie.year}" if movie.year else "?"
    return (
        f"{movie.name} ({year})\n"
        f"Рейтинг: {rating}\n\n"
        f"{movie.description}"
    )


def _format_details(details: MovieDetails) -> str:
    actors = ", ".join(details.actors) if details.actors else "неизвестны"
    directors = ", ".join(details.directors) if details.directors else "неизвестны"
    duration = f"{details.duration_minutes} мин" if details.duration_minutes else "неизвестна"
    return (
        f"Подробнее: {details.name}\n"
        f"Режиссёр: {directors}\n"
        f"Актёры: {actors}\n"
        f"Длительность: {duration}"
    )


async def _send_movie(chat_id: int, movie: MovieSummary, context: ContextTypes.DEFAULT_TYPE) -> None:
    caption = _format_movie_caption(movie)
    reply_markup = movie_details_keyboard(movie.movie_id)
    if movie.poster_url:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=movie.poster_url,
            caption=caption,
            reply_markup=reply_markup,
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=reply_markup,
        )


async def _send_main_menu(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=chat_id,
        text="Что дальше?",
        reply_markup=main_menu_keyboard(),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""

    if data == "mood_menu":
        await query.edit_message_text(
            "Выбери настроение:", reply_markup=mood_keyboard()
        )
        return

    if data == "back_to_menu":
        await query.edit_message_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())
        return

    if data.startswith("mood_"):
        mood = data.replace("mood_", "")
        mood_map = {
            "comedy": "комедия",
            "thriller": "триллер",
            "drama": "драма",
        }
        genre = mood_map.get(mood, mood)
        save_request(
            user_id=query.from_user.id,
            request_type="mood",
            query=genre,
        )
        await query.edit_message_text(f"Ищу фильмы жанра: {genre}...")
        try:
            movies = await client.get_movies_by_genre(genre=genre, limit=3)
        except httpx.HTTPError:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Не удалось получить фильмы. Попробуй позже.",
            )
            return
        if not movies:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="По этому жанру ничего не найдено.",
            )
            return
        for movie in movies:
            await _send_movie(query.message.chat_id, movie, context)
        await _send_main_menu(query.message.chat_id, context)
        return

    if data == "random":
        save_request(
            user_id=query.from_user.id,
            request_type="random",
            query="random",
        )
        await query.edit_message_text("Ищу случайный фильм...")
        try:
            movie = await client.get_random_movie()
        except httpx.HTTPError:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Не удалось получить случайный фильм. Попробуй позже.",
            )
            return
        if not movie:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Не удалось найти случайный фильм.",
            )
            return
        await _send_movie(query.message.chat_id, movie, context)
        await _send_main_menu(query.message.chat_id, context)
        return

    if data == "search":
        context.user_data["awaiting_search"] = True
        await query.edit_message_text("Введите название фильма:")
        return

    if data.startswith("detail_"):
        try:
            movie_id = int(data.replace("detail_", ""))
        except ValueError:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Некорректный идентификатор фильма.",
            )
            return
        try:
            details = await client.get_movie_details(movie_id)
        except httpx.HTTPError:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Не удалось получить детали фильма. Попробуй позже.",
            )
            return
        if not details:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Не удалось получить детали фильма.",
            )
            return
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=_format_details(details),
            reply_to_message_id=query.message.message_id,
        )
        await _send_main_menu(query.message.chat_id, context)
        return

    await query.edit_message_text(
        "Неизвестная команда. Открой меню /start"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if context.user_data.get("awaiting_search"):
        query_text = update.message.text.strip()
        context.user_data["awaiting_search"] = False
        save_request(
            user_id=update.effective_user.id,
            request_type="search",
            query=query_text,
        )
        await update.message.reply_text(f"Ищу фильмы по запросу: {query_text}...")
        try:
            movies = await client.search_movies_by_name(query_text, limit=3)
        except httpx.HTTPError:
            await update.message.reply_text(
                "Не удалось выполнить поиск. Попробуй позже."
            )
            return
        if not movies:
            await update.message.reply_text("Ничего не найдено.")
            return
        for movie in movies:
            await _send_movie(update.message.chat_id, movie, context)
        await _send_main_menu(update.message.chat_id, context)
        return

    await update.message.reply_text(
        "Я понимаю только команды и кнопки. Нажми /start, чтобы открыть меню."
    )
