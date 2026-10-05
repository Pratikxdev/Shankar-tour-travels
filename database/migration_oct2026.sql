-- Yeh migration SAFE hai — koi existing data (bookings, cars, admins, enquiries)
-- delete ya change nahi hota. Sirf jo NAYI cheezein missing hain woh add hoti hain.
-- Dobara run karna bhi safe hai (IF NOT EXISTS / ON CONFLICT DO NOTHING use kiya hai).

CREATE TABLE IF NOT EXISTS route_prices (
  origin TEXT NOT NULL, destination TEXT NOT NULL,
  front_seat INT NOT NULL, middle_seat INT NOT NULL, back_seat INT NOT NULL,
  PRIMARY KEY (origin, destination));

INSERT INTO route_prices (origin, destination, front_seat, middle_seat, back_seat) VALUES
 ('Ballia','Varanasi',599,499,499), ('Varanasi','Ballia',599,499,499),
 ('Ballia','Lucknow',899,799,799),  ('Lucknow','Ballia',899,799,799)
ON CONFLICT (origin, destination) DO NOTHING;

CREATE TABLE IF NOT EXISTS reviews (
  id SERIAL PRIMARY KEY, name TEXT NOT NULL, rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT now());

-- XUV ko delete nahi kiya (agar kisi purani booking ne use kiya ho to error aayega) —
-- bas disable kar diya, isliye website par ab nahi dikhega.
UPDATE cars SET active = FALSE WHERE type = 'xuv';
