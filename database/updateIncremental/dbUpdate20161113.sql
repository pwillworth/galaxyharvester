use swgresource;
ALTER TABLE tUserEvents ADD COLUMN causeEventType CHAR(1);
ALTER TABLE tUserEvents ADD INDEX IX_user_event_user_type (userID, eventType);
