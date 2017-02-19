use swgresource;
ALTER TABLE tResourceTypeCreature ADD COLUMN missionLevel SMALLINT;
ALTER TABLE tResourceTypeCreature ADD COLUMN galaxy SMALLINT DEFAULT 0 NOT NULL;
ALTER TABLE tResourceTypeCreature ADD COLUMN enteredBy VARCHAR(31);
ALTER TABLE tSchematic ADD COLUMN galaxy SMALLINT DEFAULT 0 NOT NULL;
ALTER TABLE tSchematic ADD COLUMN enteredBy VARCHAR(31);

ALTER TABLE tResourceTypeCreature DROP PRIMARY KEY;
ALTER TABLE tResourceTypeCreature ADD PRIMARY KEY (resourceType, speciesName, galaxy);

ALTER TABLE tSchematic ADD INDEX IX_schem_galaxy (galaxy);
UPDATE tObjectType SET typeName = 'Other', craftingTab = 524288 WHERE objectType = 0;
