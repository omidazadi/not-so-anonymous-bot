SET foreign_key_checks = 0;
        
CREATE TABLE IF NOT EXISTS channel_message (
    channel_message_id INT AUTO_INCREMENT PRIMARY KEY,
    message_tid VARCHAR(50) NOT NULL,
    from_user INT NOT NULL,
    message TEXT NOT NULL,
    media BLOB NOT NULL,
    can_reply BOOLEAN NOT NULL,
    verdict CHAR(1) NOT NULL,
    reviewed_by INT,
    sent_at TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,
    CONSTRAINT fk_from_user_1 FOREIGN KEY (from_user)
        REFERENCES user_status(user_id),
    CONSTRAINT fk_reviewed_by FOREIGN KEY (reviewed_by)
        REFERENCES user_status(user_id)
);

CREATE TABLE IF NOT EXISTS peer_message (
    peer_message_id INT AUTO_INCREMENT PRIMARY KEY,
    channel_message_reply INT,
    peer_message_reply INT,
    from_message_tid VARCHAR(50) NOT NULL,
    to_message_tid VARCHAR(50) NOT NULL,
    from_user INT NOT NULL,
    message TEXT NOT NULL,
    media BLOB NOT NULL,
    condition CHAR(1) NOT NULL,
    sent_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_channel_message_reply FOREIGN KEY (channel_message_reply)
        REFERENCES channel_message(channel_message_id),
    CONSTRAINT fk_peer_message_reply FOREIGN KEY (peer_message_reply)
        REFERENCES peer_message(peer_message_id),
    CONSTRAINT fk_from_user_2 FOREIGN KEY (from_user)
        REFERENCES user_status(user_id),
    CONSTRAINT chk_reply CHECK (
        (channel_message_reply = NULL AND peer_message_reply != NULL) OR 
        (channel_message_reply != NULL AND peer_message_reply = NULL)
    )
);

CREATE TABLE IF NOT EXISTS user_status (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_tid VARCHAR(50),
    gen_is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    veil VARCHAR(500),
    is_veiled BOOLEAN NOT NULL,
    state VARCHAR(50) NOT NULL,
    extra VARCHAR(500),
    last_message_at TIMESTAMP,
    CONSTRAINT fk_veil FOREIGN KEY (veil)
        REFERENCES veil(name)
);

CREATE TABLE IF NOT EXISTS admin (
    user_tid VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(500) NOT NULL
);

CREATE TABLE IF NOT EXISTS veil (
    name VARCHAR(500) PRIMARY KEY
);

/* Start of user_status.gen_is_admin management triggers. */

DROP TRIGGER IF EXISTS trigger_gen_is_admin_user_status_insert;
CREATE TRIGGER trigger_gen_is_admin_user_status_insert
    BEFORE INSERT ON user_status FOR EACH ROW
BEGIN
    if NEW.user_tid IN (
        SELECT user_tid
        FROM admin
    ) THEN
        SET NEW.gen_is_admin = TRUE;
    END IF;
END;

DROP TRIGGER IF EXISTS trigger_gen_is_admin_admin_insert;
CREATE TRIGGER trigger_gen_is_admin_admin_insert
    AFTER INSERT ON admin FOR EACH ROW
BEGIN
    UPDATE user_status
    SET gen_is_admin = TRUE
    WHERE user_tid = NEW.user_tid;
END;

DROP TRIGGER IF EXISTS trigger_gen_is_admin_admin_delete;
CREATE TRIGGER trigger_gen_is_admin_admin_delete
    BEFORE DELETE ON admin FOR EACH ROW
BEGIN
    UPDATE user_status
    SET gen_is_admin = FALSE
    WHERE user_tid = OLD.user_tid;
END;

/* End of user_status.gen_is_admin management triggers. */

INSERT IGNORE INTO admin VALUES
    ('5665972958', '$2b$12$nGw4T8HrlhkrzppmMFrDq.opwqemZn7S.9BG6nTUMEGq62mi4D.GW'),
    ('5496603882', '$2b$12$nGw4T8HrlhkrzppmMFrDq.opwqemZn7S.9BG6nTUMEGq62mi4D.GW');

SET foreign_key_checks = 1;