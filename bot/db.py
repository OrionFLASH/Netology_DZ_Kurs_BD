import random
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import DB_URL


def _connect():
    """Создание подключения к базе данных"""
    parsed = urlparse(DB_URL)
    return psycopg2.connect(
        dbname=parsed.path.lstrip('/'),
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        cursor_factory=RealDictCursor,
    )


# Функции для работы с пользователями

def ensure_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> int:
    """Создание или обновление пользователя в базе данных"""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (telegram_id)
            DO UPDATE SET username = EXCLUDED.username, first_name = EXCLUDED.first_name
            RETURNING id
            """,
            (telegram_id, username, first_name),
        )
        row = cur.fetchone()
        return int(row['id'])


# Функции для работы со словарем и пользовательскими словами

def get_all_dictionary_words() -> List[Tuple[str, str]]:
    """Получение всех слов из общего словаря"""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT word_en, word_ru FROM dictionary ORDER BY id")
        rows = cur.fetchall()
        return [(r['word_en'], r['word_ru']) for r in rows]


def get_user_custom_words(user_id: int) -> List[Tuple[str, str]]:
    """Получение пользовательских слов"""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT word_en, word_ru
            FROM user_words
            WHERE user_id = %s AND source = 'custom' AND is_active = TRUE
            ORDER BY id
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        return [(r['word_en'], r['word_ru']) for r in rows]


def add_user_word(user_id: int, word_en: str, word_ru: str) -> None:
    """Добавление нового слова пользователя"""
    word_en = word_en.strip().lower()
    word_ru = word_ru.strip().lower()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_words (user_id, source, word_en, word_ru)
            VALUES (%s, 'custom', %s, %s)
            """,
            (user_id, word_en, word_ru),
        )


def delete_user_word(user_id: int, word_en: str) -> bool:
    """Удаление слова пользователя (деактивация)"""
    word_en = word_en.strip().lower()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_words
            SET is_active = FALSE
            WHERE user_id = %s AND source = 'custom' AND LOWER(word_en) = %s AND is_active = TRUE
            RETURNING id
            """,
            (user_id, word_en),
        )
        return cur.fetchone() is not None


# Функции для работы с тренировками

def get_training_pool(user_id: int) -> List[Tuple[str, str]]:
    """Получение пула слов для тренировки (общие + пользовательские)"""
    pool = get_all_dictionary_words() + get_user_custom_words(user_id)
    # Удаляем дубликаты по английскому слову
    dedup = {}
    for en, ru in pool:
        dedup[en.lower()] = (en, ru)
    return list(dedup.values())


def pick_question_with_options(user_id: int) -> Optional[Tuple[str, str, List[str]]]:
    """Выбор вопроса с вариантами ответов для тренировки"""
    pool = get_training_pool(user_id)
    if len(pool) < 4:
        return None
    
    # Выбираем случайное слово для вопроса
    question_en, question_ru = random.choice(pool)
    
    # Выбираем 3 неправильных варианта
    wrong = [en for en, _ in pool if en != question_en]
    wrong_options = random.sample(wrong, 3)
    
    # Создаем список всех вариантов и перемешиваем
    options = wrong_options + [question_en]
    random.shuffle(options)
    
    return question_ru, question_en, options


def record_attempt(user_id: int, word_en: str, was_correct: bool) -> None:
    """Запись попытки ответа в базу данных"""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO quiz_attempts (user_id, word_en, was_correct) VALUES (%s, %s, %s)",
            (user_id, word_en, was_correct),
        ) 