import logging
from dataclasses import dataclass
from typing import Dict, Optional

import telebot
from telebot import types

from .config import TELEGRAM_BOT_TOKEN
from . import db
from .keyboards import main_menu, options_keyboard, cancel_keyboard, statistics_menu, statistics_during_game_menu

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='HTML')


@dataclass
class UserState:
    """Состояние пользователя для управления диалогом"""
    mode: Optional[str] = None  # 'quiz' | 'add' | 'delete'
    pending_correct_en: Optional[str] = None


# Хранилище состояний пользователей
user_states: Dict[int, UserState] = {}


def get_state(chat_id: int) -> UserState:
    """Получение или создание состояния пользователя"""
    if chat_id not in user_states:
        user_states[chat_id] = UserState()
    return user_states[chat_id]


def format_statistics(stats: Dict) -> str:
    """Форматирование статистики для отображения"""
    return (
        f"📊 <b>Ваша статистика:</b>\n\n"
        f"🎯 Всего попыток: <b>{stats['total_attempts']}</b>\n"
        f"✅ Правильных ответов: <b>{stats['correct_attempts']}</b>\n"
        f"❌ Неправильных ответов: <b>{stats['incorrect_attempts']}</b>\n"
        f"📈 Процент успеха: <b>{stats['success_rate']}%</b>\n"
        f"🔥 Текущая серия: <b>{stats['current_streak']}</b>\n"
        f"🏆 Лучшая серия: <b>{stats['best_streak']}</b>\n"
        f"🕐 Последняя активность: <b>{stats['last_activity'].strftime('%d.%m.%Y %H:%M')}</b>"
    )


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    logger.info("Пользователь зарегистрирован id=%s tg_id=%s", user_id, message.from_user.id)
    
    welcome = (
        "Привет 👋 Давай попрактикуемся в английском языке.\n\n"
        "Ты можешь использовать тренажёр как конструктор и собирать свою базу для обучения.\n"
        "Воспользуйся инструментами: добавить слово ➕, удалить слово 🔙.\n\n"
        "📊 Отслеживай свой прогресс в разделе статистики!\n\n"
        "Ну что, начнём ⬇️"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == 'Начать тренировку')
def handle_start_training(message: types.Message):
    """Обработчик кнопки 'Начать тренировку'"""
    state = get_state(message.chat.id)
    state.mode = 'quiz'
    ask_question(message)


@bot.message_handler(func=lambda m: m.text == '📊 Статистика')
def handle_statistics(message: types.Message):
    """Обработчик кнопки 'Статистика' - определяет контекст и показывает соответствующее меню"""
    state = get_state(message.chat.id)
    user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stats = db.get_user_statistics(user_db_id)
    
    # Определяем, находимся ли мы в режиме игры
    is_during_game = state.mode == 'quiz' and state.pending_correct_en is not None
    
    if stats and stats['total_attempts'] > 0:
        if is_during_game:
            # Во время игры - показываем меню с кнопкой "Продолжить"
            bot.send_message(message.chat.id, format_statistics(stats), reply_markup=statistics_during_game_menu())
        else:
            # Обычное меню статистики
            bot.send_message(message.chat.id, format_statistics(stats), reply_markup=statistics_menu())
    else:
        if is_during_game:
            bot.send_message(
                message.chat.id, 
                "📊 У вас пока нет статистики. Продолжайте тренировку!",
                reply_markup=statistics_during_game_menu()
            )
        else:
            bot.send_message(
                message.chat.id, 
                "📊 У вас пока нет статистики. Начните тренировку, чтобы накопить данные!",
                reply_markup=statistics_menu()
            )


@bot.message_handler(func=lambda m: m.text == '🔄 Сбросить статистику')
def handle_reset_statistics(message: types.Message):
    """Обработчик кнопки 'Сбросить статистику'"""
    user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    db.reset_user_statistics(user_db_id)
    bot.send_message(
        message.chat.id, 
        "🔄 Статистика сброшена! Начните заново для накопления новых данных.",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == '📈 Детальная статистика')
def handle_detailed_statistics(message: types.Message):
    """Обработчик кнопки 'Детальная статистика'"""
    user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stats = db.get_user_statistics(user_db_id)
    
    if stats and stats['total_attempts'] > 0:
        detailed_stats = (
            f"📈 <b>Детальная статистика:</b>\n\n"
            f"🎯 <b>Общие показатели:</b>\n"
            f"   • Всего попыток: {stats['total_attempts']}\n"
            f"   • Правильных: {stats['correct_attempts']}\n"
            f"   • Неправильных: {stats['incorrect_attempts']}\n\n"
            f"📊 <b>Процентные показатели:</b>\n"
            f"   • Успешность: {stats['success_rate']}%\n"
            f"   • Ошибки: {100 - stats['success_rate']:.1f}%\n\n"
            f"🔥 <b>Серии ответов:</b>\n"
            f"   • Текущая серия: {stats['current_streak']}\n"
            f"   • Лучшая серия: {stats['best_streak']}\n\n"
            f"🕐 Последняя активность: {stats['last_activity'].strftime('%d.%m.%Y в %H:%M')}"
        )
        bot.send_message(message.chat.id, detailed_stats, reply_markup=statistics_menu())
    else:
        bot.send_message(
            message.chat.id, 
            "📈 У вас пока нет данных для детальной статистики.",
            reply_markup=statistics_menu()
        )


@bot.message_handler(func=lambda m: m.text == '⏹ Остановить игру')
def handle_stop_game(message: types.Message):
    """Обработчик кнопки 'Остановить игру'"""
    state = get_state(message.chat.id)
    state.mode = None
    state.pending_correct_en = None
    
    user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stats = db.get_user_statistics(user_db_id)
    
    if stats and stats['total_attempts'] > 0:
        session_stats = (
            f"⏹ <b>Игра остановлена!</b>\n\n"
            f"📊 <b>Результаты сессии:</b>\n"
            f"   • Правильных ответов: {stats['correct_attempts']}\n"
            f"   • Неправильных ответов: {stats['incorrect_attempts']}\n"
            f"   • Процент успеха: {stats['success_rate']}%\n"
            f"   • Лучшая серия: {stats['best_streak']}\n\n"
            f"Отличная работа! 🎉"
        )
        bot.send_message(message.chat.id, session_stats, reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "⏹ Игра остановлена!", reply_markup=main_menu())





@bot.message_handler(func=lambda m: m.text == '▶️ Продолжить игру')
def handle_continue_game(message: types.Message):
    """Обработчик кнопки 'Продолжить игру'"""
    state = get_state(message.chat.id)
    if state.mode == 'quiz':
        ask_question(message)
    else:
        bot.send_message(message.chat.id, "🏠 Главное меню:", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == '🏠 Главное меню')
def handle_main_menu(message: types.Message):
    """Обработчик кнопки 'Главное меню'"""
    state = get_state(message.chat.id)
    state.mode = None
    state.pending_correct_en = None
    bot.send_message(message.chat.id, "🏠 Главное меню:", reply_markup=main_menu())


def ask_question(message: types.Message):
    """Функция для показа вопроса пользователю"""
    user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    picked = db.pick_question_with_options(user_db_id)
    
    if not picked:
        bot.send_message(
            message.chat.id,
            'Недостаточно слов для тренировки. Добавьте ещё слова (минимум 4 в сумме).',
            reply_markup=main_menu(),
        )
        return
    
    word_ru, correct_en, options = picked
    state = get_state(message.chat.id)
    state.pending_correct_en = correct_en
    
    bot.send_message(
        message.chat.id,
        f'Как переводится слово: <b>{word_ru}</b>?',
        reply_markup=options_keyboard(options),
    )


@bot.message_handler(func=lambda m: m.text == 'Добавить слово ➕')
def handle_add_word(message: types.Message):
    """Обработчик кнопки 'Добавить слово'"""
    state = get_state(message.chat.id)
    state.mode = 'add'
    bot.send_message(
        message.chat.id,
        'Отправьте слово в формате: <b>английское - русский</b> (например: <i>cat - кот</i>)',
        reply_markup=cancel_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == 'Удалить слово 🔙')
def handle_delete_word(message: types.Message):
    """Обработчик кнопки 'Удалить слово'"""
    state = get_state(message.chat.id)
    state.mode = 'delete'
    bot.send_message(
        message.chat.id,
        'Отправьте <b>английское</b> слово для удаления из вашей базы',
        reply_markup=cancel_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == 'Отмена')
def handle_cancel(message: types.Message):
    """Обработчик кнопки 'Отмена'"""
    state = get_state(message.chat.id)
    state.mode = None
    state.pending_correct_en = None
    bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=main_menu())


@bot.message_handler(content_types=['text'])
def handle_text(message: types.Message):
    """Основной обработчик текстовых сообщений"""
    state = get_state(message.chat.id)

    # Обработка ответов в режиме тренировки
    if state.mode == 'quiz' and state.pending_correct_en:
        user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        is_correct = message.text.strip().lower() == state.pending_correct_en.lower()
        db.record_attempt(user_db_id, state.pending_correct_en, is_correct)
        
        if is_correct:
            bot.send_message(message.chat.id, 'Верно ✅')
            state.pending_correct_en = None
            ask_question(message)
        else:
            bot.send_message(message.chat.id, 'Неверно. Попробуйте ещё раз ❌')
        return

    # Обработка добавления слова
    if state.mode == 'add':
        parts = message.text.split('-')
        if len(parts) != 2:
            bot.send_message(message.chat.id, 'Неверный формат. Пример: <i>cat - кот</i>')
            return
        
        en = parts[0].strip()
        ru = parts[1].strip()
        user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        db.add_user_word(user_db_id, en, ru)
        
        count = len(db.get_training_pool(user_db_id))
        bot.send_message(
            message.chat.id,
            f'Слово добавлено ✅ Сейчас в вашей базе: <b>{count}</b> слов.',
            reply_markup=main_menu(),
        )
        state.mode = None
        return

    # Обработка удаления слова
    if state.mode == 'delete':
        en = message.text.strip()
        user_db_id = db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        deleted = db.delete_user_word(user_db_id, en)
        
        if deleted:
            bot.send_message(message.chat.id, 'Слово удалено ✅', reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, 'Слово не найдено среди ваших добавленных активных слов.', reply_markup=main_menu())
        state.mode = None
        return

    # Обработка неизвестных сообщений
    bot.send_message(message.chat.id, 'Выберите действие из меню ниже ⬇️', reply_markup=main_menu())


if __name__ == '__main__':
    logger.info('Запуск бота...')
    bot.infinity_polling(skip_pending=True) 