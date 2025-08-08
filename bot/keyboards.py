from typing import List
from telebot import types


def main_menu() -> types.ReplyKeyboardMarkup:
    """Создание главного меню бота"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('Начать тренировку'))
    kb.row(types.KeyboardButton('Добавить слово ➕'), types.KeyboardButton('Удалить слово 🔙'))
    kb.row(types.KeyboardButton('📊 Статистика'), types.KeyboardButton('🏠 Главное меню'))
    return kb


def game_menu() -> types.ReplyKeyboardMarkup:
    """Создание меню во время игры"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('⏹ Остановить игру'), types.KeyboardButton('📊 Показать статистику'))
    kb.row(types.KeyboardButton('🏠 Главное меню'))
    return kb


def options_keyboard(options: List[str]) -> types.ReplyKeyboardMarkup:
    """Создание клавиатуры с вариантами ответов и кнопками управления игрой"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    
    # Располагаем варианты в сетке 2x2 когда возможно
    rows = [options[i:i+2] for i in range(0, len(options), 2)]
    for row in rows:
        kb.row(*[types.KeyboardButton(text=o) for o in row])
    
    # Добавляем кнопки управления игрой под вариантами ответов
    kb.row(types.KeyboardButton('⏹ Остановить игру'), types.KeyboardButton('📊 Статистика'))
    kb.row(types.KeyboardButton('🏠 Главное меню'))
    
    return kb


def cancel_keyboard() -> types.ReplyKeyboardMarkup:
    """Создание клавиатуры с кнопкой отмены"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(types.KeyboardButton('Отмена'))
    return kb


def statistics_menu() -> types.ReplyKeyboardMarkup:
    """Создание меню статистики"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('🔄 Сбросить статистику'), types.KeyboardButton('📈 Детальная статистика'))
    kb.row(types.KeyboardButton('🏠 Главное меню'))
    return kb


def statistics_during_game_menu() -> types.ReplyKeyboardMarkup:
    """Создание меню статистики во время игры с кнопкой продолжить"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('🔄 Сбросить статистику'), types.KeyboardButton('📈 Детальная статистика'))
    kb.row(types.KeyboardButton('▶️ Продолжить игру'), types.KeyboardButton('🏠 Главное меню'))
    return kb 