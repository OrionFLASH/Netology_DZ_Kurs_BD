from typing import List
from telebot import types


def main_menu() -> types.ReplyKeyboardMarkup:
    """Создание главного меню бота"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('Начать тренировку'))
    kb.row(types.KeyboardButton('Добавить слово ➕'), types.KeyboardButton('Удалить слово 🔙'))
    return kb


def options_keyboard(options: List[str]) -> types.ReplyKeyboardMarkup:
    """Создание клавиатуры с вариантами ответов"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # Располагаем варианты в сетке 2x2 когда возможно
    rows = [options[i:i+2] for i in range(0, len(options), 2)]
    for row in rows:
        kb.row(*[types.KeyboardButton(text=o) for o in row])
    return kb


def cancel_keyboard() -> types.ReplyKeyboardMarkup:
    """Создание клавиатуры с кнопкой отмены"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(types.KeyboardButton('Отмена'))
    return kb 