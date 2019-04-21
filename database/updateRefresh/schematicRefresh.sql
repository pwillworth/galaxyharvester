use swgresource;
DELETE tSchematic, tSchematicIngredients, tSchematicQualities, tSchematicResWeights
 FROM tSchematic LEFT JOIN tSchematicIngredients ON tSchematic.schematicID = tSchematicIngredients.schematicID
 LEFT JOIN tSchematicQualities ON tSchematic.schematicID = tSchematicQualities.schematicID
 LEFT JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID
 WHERE tSchematic.galaxy = 0;

LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematic.txt' INTO TABLE tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicIngredients.txt' INTO TABLE tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicQualities.txt' INTO TABLE tSchematicQualities (expQualityID, schematicID, expProperty, expGroup, weightTotal);
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tSchematicResWeights.txt' INTO TABLE tSchematicResWeights (expQualityID, statName, statWeight);

