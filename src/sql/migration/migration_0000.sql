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
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reviewed_by FOREIGN KEY (reviewed_by)
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE
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
    message_status CHAR(1) NOT NULL,
    sent_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_channel_message_reply FOREIGN KEY (channel_message_reply)
        REFERENCES channel_message(channel_message_id)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_peer_message_reply FOREIGN KEY (peer_message_reply)
        REFERENCES peer_message(peer_message_id)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_from_user_2 FOREIGN KEY (from_user)
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE
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
            ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS admin (
    user_tid VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(500) NOT NULL
);

CREATE TABLE IF NOT EXISTS veil (
    name VARCHAR(500) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    gen_reservation_status VARCHAR(50) NOT NULL DEFAULT 'free'
);

CREATE TABLE IF NOT EXISTS reservation (
    user_id INT PRIMARY KEY,
    veil_1 VARCHAR(500) NOT NULL,
    veil_2 VARCHAR(500) NOT NULL,
    veil_3 VARCHAR(500) NOT NULL,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES user_status(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_veil_2 FOREIGN KEY (veil_1)
        REFERENCES veil(name)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_veil_3 FOREIGN KEY (veil_2)
        REFERENCES veil(name)
            ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_veil_4 FOREIGN KEY (veil_3)
        REFERENCES veil(name)
            ON DELETE CASCADE ON UPDATE CASCADE
);

/* Start of user_status.gen_is_admin management triggers. */

DROP TRIGGER IF EXISTS trigger_gen_is_admin_user_status_insert;
CREATE TRIGGER trigger_gen_is_admin_user_status_insert
    BEFORE INSERT ON user_status FOR EACH ROW
BEGIN
    IF NEW.user_tid IN (
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

/* Start of veil.gen_reservation_status management triggers. */

DROP TRIGGER IF EXISTS trigger_gen_reservation_status_reservation_insert;
CREATE TRIGGER trigger_gen_reservation_status_reservation_insert
    AFTER INSERT ON reservation FOR EACH ROW
BEGIN
    DECLARE reservation_status_1 VARCHAR(500);
    DECLARE reservation_status_2 VARCHAR(500);
    DECLARE reservation_status_3 VARCHAR(500);

    SELECT gen_reservation_status
    FROM veil
    WHERE name = NEW.veil_1
    INTO reservation_status_1;

    SELECT gen_reservation_status
    FROM veil
    WHERE name = NEW.veil_2
    INTO reservation_status_2;

    SELECT gen_reservation_status
    FROM veil
    WHERE name = NEW.veil_3
    INTO reservation_status_3;

    IF reservation_status_1 != 'free' OR reservation_status_2 != 'free' OR reservation_status_3 != 'free' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error in gen_reservation_status management.';
    END IF;

    UPDATE veil
    SET gen_reservation_status = 'reserved'
    WHERE name IN (NEW.veil_1, NEW.veil_2, NEW.veil_3);
END;

DROP TRIGGER IF EXISTS trigger_gen_reservation_status_reservation_delete;
CREATE TRIGGER trigger_gen_reservation_status_reservation_delete
    BEFORE DELETE ON reservation FOR EACH ROW
BEGIN
    DECLARE reservation_status_1 VARCHAR(500);
    DECLARE reservation_status_2 VARCHAR(500);
    DECLARE reservation_status_3 VARCHAR(500);

    SELECT gen_reservation_status
    FROM veil
    WHERE name = OLD.veil_1
    INTO reservation_status_1;

    SELECT gen_reservation_status
    FROM veil
    WHERE name = OLD.veil_2
    INTO reservation_status_2;

    SELECT gen_reservation_status
    FROM veil
    WHERE name = OLD.veil_3
    INTO reservation_status_3;

    IF reservation_status_1 = 'free' OR reservation_status_2 = 'free' OR reservation_status_3 = 'free' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error in gen_reservation_status management.';
    END IF;

    UPDATE veil
    SET gen_reservation_status = 'free'
    WHERE gen_reservation_status = 'reserved' AND name IN (OLD.veil_1, OLD.veil_2, OLD.veil_3);
END;

DROP TRIGGER IF EXISTS trigger_gen_reservation_status_user_status_insert;
CREATE TRIGGER trigger_gen_reservation_status_user_status_insert
    AFTER INSERT ON user_status FOR EACH ROW
BEGIN
    DECLARE reservation_status VARCHAR(500);

    IF NEW.veil != NULL THEN
        SELECT gen_reservation_status
        FROM veil
        WHERE name = NEW.veil
        INTO reservation_status;

        IF reservation_status = 'taken' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error in gen_reservation_status management.';
        END IF;

        UPDATE veil
        SET gen_reservation_status = 'taken'
        WHERE name = NEW.veil; 
    END IF;
END;

DROP TRIGGER IF EXISTS trigger_gen_reservation_status_user_status_delete;
CREATE TRIGGER trigger_gen_reservation_status_user_status_delete
    BEFORE DELETE ON user_status FOR EACH ROW
BEGIN
    DECLARE reservation_status VARCHAR(500);

    IF OLD.veil != NULL THEN
        SELECT gen_reservation_status
        FROM veil
        WHERE name = OLD.veil
        INTO reservation_status;

        IF reservation_status != 'taken' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error in gen_reservation_status management.';
        END IF;

        UPDATE veil
        SET gen_reservation_status = 'free'
        WHERE name = OLD.veil; 
    END IF;
END;

DROP TRIGGER IF EXISTS trigger_gen_reservation_status_user_status_update;
CREATE TRIGGER trigger_gen_reservation_status_user_status_update
    AFTER UPDATE ON user_status FOR EACH ROW
BEGIN
    DECLARE reservation_status VARCHAR(500);

    IF OLD.veil != NULL AND NEW.veil = NULL THEN
        SELECT gen_reservation_status
        FROM veil
        WHERE name = OLD.veil
        INTO reservation_status;

        IF reservation_status != 'taken' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error in gen_reservation_status management.';
        END IF;

        UPDATE veil
        SET gen_reservation_status = 'free'
        WHERE name = OLD.veil; 
    END IF;

    IF OLD.veil = NULL AND NEW.veil != NULL THEN
        SELECT gen_reservation_status
        FROM veil
        WHERE name = NEW.veil
        INTO reservation_status;

        IF reservation_status = 'taken' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error in gen_reservation_status management.';
        END IF;

        UPDATE veil
        SET gen_reservation_status = 'taken'
        WHERE name = NEW.veil; 
    END IF;
END;

/* End of veil.gen_reservation_status management triggers. */

INSERT IGNORE INTO admin VALUES
    ('5665972958', '$2b$12$nGw4T8HrlhkrzppmMFrDq.opwqemZn7S.9BG6nTUMEGq62mi4D.GW'),
    ('5496603882', '$2b$12$nGw4T8HrlhkrzppmMFrDq.opwqemZn7S.9BG6nTUMEGq62mi4D.GW');

SET foreign_key_checks = 1;