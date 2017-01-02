use swgresource;
INSERT INTO tPlanet (planetID, planetName) VALUES (15, 'Mustafar');
INSERT INTO tPlanet (planetID, planetName) VALUES (16, 'Taanab');
INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (48, 15);
INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (32, 16);
DELETE FROM tResourceType;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tResourceType.txt' INTO TABLE tResourceType;
DELETE FROM tResourceTypeGroup;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/typegroup.csv' INTO TABLE tResourceTypeGroup FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"';
