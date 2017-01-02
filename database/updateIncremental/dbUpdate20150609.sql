USE swgresource;
CREATE TABLE tFeedback (feedbackID INT AUTO_INCREMENT PRIMARY KEY, entered DATETIME NOT NULL, userID VARCHAR(31), feedback VARCHAR(1023), feedbackState TINYINT DEFAULT 0 NOT NULL, INDEX IX_feedback_entered (entered));
CREATE TABLE tFeedbackVotes (feedbackID INT NOT NULL, entered DATETIME NOT NULL, userID VARCHAR(31), vote TINYINT, PRIMARY KEY (feedbackID, userID));
CREATE TABLE tFeedbackComments (commentID INT AUTO_INCREMENT PRIMARY KEY, feedbackID INT NOT NULL, entered DATETIME NOT NULL, userID VARCHAR(31), comment VARCHAR(1023), INDEX IX_feedbackcomments_feedback (feedbackID));


GRANT SELECT,INSERT,UPDATE,DELETE ON swgresource.tFeedback TO webusr;
GRANT SELECT,INSERT,UPDATE,DELETE ON swgresource.tFeedbackVotes TO webusr;
GRANT SELECT,INSERT,UPDATE,DELETE ON swgresource.tFeedbackComments TO webusr;

LOAD DATA LOCAL INFILE '/var/www/database/feedback.txt' INTO TABLE tFeedback (feedbackID, entered, userID, feedback);
LOAD DATA LOCAL INFILE '/var/www/database/votes.csv' INTO TABLE tFeedbackVotes FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' (feedbackID, entered, userID, vote);
LOAD DATA LOCAL INFILE '/var/www/database/comments.csv' INTO TABLE tFeedbackComments FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' (commentID, feedbackID, entered, userID, comment);
LOAD DATA LOCAL INFILE '/var/www/database/tResourceType.txt' INTO TABLE tResourceType;

UPDATE tFeedback SET feedbackState = 1;