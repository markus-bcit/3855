import mysql.connector
db_conn = mysql.connector.connect(host="markus-kafka.canadacentral.cloudapp.azure.com", user="user",
                                  password="password", auth_plugin='mysql_native_password')
db_cursor = db_conn.cursor()
db_cursor.execute('''
          CREATE DATABASE IF NOT EXISTS events;
          USE events;
           ''')
db_cursor.execute('''
          CREATE TABLE workout
          (id INT NOT NULL AUTO_INCREMENT, 
           type VARCHAR(50) NOT NULL,
           startDate VARCHAR(100) NOT NULL,
           endDate VARCHAR(100) NOT NULL,
           frequency INT NOT NULL,
           dateCreated VARCHAR(100) NOT NULL,
           traceId VARCHAR(250) NOT NULL,
           CONSTRAINT workoutId PRIMARY KEY (id))
          ''')
db_cursor.execute('''
          CREATE TABLE workoutLog
          (id INT NOT NULL AUTO_INCREMENT, 
           workoutId VARCHAR(250) NOT NULL,
           userId VARCHAR(250) NOT NULL,
           startDate VARCHAR(100) NOT NULL,
           endDate VARCHAR(100) NOT NULL,
           exercises VARCHAR(250) NOT NULL,
           dateCreated VARCHAR(100) NOT NULL,
           traceId VARCHAR(250) NOT NULL,
           CONSTRAINT workoutLogId PRIMARY KEY (id))
           ''')
db_conn.commit()
db_conn.close()
