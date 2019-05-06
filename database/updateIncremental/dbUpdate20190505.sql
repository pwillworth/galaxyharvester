use swgresource;
ALTER TABLE tUsers ADD COLUMN emailVerifyDate DATETIME;
ALTER TABLE tUsers ADD COLUMN emailVerifyIP VARCHAR(39);
