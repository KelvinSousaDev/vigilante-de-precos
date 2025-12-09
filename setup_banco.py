import sqlite3

conn = sqlite3.connect('precos.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS historico_precos (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               produto TEXT,
               valor REAL,
               loja TEXT,
               data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
''')

conn.commit()
conn.close()
print("Banco 'precos.db' criado!")