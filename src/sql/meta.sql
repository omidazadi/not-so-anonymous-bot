CREATE TABLE IF NOT EXISTS migration (
    meta_key   VARCHAR(100) PRIMARY KEY,
    meta_value VARCHAR(255) DEFAULT NULL
);

INSERT IGNORE INTO migration VALUES
    ('version', '000.000.000');