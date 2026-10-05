"""Use: python migrate.py
Missing tables (route_prices, reviews) add karta hai aur XUV car disable karta hai.
Existing data (bookings, cars, admins, enquiries) ko bilkul touch nahi karta — safe hai,
dobara bhi chala sakte ho."""
import pathlib
from app import connect

sql = pathlib.Path(__file__).parent.joinpath("database", "migration_oct2026.sql").read_text(encoding="utf-8")

with connect() as c, c.cursor() as cur:
    cur.execute(sql)
print("Migration ho gaya — route_prices aur reviews tables ab maujood hain, XUV disable ho gayi.")
