import sqlite3

conn = sqlite3.connect('stats.sqlite')

c = conn.cursor()
c.execute('''
          CREATE TABLE events
          (id INTEGER PRIMARY KEY ASC, 
           one INTEGER NOT NULL,
           two INTEGER NOT NULL,
           three INTEGER NOT NULL,
           four INTEGER NOT NULL,
           last_update VARCHAR(100) NOT NULL)
          ''')

conn.commit()
conn.close()