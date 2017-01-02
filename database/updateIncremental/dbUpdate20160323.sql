USE swgresource;
ALTER TABLE tResourceEvents ADD COLUMN galaxy SMALLINT;
UPDATE tResourceEvents SET galaxy=(SELECT galaxy FROM tResources WHERE tResources.spawnID = tResourceEvents.spawnID);
ALTER TABLE tResourceEvents ADD INDEX IX_res_galaxy (galaxy);
ALTER TABLE tResourceEvents ADD INDEX IX_res_galaxy_event_time (galaxy, eventTime);
