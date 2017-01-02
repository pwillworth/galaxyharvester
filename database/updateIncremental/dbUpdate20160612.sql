use swgresource;
CREATE TABLE tSchematicEvents (galaxy SMALLINT, eventTime DATETIME, eventType CHAR(1), schematicID VARCHAR(127), expGroup VARCHAR(31), spawnID INT, eventDetail VARCHAR(1023), INDEX IX_schemevt_galaxy (galaxy), INDEX IX_schemevt_galaxy_eventtime (galaxy, eventTime), INDEX IX_schemevt_galaxy_schem (galaxy, schematicID), INDEX IX_schemevt_spawn (spawnID));
ALTER TABLE tProfession ADD COLUMN craftingQuality INT;
UPDATE tProfession SET craftingQuality = 0;
UPDATE tProfession SET craftingQuality = 1 WHERE profID IN (1,3,5,6,7,8,9,10,11,14,15,17,18);
ALTER TABLE tFavorites ADD COLUMN galaxy INT;
ALTER TABLE tFavorites ADD INDEX IX_fav_group (favGroup);
ALTER TABLE tUsers ADD COLUMN defaultAlertTypes SMALLINT NOT NULL DEFAULT 3;
