USE swgresource;
UPDATE tSchematic SET skillGroup='variableLooted' WHERE skillGroup='';
ALTER TABLE tFilters ADD COLUMN minQuality SMALLINT;
