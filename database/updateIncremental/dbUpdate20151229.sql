USE swgresource;
ALTER TABLE tUsers ADD COLUMN userState SMALLINT NOT NULL DEFAULT 0;
ALTER TABLE tUsers ADD COLUMN verificationCode VARCHAR(32);
UPDATE tUsers SET userState = 2;
