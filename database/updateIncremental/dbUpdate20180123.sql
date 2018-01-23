use swgresource;
ALTER TABLE tGalaxy ADD COLUMN galaxyNGE SMALLINT DEFAULT 0;
UPDATE tGalaxy SET galaxyNGE=1 WHERE galaxyID IN (48,74);
UPDATE tProfession SET galaxy=1337 WHERE profID=18;
UPDATE tSchematic SET galaxy=1337 WHERE galaxy=0 AND (skillGroup LIKE '%Jedi%' OR skillGroup LIKE '%Saber%');