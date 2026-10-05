# Shankar Tour & Travels – Cab Booking Website

Stack: HTML + CSS + JS (frontend), **Python Flask** (API + admin), PostgreSQL.

## Local run (Windows)

1. PostgreSQL install karo aur database banao: `createdb -U postgres shankar_travels` (ya pgAdmin se).
2. Schema: `psql -U postgres -d shankar_travels -f database/schema.sql`
3. `.env.example` ko copy karke naam `.env` rakho, usme apna real `DB_PASSWORD` aur baaki values bhar do (file khud explain karti hai). Yeh ek baar karna hai — uske baad har baar "set" command type karne ki zaroorat nahi, `.env` khud-ba-khud load hoti hai.
4. Project folder me:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python create_admin.py ADMIN_USERNAME APNA_PASSWORD
   python app.py
   ```
5. Site: http://localhost:8000   Admin: http://localhost:8000/admin/login

**Zaroori:** `.env` file (jisme real password/secrets hain) kabhi kisi ko mat bhejna, kahin upload/share mat karna. Sirf `.env.example` (khali template) safe hai share karne ke liye.

## WhatsApp pe booking notification (optional)

Har nayi booking/enquiry ka message tumhare WhatsApp pe aata hai. Database phir bhi seat availability sambhalta hai.

**Free option: CallMeBot**

1. https://www.callmebot.com/blog/free-api-whatsapp-messages/ kholo, wahan diya CallMeBot number apne phone me save karo.
2. Us number ko WhatsApp pe wahi line bhejo jo page pe likhi hai (`I allow callmebot to send me messages`). Wo tumhe ek **apikey** bhejega.
3. `.env` file me yeh teen lines add/uncomment karo (app restart karna padega):
   ```
   WA_MODE=callmebot
   CALLMEBOT_KEY=tumhari_apikey
   WA_TO=917678891418
   ```

**Official option: WhatsApp Cloud API (Meta)**: `.env` me `WA_MODE=cloud`, `WA_TOKEN`, `WA_PHONE_ID`, `WA_TO` daalo. Dhyan: Meta free-text message sirf 24 ghante ke window me bhejne deta hai; uske baad approved template message chahiye.

`WA_MODE` set nahi hai to notification band rehti hai.

## Live hosting

- Render / Railway / PythonAnywhere / VPS, jahan Python + PostgreSQL ho. Free PostgreSQL: Neon ya Supabase.
- Zyadatar hosting panels apna khud ka "Environment Variables" section dete hain — wahan `.env` wali hi saari values daal do (`DATABASE_URL` ya `DB_*`, `SECRET_KEY`, `DEBUG=0`). Kuch hosts (jaise HelioHost) `.env` file ko seedha upload karne dete hain — tab bas `.env.example` ko `.env` bana ke values bhar ke upload kar do.
- Local testing: `python app.py`. Real traffic ke liye (Windows): `waitress-serve --host=0.0.0.0 --port=8000 app:app` (zyada reliable, ek saath multiple log handle karta hai — dev server nahi). Linux hosting ho to: `gunicorn app:app`.
- HTTPS on rakho. `python create_admin.py ...` ek baar live DB pe chalao.

## Edit karna

- Routes/layouts/phone: `public/assets/app.js` ke top pe. Prices, cars, blocked seats: admin dashboard se.
