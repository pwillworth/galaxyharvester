use swgresource;
ALTER TABLE tGalaxy ADD COLUMN galaxyNGE SMALLINT DEFAULT 0;
ALTER TABLE tGalaxy ADD COLUMN submittedBy VARCHAR(31);
UPDATE tGalaxy SET galaxyNGE=1 WHERE galaxyID IN (48,74);
UPDATE tProfession SET galaxy=1337 WHERE profID=18;
UPDATE tSchematic SET galaxy=1337 WHERE galaxy=0 AND (skillGroup LIKE '%Jedi%' OR skillGroup LIKE '%Saber%');
CREATE TABLE tGalaxyUser (galaxyID INT, userID VARCHAR(31), roleType CHAR(1), INDEX IX_galaxy_user_galaxy (galaxyID), INDEX IX_galaxy_user_user (userID));
INSERT INTO tGalaxyUser (SELECT galaxyID, 'ioscode', 'a' FROM tGalaxy);
