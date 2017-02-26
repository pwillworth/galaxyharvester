use swgresource;
ALTER TABLE tResourceTypeCreature ADD COLUMN missionLevel SMALLINT;
ALTER TABLE tResourceTypeCreature ADD COLUMN galaxy SMALLINT DEFAULT 0 NOT NULL;
ALTER TABLE tResourceTypeCreature ADD COLUMN enteredBy VARCHAR(31);
ALTER TABLE tSchematic ADD COLUMN galaxy INT DEFAULT 0 NOT NULL;
ALTER TABLE tSchematic ADD COLUMN enteredBy VARCHAR(31);

ALTER TABLE tResourceTypeCreature DROP PRIMARY KEY;
ALTER TABLE tResourceTypeCreature ADD PRIMARY KEY (resourceType, speciesName, galaxy);

ALTER TABLE tSchematic ADD INDEX IX_schem_galaxy (galaxy);
UPDATE tObjectType SET typeName = 'Other', craftingTab = 524288 WHERE objectType = 0;

ALTER TABLE tSchematicIngredients MODIFY COLUMN ingredientQuantity INT;

ALTER TABLE tSkillGroup DROP INDEX IX_profsg_sg;
ALTER TABLE tSkillGroup MODIFY COLUMN skillGroup VARCHAR(31) PRIMARY KEY;

ALTER TABLE tProfession ADD COLUMN galaxy INT DEFAULT 0 NOT NULL;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/professions_32.csv' INTO TABLE tProfession FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' (profID, profName, craftingQuality, galaxy);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSkillGroup_32.txt' INTO TABLE tSkillGroup;
ALTER TABLE tSchematicEvents DROP PRIMARY KEY (spawnID, schematicID, expGroup);
ALTER TABLE tSchematicEvents DROP INDEX spawnID;
ALTER TABLE tSchematicEvents ADD INDEX IX_schemevt_spawnschemexpgrp (spawnID, schematicID, expGroup);
