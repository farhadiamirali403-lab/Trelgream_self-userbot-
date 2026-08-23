"""Create the application database if missing (dev helper)."""
import psycopg

conn = psycopg.connect("host=localhost port=5432 user=postgres dbname=postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname='telegram_saas'")
if cur.fetchone() is None:
    cur.execute("CREATE DATABASE telegram_saas")
    print("DB_CREATED")
else:
    print("DB_EXISTS")
cur.close()
conn.close()

c2 = psycopg.connect("host=localhost port=5432 user=postgres dbname=telegram_saas")
print("CONNECTION_OK server_version=", c2.info.server_version)
c2.close()
