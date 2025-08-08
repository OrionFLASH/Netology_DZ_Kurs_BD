-- Users registered in bot
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    telegram_id   BIGINT UNIQUE NOT NULL,
    username      TEXT,
    first_name    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Global dictionary shared by all users
CREATE TABLE IF NOT EXISTS dictionary (
    id        SERIAL PRIMARY KEY,
    word_en   TEXT NOT NULL UNIQUE,
    word_ru   TEXT NOT NULL
);

-- Words a specific user studies (custom words or references to global)
CREATE TABLE IF NOT EXISTS user_words (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source         TEXT NOT NULL CHECK (source IN ('global','custom')),
    dictionary_id  INTEGER REFERENCES dictionary(id) ON DELETE CASCADE,
    word_en        TEXT,
    word_ru        TEXT,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    added_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_words_custom_has_words
        CHECK ( (source = 'custom' AND word_en IS NOT NULL AND word_ru IS NOT NULL) OR
                (source = 'global' AND dictionary_id IS NOT NULL) )
);

-- Quiz attempts for basic analytics
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word_en      TEXT NOT NULL,
    was_correct  BOOLEAN NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
); 