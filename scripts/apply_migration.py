import psycopg2
import sys

from db_config import DB_CONNECTIONS

connections = DB_CONNECTIONS

conn = None
for conn_string in connections:
    try:
        conn = psycopg2.connect(conn_string, connect_timeout=15)
        print("Connected via:", conn_string.split("@")[1][:40])
        break
    except Exception as e:
        print("Failed:", str(e)[:80])

if not conn:
    print("ERROR: Could not connect to database")
    sys.exit(1)


with open('supabase/migrations/001_initial_schema.sql', 'r') as f:
    sql = f.read()

try:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql)
    print("Migration applied successfully!")
    
    # Verify tables were created
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print("\nTables created:")
    for t in tables:
        print(f"  - {t[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
