CREATE TABLE IF NOT EXISTS message (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    verdict TEXT NOT NULL,
    reviewed_by TEXT,
    sent_at TEXT NOT NULL,
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS user_status (
    telegram_id TEXT NOT NULL PRIMARY KEY,
    state TEXT NOT NULL,
    extra TEXT,
    no_messages INT NOT NULL,
    last_message_at TEXT
) WITHOUT ROWID;