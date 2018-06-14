use swgresource;
INSERT INTO tPlanet (planetName) VALUES ('Ghomrassen');
DELETE FROM tResourceType;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/tResourceType.txt' INTO TABLE tResourceType;
DELETE FROM tResourceTypeGroup;
LOAD DATA LOCAL INFILE '/var/www/database/seedData/typegroup.csv' INTO TABLE tResourceTypeGroup FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"';
