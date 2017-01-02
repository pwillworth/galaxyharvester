USE swgresource;
ALTER TABLE tGalaxy ADD COLUMN totalSpawns INT;
ALTER TABLE tGalaxy ADD COLUMN totalWaypoints INT;
UPDATE tGalaxy SET totalSpawns = 0, totalWaypoints = 0;
