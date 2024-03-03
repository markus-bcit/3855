import sqlite3

conn = sqlite3.connect('stats.sqlite')

c = conn.cursor()
c.execute('''
          CREATE TABLE WorkoutStats
          (id INTEGER PRIMARY KEY ASC, 
           num_workouts INTEGER NOT NULL,
           num_workout_logs INTEGER NOT NULL,
           max_freq_workout INTEGER NOT NULL,
           min_freq_workout INTEGER NOT NULL,
           last_update VARCHAR(100) NOT NULL)
          ''')

conn.commit()
conn.close()