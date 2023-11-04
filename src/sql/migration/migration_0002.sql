DROP TRIGGER trigger_gen_reservation_status_reservation_insert;
DROP TRIGGER trigger_gen_reservation_status_reservation_delete;
DROP TRIGGER trigger_gen_reservation_status_user_status_insert;
DROP TRIGGER trigger_gen_reservation_status_user_status_delete;
DROP TRIGGER trigger_gen_reservation_status_user_status_update;

DROP TABLE reservation;

ALTER TABLE veil DROP COLUMN gen_reservation_status;
ALTER TABLE veil ADD COLUMN reserved_by INT DEFAULT NULL;
ALTER TABLE veil ADD CONSTRAINT fk_reserved_by FOREIGN KEY (reserved_by)
    REFERENCES user_status(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE veil ADD COLUMN owned_by INT DEFAULT NULL;
ALTER TABLE veil ADD CONSTRAINT fk_owned_by FOREIGN KEY (owned_by)
    REFERENCES user_status(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE veil ADD COLUMN reservation_status VARCHAR(50) NOT NULL DEFAULT 'free';

ALTER TABLE peer_message RENAME COLUMN to_message_tid TO to_notification_tid;
ALTER TABLE peer_message ADD COLUMN to_message_tid VARCHAR(50) NOT NULL DEFAULT '?' AFTER to_notification_tid;
ALTER TABLE peer_message ADD COLUMN from_user_veil VARCHAR(500) DEFAULT NULL AFTER from_user;
UPDATE peer_message SET to_message_tid = to_notification_tid WHERE message_status = 's' AND to_message_tid = '?';

ALTER TABLE channel_message ADD COLUMN from_user_veil VARCHAR(500) DEFAULT NULL AFTER from_user;

ALTER TABLE user_status DROP COLUMN is_veiled;
ALTER TABLE user_status DROP CONSTRAINT fk_veil;
ALTER TABLE user_status DROP COLUMN veil;
ALTER TABLE user_status ADD COLUMN veil VARCHAR(500) DEFAULT NULL AFTER gen_is_admin;
ALTER TABLE user_status ADD CONSTRAINT fk_veil FOREIGN KEY (veil)
    REFERENCES veil(name)
        ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE user_status ADD COLUMN ticket INT DEFAULT 0 AFTER veil;