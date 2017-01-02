use swgresource;
INSERT INTO tPlanet (planetID, planetName) VALUES (18, 'Jakku');
INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (37, 18);
DELETE FROM tResourceType;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tResourceType.txt' INTO TABLE tResourceType;
DELETE FROM tResourceTypeGroup;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/typegroup.csv' INTO TABLE tResourceTypeGroup FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"';
