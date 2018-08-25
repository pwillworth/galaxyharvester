use swgresource;
ALTER TABLE tResources ADD INDEX IX_res_galaxy_restype (galaxy, resourceType);
