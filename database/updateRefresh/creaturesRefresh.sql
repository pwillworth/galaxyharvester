use swgresource;
DELETE FROM tResourceTypeCreature;

LOAD DATA LOCAL INFILE '/var/www/database/seedData/tResourceTypeCreature.txt' INTO TABLE tResourceTypeCreature (resourceType, speciesName, maxAmount);
