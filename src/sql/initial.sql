CREATE TABLE IF NOT EXISTS meta_data (
    meta_key VARCHAR(255) PRIMARY KEY,
    meta_value VARCHAR(255) DEFAULT NULL
);

INSERT IGNORE INTO meta_data VALUES
    ('version', '000.000.000'),
    ('migration_0000', '000.002.000');