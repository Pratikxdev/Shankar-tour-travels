"""Use: python whoami_admin.py
Dikhata hai ki abhi database me kaun-kaun se admin username bane hue hain, aur
app.py KAUNSE database se connect ho raha hai (taaki pata chale agar galat
database use ho raha ho). Password kabhi nahi dikhega — woh hashed save hota
hai, isiliye wapas nahi dekha ja sakta. Bhool gaye ho to reset karo:
  python create_admin.py username NayaPassword"""
import re
from app import DSN, connect

print("Yeh database use ho raha hai:", re.sub(r"password=\S+", "password=****", DSN))
try:
    with connect() as c, c.cursor() as cur:
        cur.execute("SELECT username FROM admins ORDER BY username")
        rows = cur.fetchall()
except Exception as e:
    raise SystemExit(f"\nConnect nahi ho paya: {e}\n-> Yeh WAHI env vars (DB_HOST/DB_NAME/...) set karke chalao jisse 'python app.py' chalate ho, varna galat database check ho jayega.")

if not rows:
    print("\nKoi admin hai hi nahi is database me! Banao: python create_admin.py username password")
else:
    print(f"\n{len(rows)} admin username(s) mile:")
    for r in rows: print(" -", r["username"])
