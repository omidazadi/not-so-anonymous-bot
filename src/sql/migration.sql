DROP PROCEDURE IF EXISTS migrate;
CREATE PROCEDURE migrate()
BEGIN
    DECLARE version VARCHAR(255);
    DECLARE v0_2_0 VARCHAR(255);
    SELECT meta_value
        FROM migration
        WHERE meta_key = 'version'
        INTO version;
    SET v0_2_0 = '000.002.000';

    IF STRCMP(version, v0_2_0) = -1 THEN
        SET foreign_key_checks = 0;
                
        CREATE TABLE IF NOT EXISTS channel_message (
            channel_message_id INT AUTO_INCREMENT PRIMARY KEY,
            message_tid VARCHAR(50) NOT NULL,
            from_user INT NOT NULL,
            message TEXT NOT NULL,
            media BLOB NOT NULL,
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
            to_user INT NOT NULL,
            message TEXT NOT NULL,
            media BLOB NOT NULL,
            sent_at TIMESTAMP NOT NULL,
            CONSTRAINT fk_channel_message_reply FOREIGN KEY (channel_message_reply)
                REFERENCES channel_message(channel_message_id),
            CONSTRAINT fk_peer_message_reply FOREIGN KEY (peer_message_reply)
                REFERENCES peer_message(peer_message_id),
            CONSTRAINT fk_from_user_2 FOREIGN KEY (from_user)
                REFERENCES user_status(user_id),
            CONSTRAINT fk_to_user FOREIGN KEY (to_user)
                REFERENCES user_status(user_id),
            CONSTRAINT chk_reply CHECK (
                (channel_message_reply = NULL AND peer_message_reply != NULL) OR 
                (channel_message_reply != NULL AND peer_message_reply = NULL)
            )
        );

        CREATE TABLE IF NOT EXISTS user_status (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            user_tid VARCHAR(50),
            is_admin BOOLEAN NOT NULL,
            mask_name VARCHAR(500),
            is_masked BOOLEAN NOT NULL,
            state VARCHAR(50) NOT NULL,
            extra VARCHAR(500),
            last_message_at TIMESTAMP,
            CONSTRAINT fk_mask_name FOREIGN KEY (mask_name)
                REFERENCES indian_name(name)
        );

        CREATE TABLE IF NOT EXISTS admin (
            user_tid VARCHAR(50) PRIMARY KEY,
            password_hash VARCHAR(500) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS indian_name (
            name VARCHAR(500) PRIMARY KEY
        );

        INSERT IGNORE INTO admin VALUES
            ('5665972958', '$2b$12$nGw4T8HrlhkrzppmMFrDq.opwqemZn7S.9BG6nTUMEGq62mi4D.GW'),
            ('5496603882', '$2b$12$nGw4T8HrlhkrzppmMFrDq.opwqemZn7S.9BG6nTUMEGq62mi4D.GW');

        SET foreign_key_checks = 1;

        SET version = v0_2_0;
    END IF;

    UPDATE migration
        SET meta_value = version
        WHERE meta_key = 'version';
END;

CALL migrate();