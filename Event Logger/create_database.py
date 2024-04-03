import sqlite3

conn = sqlite3.connect('stats.sqlite')

c = conn.cursor()
c.execute('''
          CREATE TABLE events
          (id INTEGER PRIMARY KEY ASC, 
           0001 INTEGER NOT NULL,
           0002 INTEGER NOT NULL,
           0003 INTEGER NOT NULL,
           0004 INTEGER NOT NULL,
           last_update VARCHAR(100) NOT NULL)
          ''')

conn.commit()
conn.close()