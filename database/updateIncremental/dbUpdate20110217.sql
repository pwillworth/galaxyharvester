ALTER TABLE tUserStats ADD COLUMN waypoint INT AFTER verified;
UPDATE tUserStats SET waypoint=0;
INSERT INTO tResourceEvents (spawnID, userID, eventTime, eventType, planetID) (SELECT spawnID,owner,entered,'w',planetID FROM tWaypoint WHERE waypointType='u');
UPDATE tUserStats SET waypoint=(SELECT Count(eventTime) FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID=tResources.spawnID WHERE tResourceEvents.eventType='w' AND tResourceEvents.userID=tUserStats.userID AND tResources.galaxy=tUserStats.galaxy);
