import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / 'config.txt'


def load_config():
    """Загружает конфигурацию из config.txt"""
    config = {}
    
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f'Файл конфигурации не найден: {CONFIG_PATH}\n'
            f'Скопируйте config.sample.txt в config.txt и укажите токен бота'
        )
    
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


# Загружаем конфигурацию
try:
    config = load_config()
    TELEGRAM_BOT_TOKEN = config.get('BOT_TOKEN', '').strip()
    
    # Формируем строку подключения к БД
    DB_HOST = config.get('DB_HOST', 'localhost')
    DB_PORT = config.get('DB_PORT', '5432')
    DB_NAME = config.get('DB_NAME', 'englishcard')
    DB_USER = config.get('DB_USER', 'englishcard')
    DB_PASSWORD = config.get('DB_PASSWORD', 'englishcard')
    
    DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА_ЗДЕСЬ':
        raise RuntimeError(
            'TELEGRAM_BOT_TOKEN не настроен в config.txt\n'
            'Укажите ваш токен бота в файле config.txt'
        )
        
except Exception as e:
    print(f'Ошибка загрузки конфигурации: {e}')
    raise 