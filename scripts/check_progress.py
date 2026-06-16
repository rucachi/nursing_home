import sqlite3
import pandas as pd
DB_PATH = r'd:\anti_gravity\nursing home\data\nursing_facilities_nationwide.db'
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT status_vworld, status_arch, COUNT(*) as cnt FROM nationwide_facilities WHERE facility_type='요양원' GROUP BY status_vworld, status_arch", conn)
print(df)
conn.close()
