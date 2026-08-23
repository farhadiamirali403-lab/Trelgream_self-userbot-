import psycopg

PLANS = [
    ("basic", "30 روزه", 30),
    ("pro", "60 روزه", 60),
    ("premium", "90 روزه", 90),
    ("business", "360 روزه", 360),
]

c = psycopg.connect("host=localhost user=postgres dbname=telegram_saas")
cur = c.cursor()
for key, name, days in PLANS:
    cur.execute("UPDATE plans SET name=%s, duration_days=%s WHERE key=%s", (name, days, key))
c.commit()

cur.execute("SELECT key, name, price, duration_days FROM plans ORDER BY sort_order")
for row in cur.fetchall():
    print(row[0], "|", row[1], "|", row[2], "|", row[3])
c.close()
print("PLANS_UPDATED")
