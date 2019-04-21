use swgresource;

DELETE tSchematic, tSchematicIngredients, tSchematicQualities, tSchematicResWeights
 FROM tSchematic LEFT JOIN tSchematicIngredients ON tSchematic.schematicID = tSchematicIngredients.schematicID
 LEFT JOIN tSchematicQualities ON tSchematic.schematicID = tSchematicQualities.schematicID
 LEFT JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID
 WHERE tSchematic.galaxy = 0;

ALTER TABLE tSchematic MODIFY COLUMN craftingTab BIGINT;
ALTER TABLE tSchematic MODIFY COLUMN xpAmount INT;
ALTER TABLE tSchematicIngredients MODIFY COLUMN ingredientQuantity INT;
ALTER TABLE tSchematicQualities MODIFY COLUMN expProperty VARCHAR(63);

LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematic.txt' INTO TABLE tSchematic;
UPDATE tSchematic SET skillGroup='variableLooted' WHERE skillGroup='';
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicIngredients.txt' INTO TABLE tSchematicIngredients;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicQualities.txt' INTO TABLE tSchematicQualities;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicResWeights.txt' INTO TABLE tSchematicResWeights;

DELETE FROM tResourceTypeCreature WHERE galaxy=0;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tResourceTypeCreature.txt' INTO TABLE tResourceTypeCreature;
