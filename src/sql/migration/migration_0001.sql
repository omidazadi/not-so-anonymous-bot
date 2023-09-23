CREATE TABLE IF NOT EXISTS block (
    user_id INT,
    blocked INT,
    PRIMARY KEY (user_id, blocked),
    CONSTRAINT fk_user_id_3 FOREIGN KEY (user_id)
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_blocked FOREIGN KEY (blocked)
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE user_status 
ADD COLUMN is_banned BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE peer_message 
ADD COLUMN is_reported BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN is_report_reviewed BOOLEAN NOT NULL DEFAULT FALSE;