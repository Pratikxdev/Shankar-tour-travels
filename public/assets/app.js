// ====== Easy-to-edit settings ======
const PHONE = '917678891418';
const ROUTES = { // kahan se kahan tak (yahan badal sakte ho)
  Ballia: ['Varanasi','Gorakhpur','Azamgarh','Mau','Lucknow','Chapra','Buxar','Local'],
  Varanasi: ['Ballia','Gorakhpur','Azamgarh','Mau','Lucknow'],
  Lucknow: ['Ballia','Varanasi','Gorakhpur','Azamgarh']
};
const LAYOUTS = { sedan: [['F1'],['M1','M2','M3']], dzire: [['F1'],['M1','M2','M3']] };
const CAR_IMG = { sedan: 'assets/cars/sedan.svg', dzire: 'assets/cars/dzire.svg' };
const POS = { F: 'Front Seat', M: 'Middle Seat', B: 'Back Seat' };
// ===================================
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inr = n => '₹' + Number(n).toLocaleString('en-IN');
const S = { cars: [], car: null, seat: null, booked: [], prices: { F: 899, M: 799, B: 799 }, perDay: 2500, disc: 50 };
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 6e4).toISOString().slice(0, 10);

function toast(m) { const t = $('toast'); t.textContent = m; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => t.hidden = true, 3200); }
async function api(path, body) {
  const r = await fetch('/api/' + path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {});
  const d = await r.json().catch(() => ({ error: 'Server se jawab nahi mila.' }));
  if (!r.ok) throw new Error(d.error || 'Kuch galat hua.'); return d;
}
const opts = (el, list, keep) => { el.innerHTML = list.map(v => `<option>${esc(v)}</option>`).join(''); if (list.includes(keep)) el.value = keep; };
const seatPrice = id => S.prices[id[0]];
const dateFmt = d => d.split('-').reverse().join('/');

function fillDest(o, d) { opts(d, ROUTES[o.value], d.value); }
function initSelects() {
  for (const [o, d] of [['origin', 'dest'], ['hOrigin', 'hDest']]) {
    opts($(o), Object.keys(ROUTES)); fillDest($(o), $(d));
    $(o).onchange = () => { fillDest($(o), $(d)); if (o === 'origin') { S.seat = null; loadSeats(); } };
  }
  ['date', 'hDate', 'edate'].forEach(i => { $(i).min = today; }); $('date').value = $('hDate').value = today;
  $('dest').onchange = () => { S.seat = null; loadSeats(); };
  $('date').onchange = () => { S.seat = null; loadSeats(); };
}

async function init() {
  initSelects(); renderServices();
  try {
    const d = await api('cars'); Object.assign(S, { cars: d.cars, prices: d.prices, perDay: d.per_day, disc: d.discount });
    document.querySelectorAll('.pf').forEach(e => e.textContent = S.prices.F); document.querySelectorAll('.pm').forEach(e => e.textContent = S.prices.M);
    $('disc').textContent = S.disc; renderServices(); renderCars(); if (S.cars.length) pickCar(S.cars[0].id);
    else $('cars').innerHTML = '<p class="muted">Abhi koi car available nahi hai. Call karke poocho.</p>';
  } catch (e) { $('cars').innerHTML = `<p class="err">Cars load nahi hue: ${esc(e.message)}</p>`; }
}

function renderServices() {
  const wa = t => `https://wa.me/${PHONE}?text=${encodeURIComponent(t)}`;
  const list = [
    ['🚕', 'Sharing Cab', `Starting ${inr(S.prices.M)} per seat`, 'Apni seat khud chuno. Ballia, Varanasi, Lucknow se.', '#book'],
    ['🚗', 'Full Car Booking', 'Get Price / Request Quote', 'Poori car apne parivar ya group ke liye.', 'Full Car Booking'],
    ['📅', 'Monthly Car Rental', `Per day: ${inr(S.perDay)} + fuel`, 'Driver ke saath, personal ya office use. Final price car aur duration pe depend karta hai.', 'Monthly Rental'],
    ['💍', 'Wedding Car Booking', 'Request Quote', 'Sedan, SUV aur premium cars, decoration ke saath.', 'Wedding Booking'],
    ['🛣️', 'One-Way Drop', 'Get Price · 300 KM minimum', 'All India one-way dropping service.', 'One Way Drop'],
    ['✈️', 'Airport Pick-up & Drop', 'Request Quote', 'Flight time ke hisaab se pickup aur drop.', 'Airport Transfer']];
  $('svc').innerHTML = list.map(([ic, t, p, d, k]) => `<div class="card svc"><div class="ic">${ic}</div><h3>${t}</h3><div class="price">${p}</div><p class="muted">${d}</p>
    <div class="row"><a class="btn gold sm" href="${k.startsWith('#') ? k : '#enquiry'}" data-svc="${k.startsWith('#') ? '' : k}">Book Now</a>
    <a class="btn sm" target="_blank" rel="noopener" href="${wa('Hello, mujhe ' + t + ' ke baare me jaankari chahiye.')}">View Details</a></div></div>`).join('');
  document.querySelectorAll('[data-svc]').forEach(a => a.onclick = () => { if (a.dataset.svc) $('esvc').value = a.dataset.svc; });
}

function renderCars() {
  $('cars').innerHTML = S.cars.map(c => `<button class="car ${S.car?.id === c.id ? 'on' : ''}" data-id="${c.id}">
    <img src="${CAR_IMG[c.type] || ''}" alt="${esc(c.name)}" class="carimg" loading="lazy">
    <b>${esc(c.name)}</b><small>${c.type.toUpperCase()} · ${LAYOUTS[c.type].flat().length} seats · ${c.ac ? 'AC' : 'Non-AC'}</small><br><small>Driver included</small></button>`).join('');
  document.querySelectorAll('.car').forEach(b => b.onclick = () => pickCar(+b.dataset.id));
}
function pickCar(id) { S.car = S.cars.find(c => c.id === id); S.seat = null; renderCars(); loadSeats(); }

async function loadSeats() {
  if (!S.car) return;
  try {
    const d = await api(`seats?car_id=${S.car.id}&origin=${encodeURIComponent($('origin').value)}&destination=${encodeURIComponent($('dest').value)}&date=${$('date').value}`);
    S.booked = d.booked; S.prices = d.prices;   // is route ke seat-prices (route-specific ho sakte hain)
  } catch (e) { S.booked = []; toast(e.message); }
  renderSeats(); renderSummary();
}

function status(id) {
  if ((S.car.blocked_seats || '').split(',').includes(id)) return 'n';
  if (S.booked.includes(id)) return 'b'; return S.seat === id ? 's' : 'v';
}
function renderSeats() {
  const rows = LAYOUTS[S.car.type].map((r, i) => `<div class="srow">${i === 0 ? '<div class="wheel">DRIVER</div>' : ''}${r.map(id => {
    const st = status(id), label = { v: inr(seatPrice(id)), b: 'BOOKED', n: 'N/A', s: inr(seatPrice(id)) }[st];
    return `<button class="seat ${st}" data-id="${id}" aria-label="Seat ${id} ${label}">${id}<small>${label}</small></button>`; }).join('')}</div>`).join('');
  $('seatmap').innerHTML = rows; $('seatNote').textContent = `${S.car.name} · ${dateFmt($('date').value)}`;
  document.querySelectorAll('.seat').forEach(b => b.onclick = () => seatClick(b.dataset.id));
}
function seatDetail(id) {
  const row = LAYOUTS[S.car.type].find(r => r.includes(id)), i = row.indexOf(id);
  return row.length === 1 ? 'Window seat (next to driver)' : i === 1 ? 'Center seat' : i === 0 ? 'Left window seat' : 'Right window seat';
}
function seatClick(id) {
  const st = status(id);
  if (st === 'b') return toast('Seat already booked');
  if (st === 'n') return toast('Ye seat available nahi hai');
  $('mbox').innerHTML = `<h3>Seat ${id}</h3><div class="sumline"><span>Position</span><b>${POS[id[0]]}</b></div><div class="sumline"><span>Type</span><b>${seatDetail(id)}</b></div>
    <div class="sumline"><span>Status</span><b>Available</b></div><div class="sumline"><span>Price</span><b>${inr(seatPrice(id))}</b></div>
    <div class="row"><button class="btn gold" id="mok">Select Seat</button><button class="btn ghost dark" id="mno">Close</button></div>`;
  $('modal').hidden = false; $('mok').focus();
  $('mok').onclick = () => { S.seat = id; $('modal').hidden = true; renderSeats(); renderSummary(); };
  $('mno').onclick = () => $('modal').hidden = true;
}
$('modal').onclick = e => { if (e.target.id === 'modal') $('modal').hidden = true; };
document.addEventListener('keydown', e => { if (e.key === 'Escape') $('modal').hidden = true; });

function renderSummary() {
  if (!S.car || !S.seat) { $('summary').innerHTML = 'Pehle car aur seat chuno.'; $('pform').hidden = true; return; }
  const p = seatPrice(S.seat), l = (k, v) => `<div class="sumline"><span>${k}</span><b>${esc(v)}</b></div>`;
  $('summary').innerHTML = l('Car', S.car.name) + l('Trip', 'Sharing Cab') + l('Seat', `${S.seat} (${POS[S.seat[0]]})`) +
    l('Route', `${$('origin').value} → ${$('dest').value}`) + l('Date', dateFmt($('date').value)) + l('Pickup time', 'Call/WhatsApp par confirm hoga') + l('Base fare', inr(p)) + l('Taxes/Charges', '₹0') +
    `<div class="tot"><span>Total</span><span>${inr(p)}</span></div><p class="muted">Follow discount checkout pe lagega.</p>`;
  $('pform').hidden = false;
}

$('pform').onsubmit = async e => {
  e.preventDefault(); const btn = e.submitter; btn.disabled = true;
  try {
    const d = await api('book', { car_id: S.car.id, seat: S.seat, origin: $('origin').value, destination: $('dest').value, date: $('date').value,
      name: $('pname').value, mobile: $('pmobile').value, email: $('pemail').value, follows: $('pfollow').checked });
    showTicket(d); S.seat = null; loadSeats(); toast('Booking confirmed!');
  } catch (err) { toast(err.message); if (/book kar li/.test(err.message)) { S.seat = null; loadSeats(); } }
  btn.disabled = false;
};
function showTicket(d) {
  const t = $('ticket'), r = (k, v) => `<div class="sumline"><span>${k}</span><b>${esc(v)}</b></div>`;
  const msg = `Booking ${d.code}\n${$('pname').value}\n${S.car.name}, Seat ${d.seat}\n${$('origin').value} → ${$('dest').value}\n${dateFmt($('date').value)}\nAmount ${inr(d.total)}`;
  t.innerHTML = `<h3>SHANKAR TOUR & TRAVELS</h3><div class="ok">✓ Booking Confirmed</div>` + r('Booking ID', d.code) + r('Passenger', $('pname').value) + r('Mobile', $('pmobile').value) +
    r('Car / Seat', `${d.car} / ${d.seat}`) + r('Route', `${$('origin').value} → ${$('dest').value}`) + r('Date', dateFmt($('date').value)) +
    r('Base fare', inr(d.base)) + (d.discount ? r('First-booking discount', '-' + inr(d.discount)) : '') + `<div class="tot"><span>Amount</span><span>${inr(d.total)}</span></div>
    <p class="muted">Pickup time ke liye hum aapko jald call/WhatsApp karenge. Payment travel ke time driver ko karo. Follow discount ke liye Instagram/Facebook page dikhana pad sakta hai.</p>
    <div class="row"><button class="btn gold" onclick="window.print()">Download / Print Ticket</button>
    <a class="btn wa" target="_blank" rel="noopener" href="https://wa.me/${PHONE}?text=${encodeURIComponent(msg)}">WhatsApp Booking</a><a class="btn" href="tel:+${PHONE}">Call Support</a></div>`;
  t.hidden = false; $('pform').reset(); t.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

$('heroForm').onsubmit = e => {
  e.preventDefault(); $('origin').value = $('hOrigin').value; fillDest($('origin'), $('dest')); $('dest').value = $('hDest').value; $('date').value = $('hDate').value;
  S.seat = null; loadSeats(); $('book').scrollIntoView({ behavior: 'smooth' });
};
const enqText = () => `*${$('esvc').value}*\nName: ${$('ename').value}\nPhone: ${$('ephone').value}\nPickup: ${$('epick').value}\nDrop/Venue: ${$('edrop').value}\nDate: ${$('edate').value} ${$('etime').value}\n${$('edet').value}`;
$('eform').onsubmit = async e => {
  e.preventDefault();
  try { await api('enquiry', { service: $('esvc').value, name: $('ename').value, phone: $('ephone').value, pickup: $('epick').value, drop: $('edrop').value, date: $('edate').value, time: $('etime').value, details: $('edet').value });
    toast('Enquiry mil gayi. Hum jald call karenge.'); $('eform').reset(); } catch (err) { toast(err.message); }
};
$('ewa').onclick = () => { if (!$('ename').value) return toast('Pehle naam daalo.'); window.open(`https://wa.me/${PHONE}?text=${encodeURIComponent(enqText())}`, '_blank', 'noopener'); };
$('burger').onclick = () => { const o = $('menu').classList.toggle('open'); $('burger').setAttribute('aria-expanded', o); };
$('menu').onclick = () => $('menu').classList.remove('open');

// ---------- Reviews ----------
let rRating = 0;
const starsHtml = n => Array.from({ length: 5 }, (_, i) => `<span class="${i < n ? 'on' : ''}">★</span>`).join('');
document.querySelectorAll('#rstars button').forEach(b => b.onclick = () => {
  rRating = +b.dataset.v;
  document.querySelectorAll('#rstars button').forEach(x => x.classList.toggle('on', +x.dataset.v <= rRating));
});
async function loadReviews() {
  try {
    const { reviews } = await api('reviews');
    $('revList').innerHTML = reviews.length ? reviews.map(r => `<div class="card rev">
        <div class="revtop"><b>${esc(r.name)}</b><span class="rstar">${starsHtml(r.rating)}</span></div>
        <p class="muted">${esc(r.comment)}</p></div>`).join('')
      : '<p class="muted">Abhi koi review nahi hai — sabse pehle aap likho!</p>';
  } catch { $('revList').innerHTML = '<p class="muted">Reviews load nahi hue.</p>'; }
}
$('rform').onsubmit = async e => {
  e.preventDefault();
  if (!rRating) return toast('Pehle star rating chuno.');
  const btn = e.submitter; btn.disabled = true;
  try {
    await api('review', { name: $('rname').value, rating: rRating, comment: $('rcomment').value });
    toast('Review mil gaya! Check hone ke baad website par dikhega.');
    $('rform').reset(); rRating = 0; document.querySelectorAll('#rstars button').forEach(x => x.classList.remove('on'));
  } catch (err) { toast(err.message); }
  btn.disabled = false;
};
loadReviews();

init();
