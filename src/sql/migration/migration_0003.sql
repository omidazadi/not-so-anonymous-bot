ALTER TABLE peer_message ADD COLUMN answer_message_reply INT DEFAULT NULL AFTER peer_message_reply;

ALTER TABLE channel_message ADD COLUMN channel_message_tid VARCHAR(50) NOT NULL DEFAULT '?' AFTER message_tid;
ALTER TABLE channel_message ADD COLUMN discussion_message_tid VARCHAR(50) NOT NULL DEFAULT '?' AFTER channel_message_tid;
ALTER TABLE channel_message ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE AFTER can_reply;

CREATE TABLE IF NOT EXISTS answer_message (
    answer_message_id INT AUTO_INCREMENT PRIMARY KEY,
    channel_message_reply INT,
    from_message_tid VARCHAR(50) NOT NULL,
    to_notification_tid VARCHAR(50) NOT NULL,
    to_message_tid VARCHAR(50) NOT NULL,
    discussion_message_tid VARCHAR(50) NOT NULL,
    from_user INT NOT NULL,
    from_user_veil VARCHAR(500),
    message TEXT NOT NULL,
    media BLOB NOT NULL,
    can_reply BOOLEAN NOT NULL,
    message_status CHAR(1) NOT NULL,
    is_reported BOOLEAN NOT NULL,
    is_report_reviewed BOOLEAN NOT NULL,
    sent_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_channel_message_reply_2 FOREIGN KEY (channel_message_reply)
        REFERENCES channel_message(channel_message_id)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_from_user_3 FOREIGN KEY (from_user)
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE
) CHARACTER SET utf8mb4;

UPDATE user_status SET state = 'home', extra = NULL WHERE state = 'sending';