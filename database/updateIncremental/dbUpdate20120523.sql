use swgresource;
INSERT INTO tResourceGroupCategory (resourceGroup, resourceCategory) VALUES ('inorganic','resource');
INSERT INTO tResourceGroupCategory (resourceGroup, resourceCategory) VALUES ('organic','resource');
DELETE FROM tResourceTypeCreature;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tResourceTypeCreature.txt' INTO TABLE tResourceTypeCreature;
