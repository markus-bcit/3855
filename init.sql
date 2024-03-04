CREATE TABLE IF NOT EXISTS workout (
    id INT NOT NULL AUTO_INCREMENT, 
    type VARCHAR(50) NOT NULL,
    startDate VARCHAR(100) NOT NULL,
    endDate VARCHAR(100) NOT NULL,
    frequency INT NOT NULL,
    dateCreated VARCHAR(100) NOT NULL,
    traceId VARCHAR(250) NOT NULL,
    CONSTRAINT workoutId PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS workoutLog (
    id INT NOT NULL AUTO_INCREMENT, 
    workoutId VARCHAR(250) NOT NULL,
    userId VARCHAR(250) NOT NULL,
    startDate VARCHAR(100) NOT NULL,
    endDate VARCHAR(100) NOT NULL,
    exercises VARCHAR(250) NOT NULL,
    dateCreated VARCHAR(100) NOT NULL,
    traceId VARCHAR(250) NOT NULL,
    CONSTRAINT workoutLogId PRIMARY KEY (id)
);