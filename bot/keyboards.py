from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎭 Настроение", callback_data="mood_menu")],
        [InlineKeyboardButton("🎲 Случайный фильм", callback_data="random")],
        [InlineKeyboardButton("🔍 Поиск по названию", callback_data="search")],
    ]
    return InlineKeyboardMarkup(keyboard)


def mood_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Комедия", callback_data="mood_comedy"),
            InlineKeyboardButton("Триллер", callback_data="mood_thriller"),
        ],
        [InlineKeyboardButton("Драма", callback_data="mood_drama")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def movie_details_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("Подробнее", callback_data=f"detail_{movie_id}")]]
    return InlineKeyboardMarkup(keyboard)
