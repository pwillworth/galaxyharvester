use swgresource;
DELETE FROM tSchematic;
DELETE FROM tSchematicIngredients;
DELETE FROM tSchematicQualities;
DELETE FROM tSchematicResWeights;

LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematic.txt' INTO TABLE tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicIngredients.txt' INTO TABLE tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicQualities.txt' INTO TABLE tSchematicQualities (expQualityID, schematicID, expProperty, expGroup, weightTotal);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicResWeights.txt' INTO TABLE tSchematicResWeights (expQualityID, statName, statWeight);

