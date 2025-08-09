#!/usr/bin/env python3
"""
Утилиты для безопасного запуска бота
"""

import os
import sys
import time
import signal
import subprocess
import requests
import psutil
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def find_bot_processes(token: str) -> List[int]:
    """Поиск процессов, использующих токен бота"""
    processes = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Пропускаем текущий процесс
            if proc.info['pid'] == current_pid:
                continue
                
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Ищем процессы с токеном или bot.main, но не текущий запуск
                if (token in cmdline or 'bot.main' in cmdline) and 'startup_utils' not in cmdline:
                    processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return processes


def kill_bot_processes(token: str, timeout: int = 10) -> bool:
    """Остановка процессов бота"""
    processes = find_bot_processes(token)
    
    if not processes:
        logger.info("Процессы бота не найдены")
        return True
    
    logger.info(f"Найдены процессы бота: {processes}")
    
    # Сначала пытаемся мягко завершить
    for pid in processes:
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Отправлен SIGTERM процессу {pid}")
        except ProcessLookupError:
            logger.info(f"Процесс {pid} уже завершен")
        except PermissionError:
            logger.warning(f"Нет прав для завершения процесса {pid}")
    
    # Ждем завершения
    time.sleep(2)
    
    # Проверяем что процессы завершились
    remaining = find_bot_processes(token)
    
    if remaining:
        logger.warning(f"Принудительно завершаем процессы: {remaining}")
        for pid in remaining:
            try:
                os.kill(pid, signal.SIGKILL)
                logger.info(f"Отправлен SIGKILL процессу {pid}")
            except ProcessLookupError:
                logger.info(f"Процесс {pid} уже завершен")
            except PermissionError:
                logger.error(f"Нет прав для принудительного завершения процесса {pid}")
        
        time.sleep(1)
        final_check = find_bot_processes(token)
        if final_check:
            logger.error(f"Не удалось завершить процессы: {final_check}")
            return False
    
    logger.info("Все процессы бота успешно завершены")
    return True


def clear_telegram_connections(token: str) -> bool:
    """Очистка соединений с Telegram API"""
    try:
        logger.info("Очищаем соединения с Telegram API...")
        
        # Удаляем webhook если есть
        webhook_url = f'https://api.telegram.org/bot{token}/deleteWebhook'
        response = requests.get(webhook_url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("Webhook успешно удален")
        else:
            logger.warning(f"Ошибка удаления webhook: {result}")
        
        # Очищаем pending updates
        updates_url = f'https://api.telegram.org/bot{token}/getUpdates'
        
        # Пытаемся получить updates с разными offset'ами
        for offset in [999999999, -999999999, 0]:
            try:
                response = requests.get(
                    updates_url, 
                    params={'offset': offset, 'timeout': 1}, 
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info(f"Очистка с offset {offset}: успешно")
                    break
            except Exception as e:
                logger.warning(f"Ошибка очистки с offset {offset}: {e}")
        
        # Финальная проверка
        time.sleep(2)
        response = requests.get(updates_url, params={'timeout': 1}, timeout=5)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Telegram API готов к подключению")
            return True
        else:
            logger.error(f"❌ Ошибка проверки API: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка очистки соединений: {e}")
        return False


def check_postgresql_connection(db_url: str) -> bool:
    """Проверка подключения к PostgreSQL"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
        )
        conn.close()
        logger.info("✅ PostgreSQL подключение успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False


def print_postgresql_help():
    """Вывод инструкций по запуску PostgreSQL"""
    help_text = """
🔧 ИНСТРУКЦИИ ПО ЗАПУСКУ POSTGRESQL:

📍 Для macOS (Homebrew):
   brew services start postgresql@14
   # или для другой версии:
   brew services start postgresql@15

📍 Для Ubuntu/Debian:
   sudo systemctl start postgresql
   sudo systemctl enable postgresql

📍 Для Windows:
   net start postgresql-x64-14
   # или через Services (services.msc)

📍 Для Docker:
   docker-compose up -d
   # или:
   docker run -d --name postgres -e POSTGRES_DB=englishcard \\
     -e POSTGRES_USER=englishcard -e POSTGRES_PASSWORD=englishcard \\
     -p 5432:5432 postgres:14

📍 Проверка статуса:
   macOS: brew services list | grep postgres
   Linux: sudo systemctl status postgresql
   Windows: sc query postgresql-x64-14

📍 Создание базы данных (если нужно):
   createdb englishcard
   # или:
   psql -c "CREATE DATABASE englishcard;"

📍 Инициализация схемы:
   python scripts/init_db.py
"""
    print(help_text)


def safe_startup_check(token: str, db_url: str) -> bool:
    """Комплексная проверка перед запуском бота"""
    logger.info("🚀 Начинаем безопасный запуск бота...")
    
    # 1. Остановка существующих процессов
    logger.info("1️⃣ Проверяем и останавливаем существующие процессы...")
    if not kill_bot_processes(token):
        logger.error("Не удалось остановить существующие процессы")
        return False
    
    # 2. Очистка Telegram соединений
    logger.info("2️⃣ Очищаем соединения с Telegram API...")
    if not clear_telegram_connections(token):
        logger.error("Не удалось очистить соединения с Telegram API")
        return False
    
    # 3. Проверка PostgreSQL
    logger.info("3️⃣ Проверяем подключение к PostgreSQL...")
    if not check_postgresql_connection(db_url):
        logger.error("PostgreSQL недоступен!")
        print_postgresql_help()
        return False
    
    logger.info("✅ Все проверки прошли успешно! Бот готов к запуску.")
    return True


if __name__ == "__main__":
    # Тестирование утилит
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
        db_url = sys.argv[2] if len(sys.argv) > 2 else "postgresql://localhost:5432/englishcard"
        
        logging.basicConfig(level=logging.INFO)
        safe_startup_check(token, db_url)
