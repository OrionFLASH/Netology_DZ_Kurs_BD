import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
from psycopg2 import sql

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / 'db' / 'schema.sql'
SEED_PATH = BASE_DIR / 'db' / 'seed.sql'
CONFIG_PATH = BASE_DIR / 'config.txt'


def load_config():
    """Загружает конфигурацию из config.txt"""
    config = {}
    
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f'Файл конфигурации не найден: {CONFIG_PATH}\n'
            f'Скопируйте config.sample.txt в config.txt и укажите настройки'
        )
    
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def get_db_conn():
    """Создание подключения к базе данных"""
    config = load_config()
    return psycopg2.connect(
        dbname=config.get('DB_NAME', 'englishcard'),
        user=config.get('DB_USER', 'englishcard'),
        password=config.get('DB_PASSWORD', 'englishcard'),
        host=config.get('DB_HOST', 'localhost'),
        port=config.get('DB_PORT', '5432'),
    )


def run_sql_file(cursor, path: Path):
    """Выполнение SQL файла"""
    with path.open('r', encoding='utf-8') as f:
        sql_text = f.read()
    cursor.execute(sql.SQL(sql_text))


def main():
    """Основная функция инициализации базы данных"""
    try:
        with get_db_conn() as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                print(f"Применение схемы: {SCHEMA_PATH}")
                run_sql_file(cur, SCHEMA_PATH)
                print(f"Заполнение данными: {SEED_PATH}")
                run_sql_file(cur, SEED_PATH)
        print('База данных успешно инициализирована.')
    except Exception as exc:
        print(f'Ошибка инициализации БД: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main() 