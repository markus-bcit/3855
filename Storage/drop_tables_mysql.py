import mysql.connector
db_conn = mysql.connector.connect(host="markus-kafka.canadacentral.cloudapp.azure.com", user="user",
                                  password="password", database="events", auth_plugin='mysql_native_password')
db_cursor = db_conn.cursor()
db_cursor.execute('''
                  DROP TABLE workout, workoutLog
                  ''')
db_conn.commit()
db_conn.close()
