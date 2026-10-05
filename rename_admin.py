"""Use: python rename_admin.py old_username new_username [new_password]
Password optional hai — agar nahi doge to purana password hi chalta rahega."""
import sys
from werkzeug.security import generate_password_hash
from app import connect

if len(sys.argv) not in (3, 4):
    sys.exit("Use: python rename_admin.py old_username new_username [new_password]")

old, new = sys.argv[1], sys.argv[2]
with connect() as c, c.cursor() as cur:
    if len(sys.argv) == 4:
        cur.execute("UPDATE admins SET username=%s, password_hash=%s WHERE username=%s",
                     (new, generate_password_hash(sys.argv[3]), old))
    else:
        cur.execute("UPDATE admins SET username=%s WHERE username=%s", (new, old))
    if cur.rowcount == 0:
        sys.exit(f"'{old}' naam ka admin mila nahi — username sahi likha hai? (python check_db.py se list dekho)")
print(f"Admin '{old}' ka naam ab '{new}' ho gaya.")
