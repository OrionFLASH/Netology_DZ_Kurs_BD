import random
from typing import List, Optional, Tuple, Dict
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
        user_id = int(row['id'])
        
        # Создаем запись статистики если её нет
        cur.execute(
            """
            INSERT INTO user_statistics (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        
        return user_id


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
        # Записываем попытку
        cur.execute(
            "INSERT INTO quiz_attempts (user_id, word_en, was_correct) VALUES (%s, %s, %s)",
            (user_id, word_en, was_correct),
        )
        
        # Обновляем статистику
        if was_correct:
            cur.execute(
                """
                UPDATE user_statistics 
                SET total_attempts = total_attempts + 1,
                    correct_attempts = correct_attempts + 1,
                    current_streak = current_streak + 1,
                    best_streak = CASE 
                        WHEN current_streak + 1 > best_streak THEN current_streak + 1 
                        ELSE best_streak 
                    END,
                    last_activity = NOW()
                WHERE user_id = %s
                """,
                (user_id,),
            )
        else:
            cur.execute(
                """
                UPDATE user_statistics 
                SET total_attempts = total_attempts + 1,
                    incorrect_attempts = incorrect_attempts + 1,
                    current_streak = 0,
                    last_activity = NOW()
                WHERE user_id = %s
                """,
                (user_id,),
            )


# Функции для работы со статистикой

def get_user_statistics(user_id: int) -> Optional[Dict]:
    """Получение статистики пользователя"""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT total_attempts, correct_attempts, incorrect_attempts, 
                   current_streak, best_streak, last_activity
            FROM user_statistics
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return {
                'total_attempts': row['total_attempts'],
                'correct_attempts': row['correct_attempts'],
                'incorrect_attempts': row['incorrect_attempts'],
                'current_streak': row['current_streak'],
                'best_streak': row['best_streak'],
                'last_activity': row['last_activity'],
                'success_rate': round((row['correct_attempts'] / row['total_attempts'] * 100) if row['total_attempts'] > 0 else 0, 1)
            }
        return None


def reset_user_statistics(user_id: int) -> None:
    """Сброс статистики пользователя"""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_statistics 
            SET total_attempts = 0, correct_attempts = 0, incorrect_attempts = 0,
                current_streak = 0, best_streak = 0, last_activity = NOW()
            WHERE user_id = %s
            """,
            (user_id,),
        ) 