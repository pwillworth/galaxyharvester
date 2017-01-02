USE swgresource;
ALTER TABLE tResourceType ADD COLUMN specificPlanet SMALLINT NOT NULL DEFAULT 0;
UPDATE tResourceType SET specificPlanet = 1 WHERE resourceTypeName LIKE 'Corellian%';
UPDATE tResourceType SET specificPlanet = 2 WHERE resourceTypeName LIKE 'Dantooi%';
UPDATE tResourceType SET specificPlanet = 3 WHERE resourceTypeName LIKE 'Dathomir%';
UPDATE tResourceType SET specificPlanet = 4 WHERE resourceTypeName LIKE 'Endor%';
UPDATE tResourceType SET specificPlanet = 5 WHERE resourceTypeName LIKE 'Lok%';
UPDATE tResourceType SET specificPlanet = 6 WHERE resourceTypeName LIKE 'Naboo%';
UPDATE tResourceType SET specificPlanet = 7 WHERE resourceTypeName LIKE 'Rori%';
UPDATE tResourceType SET specificPlanet = 8 WHERE resourceTypeName LIKE 'Talus%';
UPDATE tResourceType SET specificPlanet = 9 WHERE resourceTypeName LIKE 'Tatooin%';
UPDATE tResourceType SET specificPlanet = 10 WHERE resourceTypeName LIKE 'Yavin%';
UPDATE tResourceType SET specificPlanet = 11 WHERE resourceTypeName LIKE 'Hoth%';
UPDATE tResourceType SET specificPlanet = 12 WHERE resourceTypeName LIKE 'Kaas%';
UPDATE tResourceType SET specificPlanet = 13 WHERE resourceTypeName LIKE 'Kashyy%';

ALTER TABLE tSessions ADD COLUMN pushKey VARCHAR(255);
