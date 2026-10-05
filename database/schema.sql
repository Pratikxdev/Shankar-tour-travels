CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT INTO settings VALUES
 ('front_seat','899'),('middle_seat','799'),('back_seat','799'),
 ('per_day','2500'),('follow_discount','50');

CREATE TABLE admins (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);

CREATE TABLE cars (
  id SERIAL PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL CHECK (type IN ('sedan','dzire')),
  plate TEXT, driver TEXT, ac BOOLEAN DEFAULT TRUE, blocked_seats TEXT DEFAULT '', active BOOLEAN DEFAULT TRUE);
INSERT INTO cars (name,type,plate,driver) VALUES
 ('Swift Dzire','dzire','UP60 AA 0001','Driver 1'),
 ('Honda Amaze (Sedan)','sedan','UP60 AA 0002','Driver 2');

CREATE TABLE bookings (
  id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, mobile TEXT NOT NULL, email TEXT,
  car_id INT NOT NULL REFERENCES cars(id), seat TEXT NOT NULL, origin TEXT NOT NULL, destination TEXT NOT NULL,
  travel_date DATE NOT NULL, travel_time TEXT, amount INT NOT NULL, discount INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Confirmed','Cancelled')),
  created_at TIMESTAMPTZ DEFAULT now());
-- ek seat ek car/date/origin pe sirf ek baar book ho sakti hai (double booking rokta hai)
CREATE UNIQUE INDEX one_seat_once ON bookings (car_id, seat, origin, travel_date) WHERE status <> 'Cancelled';

CREATE TABLE enquiries (
  id SERIAL PRIMARY KEY, service TEXT NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL,
  pickup TEXT, drop_or_venue TEXT, travel_date DATE, travel_time TEXT, details TEXT, created_at TIMESTAMPTZ DEFAULT now());

-- Route (origin -> destination) ke hisaab se alag pricing. Agar kisi route ke
-- liye yahan row NAHI hai, to woh route upar wale global "settings" price use
-- karta hai (default). Abhi sirf Ballia->Varanasi aur Ballia->Lucknow fix hain;
-- baaki sab routes (Ballia ke doosre destinations, aur Varanasi/Lucknow se
-- shuru hone wale saare routes) jaan-bujhkar KHAALI rakhe hain — admin
-- dashboard ke "Route Pricing" section se Aditya ji se rate confirm karke
-- set karna hoga.
CREATE TABLE route_prices (
  origin TEXT NOT NULL, destination TEXT NOT NULL,
  front_seat INT NOT NULL, middle_seat INT NOT NULL, back_seat INT NOT NULL,
  PRIMARY KEY (origin, destination));
INSERT INTO route_prices (origin, destination, front_seat, middle_seat, back_seat) VALUES
 ('Ballia','Varanasi',599,499,499), ('Varanasi','Ballia',599,499,499),
 ('Ballia','Lucknow',899,799,799),  ('Lucknow','Ballia',899,799,799);

-- Customer reviews (star rating ke saath). Naya review pehle "approved=false" rehta
-- hai — admin dashboard se ek baar dekh/approve karne ke baad hi website par
-- public ko dikhta hai (spam/fake review se bachne ke liye).
CREATE TABLE reviews (
  id SERIAL PRIMARY KEY, name TEXT NOT NULL, rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT now());
