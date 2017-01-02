use swgresource;
ALTER TABLE tResourceEvents ADD INDEX IX_res_event_type (eventType);
