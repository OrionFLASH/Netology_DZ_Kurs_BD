# Telegram-бот EnglishCard (Курсовая по БД, Netology)

Курсовая работа по предмету "Базы данных" на тему "Telegram-бот для изучения английского языка".

Основано на задании: [sqlpy-diplom](https://github.com/netology-code/sqlpy-diplom).

## Описание проекта

Разработан Telegram-бот для изучения английского языка с возможностью:
- Тренировки по базовому словарю (179+ слов)
- Тестирования с 4 вариантами ответа
- Добавления и удаления персональных слов
- Отслеживания прогресса обучения и статистики
- Управления игровым процессом

## Возможности
- Общий словарь (179+ слов) хранится в PostgreSQL
- Тренировка с 4 вариантами ответа
- Подтверждение верного ответа и повтор при ошибке
- Пользователь может добавлять и удалять свои слова (они видны только ему)
- **Новые функции:**
  - 📊 Статистика успехов и ошибок
  - 🔥 Отслеживание серий правильных ответов
  - ⏹ Остановка игры с выводом результатов
  - 📈 Детальная статистика прогресса
  - 🔄 Сброс статистики

## Требования
- Python 3.10+
- PostgreSQL 14+
- Telegram Bot Token

## Пошаговая настройка

### 1. Создание Telegram-бота и получение токена

#### Способ 1: Через @BotFather в Telegram
1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Укажите имя бота (например: "EnglishCard")
4. Укажите username (например: "englishcard_bot") - должен заканчиваться на `_bot`
5. Скопируйте полученный токен (выглядит как `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### Способ 2: Через веб-интерфейс
1. Перейдите на [@BotFather](https://t.me/botfather) в браузере
2. Нажмите "Start" или отправьте `/start`
3. Выберите "Create a new bot" или отправьте `/newbot`
4. Следуйте инструкциям

#### Важно:
- **Сохраните токен** - он понадобится для настройки
- **Не делитесь токеном** - это ключ доступа к вашему боту
- **Токен можно пересоздать** командой `/revoke` у @BotFather

### 2. Установка зависимостей
```bash
# Создание виртуального окружения
python3 -m venv .venv

# Активация (macOS/Linux)
source .venv/bin/activate

# Установка пакетов
pip install -r requirements.txt
```

### 3. Настройка PostgreSQL

#### Установка PostgreSQL (macOS)
```bash
# Установка через Homebrew
brew install postgresql@14

# Запуск службы
brew services start postgresql@14

# Проверка статуса
brew services list | grep postgres
```

#### Установка PostgreSQL (Ubuntu/Debian)
```bash
# Обновление пакетов
sudo apt update

# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Запуск службы
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Установка PostgreSQL (Windows)
1. Скачайте установщик с [официального сайта](https://www.postgresql.org/download/windows/)
2. Запустите установщик и следуйте инструкциям
3. Запомните пароль для пользователя postgres

### 4. Создание базы данных
```bash
# Подключение к PostgreSQL (macOS/Linux)
psql -U orionflash -d postgres

# Создание базы данных
CREATE DATABASE englishcard;

# Создание пользователя (если нужно)
CREATE USER englishcard WITH PASSWORD 'englishcard';

# Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE englishcard TO englishcard;

# Выход
\q
```

### 5. Настройка конфигурации
```bash
# Копирование файла с примерами
cp config.sample.txt config.txt

# Редактирование config.txt
# Замените ВАШ_ТОКЕН_БОТА_ЗДЕСЬ на полученный токен
```

Содержимое файла `config.txt`:
```
# Конфигурация Telegram-бота EnglishCard
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Настройки базы данных
DB_HOST=localhost
DB_PORT=5432
DB_NAME=englishcard
DB_USER=orionflash
DB_PASSWORD=
```

### 6. Инициализация базы данных
```bash
# Применение схемы и заполнение начальными данными
python scripts/init_db.py
```

### 7. Запуск бота
```bash
# Запуск бота
python -m bot.main
```

## Безопасность

### Файлы конфигурации:
- `config.txt` - **НЕ попадает в Git** (в .gitignore)
- `config.sample.txt` - пример файла, безопасен для Git
- Токен бота хранится только локально

### Проверка безопасности:
```bash
# Убедитесь что config.txt в .gitignore
git status
# config.txt не должен отображаться в измененных файлах
```

## Структура базы данных

### Таблицы:
1. **users** - пользователи бота
   - `id` (SERIAL PRIMARY KEY)
   - `telegram_id` (BIGINT UNIQUE)
   - `username`, `first_name` (TEXT)
   - `created_at` (TIMESTAMPTZ)

2. **dictionary** - общий словарь для всех пользователей
   - `id` (SERIAL PRIMARY KEY)
   - `word_en`, `word_ru` (TEXT)

3. **user_words** - слова пользователей
   - `id` (SERIAL PRIMARY KEY)
   - `user_id` (REFERENCES users)
   - `source` ('global' или 'custom')
   - `dictionary_id` (REFERENCES dictionary, для глобальных слов)
   - `word_en`, `word_ru` (для пользовательских слов)
   - `is_active` (BOOLEAN)
   - `added_at` (TIMESTAMPTZ)

4. **quiz_attempts** - попытки прохождения тестов
   - `id` (SERIAL PRIMARY KEY)
   - `user_id` (REFERENCES users)
   - `word_en` (TEXT)
   - `was_correct` (BOOLEAN)
   - `attempted_at` (TIMESTAMPTZ)

5. **user_statistics** - статистика пользователей
   - `id` (SERIAL PRIMARY KEY)
   - `user_id` (REFERENCES users)
   - `total_attempts` (INTEGER)
   - `correct_attempts` (INTEGER)
   - `incorrect_attempts` (INTEGER)
   - `current_streak` (INTEGER)
   - `best_streak` (INTEGER)
   - `last_activity` (TIMESTAMPTZ)

### Начальные данные:
- 179 базовых слов по категориям
- Словарь доступен всем пользователям

## Список слов в базе данных

### Цвета (13 слов)
- red - красный
- blue - синий
- green - зеленый
- yellow - желтый
- black - черный
- white - белый
- orange - оранжевый
- purple - фиолетовый
- pink - розовый
- brown - коричневый
- gray - серый
- gold - золотой
- silver - серебряный

### Местоимения (12 слов)
- I - я
- you - ты
- we - мы
- they - они
- he - он
- she - она
- it - оно
- me - меня
- him - его
- her - ее
- us - нас
- them - их

### Числа (12 слов)
- one - один
- two - два
- three - три
- four - четыре
- five - пять
- six - шесть
- seven - семь
- eight - восемь
- nine - девять
- ten - десять
- hundred - сто
- thousand - тысяча

### Животные (17 слов)
- cat - кот
- dog - собака
- bird - птица
- horse - лошадь
- cow - корова
- pig - свинья
- sheep - овца
- chicken - курица
- duck - утка
- rabbit - кролик
- mouse - мышь
- elephant - слон
- tiger - тигр
- lion - лев
- bear - медведь
- wolf - волк
- fox - лиса

### Еда (18 слов)
- bread - хлеб
- milk - молоко
- egg - яйцо
- meat - мясо
- apple - яблоко
- banana - банан
- tomato - помидор
- potato - картофель
- carrot - морковь
- onion - лук
- cheese - сыр
- butter - масло
- sugar - сахар
- salt - соль
- water - вода
- tea - чай
- coffee - кофе
- juice - сок

### Семья (14 слов)
- mother - мама
- father - папа
- sister - сестра
- brother - брат
- grandmother - бабушка
- grandfather - дедушка
- aunt - тетя
- uncle - дядя
- cousin - двоюродный брат/сестра
- son - сын
- daughter - дочь
- wife - жена
- husband - муж
- baby - ребенок

### Дом (18 слов)
- house - дом
- room - комната
- kitchen - кухня
- bedroom - спальня
- bathroom - ванная
- door - дверь
- window - окно
- wall - стена
- floor - пол
- ceiling - потолок
- table - стол
- chair - стул
- bed - кровать
- sofa - диван
- lamp - лампа
- mirror - зеркало
- clock - часы
- picture - картина

### Одежда (15 слов)
- shirt - рубашка
- pants - брюки
- dress - платье
- skirt - юбка
- shoes - обувь
- socks - носки
- hat - шляпа
- coat - пальто
- jacket - куртка
- scarf - шарф
- gloves - перчатки
- bag - сумка
- watch - часы
- ring - кольцо
- necklace - ожерелье

### Транспорт (10 слов)
- car - машина
- bus - автобус
- train - поезд
- plane - самолет
- bike - велосипед
- boat - лодка
- ship - корабль
- taxi - такси
- truck - грузовик
- motorcycle - мотоцикл

### Природа (18 слов)
- sun - солнце
- moon - луна
- star - звезда
- sky - небо
- cloud - облако
- rain - дождь
- snow - снег
- wind - ветер
- tree - дерево
- flower - цветок
- grass - трава
- mountain - гора
- river - река
- lake - озеро
- sea - море
- forest - лес
- field - поле
- garden - сад

### Время (13 слов)
- morning - утро
- afternoon - день
- evening - вечер
- night - ночь
- today - сегодня
- yesterday - вчера
- tomorrow - завтра
- week - неделя
- month - месяц
- year - год
- hour - час
- minute - минута
- second - секунда

### Дни недели (7 слов)
- monday - понедельник
- tuesday - вторник
- wednesday - среда
- thursday - четверг
- friday - пятница
- saturday - суббота
- sunday - воскресенье

### Месяцы (12 слов)
- january - январь
- february - февраль
- march - март
- april - апрель
- may - май
- june - июнь
- july - июль
- august - август
- september - сентябрь
- october - октябрь
- november - ноябрь
- december - декабрь

**Всего: 179 слов в базе данных**

## Структура проекта
```
Netology_DZ_Kurs_BD/
├── bot/
│   ├── main.py          # Основная логика бота
│   ├── db.py            # Функции работы с БД
│   ├── keyboards.py     # Клавиатуры
│   └── config.py        # Загрузка конфигурации
├── db/
│   ├── schema.sql       # Схема БД
│   └── seed.sql         # Начальные данные
├── scripts/
│   └── init_db.py       # Инициализация БД
├── docker-compose.yml   # PostgreSQL контейнер
├── requirements.txt     # Python зависимости
├── config.sample.txt    # Пример конфигурации
├── config.txt          # Ваша конфигурация (НЕ в Git)
└── README.md           # Документация
```

## Использование бота

### Команды:
- `/start` - приветствие и главное меню

### Функции:
1. **Начать тренировку** - запуск тестирования с 4 вариантами ответа
2. **Добавить слово ➕** - добавление нового слова в формате "английское - русский"
3. **Удалить слово 🔙** - удаление слова из личной базы
4. **📊 Статистика** - просмотр статистики обучения
5. **⏹ Остановить игру** - остановка тренировки с результатами
6. **📊 Показать статистику** - статистика во время игры
7. **🔄 Сбросить статистику** - сброс всех данных статистики
8. **📈 Детальная статистика** - подробная статистика
9. **🏠 Главное меню** - возврат в главное меню

### Особенности:
- Минимум 4 слова для начала тренировки
- Пользовательские слова видны только их владельцу
- При добавлении слова показывается общее количество слов пользователя
- Неверные ответы позволяют попробовать снова
- **Отслеживание прогресса:**
  - Общее количество попыток
  - Процент успешных ответов
  - Текущая и лучшая серии правильных ответов
  - Время последней активности

## Устранение неполадок

### Ошибка подключения к БД:
```bash
# Проверка статуса PostgreSQL (macOS)
brew services list | grep postgres

# Запуск если остановлен
brew services start postgresql@14

# Проверка подключения
psql -U orionflash -d englishcard -c "SELECT version();"
```

### Ошибка токена бота:
- Проверьте правильность токена в `config.txt`
- Убедитесь что бот не заблокирован
- Проверьте что токен не содержит лишних символов

### Ошибка конфигурации:
```bash
# Проверка наличия config.txt
ls -la config.txt

# Проверка содержимого (безопасно)
head -1 config.txt
```

### Ошибки Python:
```bash
# Проверка виртуального окружения
which python
# Должно показывать путь к .venv/bin/python

# Переустановка зависимостей
pip install -r requirements.txt --force-reinstall
```

### Управление PostgreSQL:
```bash
# Запуск PostgreSQL
brew services start postgresql@14

# Остановка PostgreSQL
brew services stop postgresql@14

# Перезапуск PostgreSQL
brew services restart postgresql@14

# Проверка статуса
brew services list | grep postgres
```

## Примечания
- Для старта тренировки необходимо минимум 4 слова в сумме (глобальные + пользовательские)
- Рекомендуется Python 3.10+
- Следуйте PEP8 (можно использовать flake8/black)
- **Важно**: Файл `config.txt` с токеном НЕ должен попадать в Git
- База данных содержит 179 базовых слов по 12 категориям

## Выполненные требования курсовой работы

✅ **Основные требования:**
- Спроектирована и реализована база данных (5 таблиц)
- Разработана программа-бота на Python
- Написана документация по использованию

✅ **Функциональные требования:**
- Заполнена база данных общим набором слов (179+ слов)
- Реализована тренировка с 4 вариантами ответа
- Подтверждение правильного ответа и повтор при ошибке
- Функция добавления новых слов
- Функция удаления слов (персонально для пользователя)
- Пользовательские слова не видны другим пользователям
- Приветственное сообщение при запуске

✅ **Дополнительные функции:**
- Система статистики и отслеживания прогресса
- Управление игровым процессом
- Детальная аналитика успехов и ошибок
- Отслеживание серий правильных ответов

✅ **Технические требования:**
- Отсутствуют ошибки во время выполнения
- Результаты записываются в БД
- Количество таблиц: 5 (больше минимальных 3)
- Программа добавляет новые слова для каждого пользователя
- Код соответствует PEP8

Ссылка на оригинальное задание: [`netology-code/sqlpy-diplom`](https://github.com/netology-code/sqlpy-diplom). 