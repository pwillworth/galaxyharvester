use swgresource;
ALTER TABLE tUsers ADD COLUMN emailChange VARCHAR(255);
UPDATE tResourceType SET PEmax=1000, OQmin=1, OQmax=1000 WHERE resourceType LIKE '%geothermal%';
UPDATE tResourceType SET specificPlanet=18 WHERE resourceType LIKE '%jakk%';
