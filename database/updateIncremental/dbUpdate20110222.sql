ALTER TABLE tUsers ADD COLUMN paidThrough DATETIME;
ALTER TABLE tUserStats ADD COLUMN repGood INT, ADD COLUMN repBad INT;
UPDATE tUserStats SET repGood = 0, repBad = 0;
CREATE TABLE tUserEvents (userID VARCHAR(31), targetType CHAR(1), targetID INT, eventType CHAR(1), eventTime DATETIME, INDEX IX_user_event_ttype (targetType));
ALTER TABLE tWaypoint ADD COLUMN unavailable DATETIME;
