use swgresource;
ALTER TABLE tSchematicIngredients ADD INDEX IX_scheming_object (ingredientObject);
ALTER TABLE tSchematic ADD INDEX IX_schem_skill (skillGroup);
ALTER TABLE tWaypoint ADD INDEX IX_waypoint_spawnid (spawnID);
