use swgresource;
ALTER TABLE tAlerts ADD INDEX IX_alerts_status (alertStatus);
ALTER TABLE tSchematicEvents ADD PRIMARY KEY (spawnID, schematicID, expGroup);
