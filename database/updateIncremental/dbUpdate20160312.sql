use swgresource;
ALTER TABLE tResources ADD INDEX IX_res_galaxy (galaxy);
ALTER TABLE tResources ADD INDEX IX_res_id_galaxy (spawnID, galaxy);
