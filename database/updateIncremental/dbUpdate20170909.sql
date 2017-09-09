use swgresource;
CREATE TABLE tServerBestStatus (galaxy SMALLINT, eventTime DATETIME, eventType CHAR(1), schematicID VARCHAR(127), expGroup VARCHAR(31), spawnID INT, eventDetail VARCHAR(1023), INDEX IX_sbstat_spawnschemexpgrp (spawnID, schematicID, expGroup), INDEX IX_sbstat_galaxy (galaxy), INDEX IX_sbstat_galaxy_eventtime (galaxy, eventTime), INDEX IX_sbstat_galaxy_schem (galaxy, schematicID), INDEX IX_sbstat_spawn (spawnID));
ALTER TABLE tFilters ADD COLUMN fltGroup VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE tFilters ADD INDEX IX_filter_user_group (userID, fltGroup);
