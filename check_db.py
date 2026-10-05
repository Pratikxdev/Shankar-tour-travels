import re
import psycopg2
from app import DSN

print("Connecting with:", re.sub(r"password=\S+", "password=****", DSN))
try:
    c = psycopg2.connect(DSN)
except Exception as e:
    msg = str(e)
    print("\nFAIL:", msg.strip())
    if "password authentication failed" in msg: print("-> DB_PASSWORD galat hai (set DB_PASSWORD=... dobara karo)")
    elif "does not exist" in msg: print("-> Database 'Shankar_travels' bana hi nahi, pgAdmin me banao")
    elif "Connection refused" in msg or "could not connect" in msg: print("-> PostgreSQL service band hai ya port galat hai (services.msc me check karo)")
    raise SystemExit(1)

cur = c.cursor()
print("Connection OK")
for t in ["settings", "admins", "cars", "bookings", "enquiries"]:
    try:
        cur.execute(f"SELECT count(*) FROM {t}")
        print(f"  {t}: {cur.fetchone()[0]} rows")
    except Exception:
        c.rollback()
        print(f"  {t}: MISSING -> schema.sql import karo")