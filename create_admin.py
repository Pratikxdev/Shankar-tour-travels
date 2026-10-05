"""Use: python create_admin.py username password"""
import sys
from werkzeug.security import generate_password_hash
from app import connect
if len(sys.argv) != 3: sys.exit("Use: python create_admin.py username password")
with connect() as c, c.cursor() as cur:
    cur.execute("INSERT INTO admins(username,password_hash) VALUES(%s,%s) ON CONFLICT (username) DO UPDATE SET password_hash=EXCLUDED.password_hash",
                (sys.argv[1], generate_password_hash(sys.argv[2])))
print(f"Admin '{sys.argv[1]}' ready.")
