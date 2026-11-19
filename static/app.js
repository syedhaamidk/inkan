const $ = id => document.getElementById(id);
const S = {ca: null, leaf: null, done: new Set()};
const fine = matchMedia('(pointer:fine)').matches, calm = matchMedia('(prefers-reduced-motion:reduce)').matches;
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
async function api(path, data) {
  const r = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data || {})});
  const j = await r.json().catch(() => ({error: 'The server sent an unreadable reply.'}));
  if (!r.ok) throw new Error(j.error || 'Something went wrong.');
  return j;
}
function toast(msg) { const t = el('div', 'toast', msg); $('toasts').append(t); setTimeout(() => { t.classList.add('is-leaving'); setTimeout(() => t.remove(), 260); }, 2600); }
/* theme, scroll rule, reveals */
const root = document.documentElement;
try { if (localStorage.getItem('sw-theme') === 'dark') root.dataset.theme = 'dark'; } catch (e) {}
function syncTheme() { const d = root.dataset.theme === 'dark'; $('theme').textContent = d ? 'Light sheet' : 'Dark sheet'; $('theme').setAttribute('aria-pressed', d); }
$('theme').onclick = () => { root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark'; try { localStorage.setItem('sw-theme', root.dataset.theme); } catch (e) {} syncTheme(); };
syncTheme();
addEventListener('scroll', () => { const h = document.documentElement; $('rule').style.transform = `scaleX(${h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight)})`; }, {passive: true});
root.classList.add('js-reveals');
const io = 'IntersectionObserver' in window ? new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); } }), {threshold: .12}) : null;
document.querySelectorAll('.reveal-on-scroll,.dim-divider').forEach(n => io ? io.observe(n) : n.classList.add('in-view'));
/* cursor: drafting crosshair with live coordinates */
if (fine && !calm) {
  root.classList.add('fx');
  const ring = $('ring'), lab = $('cl'); let x = -100, y = -100, rx = x, ry = y;
  addEventListener('pointermove', e => {
    x = e.clientX; y = e.clientY; const t = e.target, c = t.closest('.cert,.gate'), d = t.closest('[data-cur]');
    ring.className = '';
    if (t.closest('input:not([type=checkbox]),textarea')) { ring.classList.add('text'); lab.textContent = ''; }
    else if (t.closest('button,a')) { ring.classList.add('press'); lab.textContent = '[ ' + ((d && d.dataset.cur) || 'go') + ' ]'; }
    else if (c) { ring.classList.add('lens'); lab.textContent = '[ inspect ]'; }
    else lab.textContent = `x ${Math.round(x)}  y ${Math.round(y)}`;
    if (c) { const b = c.getBoundingClientRect(), px = (e.clientX - b.left) / b.width, py = (e.clientY - b.top) / b.height;
      c.style.setProperty('--mx', px * 100 + '%'); c.style.setProperty('--my', py * 100 + '%');
      if (c.classList.contains('cert')) { c.style.setProperty('--ry', (px - .5) * 8 + 'deg'); c.style.setProperty('--rx', (.5 - py) * 6 + 'deg'); } }
  });
  addEventListener('pointerout', e => { const c = e.target.closest && e.target.closest('.cert'); if (c && !c.contains(e.relatedTarget)) { c.style.setProperty('--rx', '0deg'); c.style.setProperty('--ry', '0deg'); } });
  addEventListener('pointerdown', () => ring.classList.add('down'));
  addEventListener('pointerup', e => { ring.classList.remove('down'); const i = el('div', 'imprint'); i.style.left = e.clientX + 'px'; i.style.top = e.clientY + 'px'; document.body.append(i); setTimeout(() => i.remove(), 750); });
  (function loop() { rx += (x - rx) * .3; ry += (y - ry) * .3; ring.style.transform = `translate(${rx}px,${ry}px)`; requestAnimationFrame(loop); })();
}
/* seals: solid ring = passed, double ring = failed */
function seal(state, label) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', '0 0 120 120'); s.setAttribute('class', 'seal stamp ' + state); s.setAttribute('role', 'img'); s.setAttribute('aria-label', label);
  s.innerHTML = state === 'bad'
    ? '<circle cx="60" cy="60" r="56" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="60" cy="60" r="47" fill="none" stroke="currentColor" stroke-width="3"/><text x="60" y="65" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-weight="500" fill="currentColor"></text>'
    : '<circle cx="60" cy="60" r="56" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="60" cy="60" r="48" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2 4"/><text x="60" y="65" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-weight="500" fill="currentColor"></text>';
  const t = s.querySelector('text'); t.textContent = label; t.setAttribute('font-size', label.length > 6 ? 12 : label.length > 3 ? 15 : 20); return s;
}
function identicon(hex) {
  const b = hex.match(/../g).map(h => parseInt(h, 16)), n = 5; let r = '';
  for (let y = 0; y < n; y++) for (let x = 0; x < 3; x++) if (b[1 + y * 3 + x] & 1) { r += `<rect x="${x}" y="${y}" width="1" height="1"/>`; if (x < 2) r += `<rect x="${n - 1 - x}" y="${y}" width="1" height="1"/>`; }
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); s.setAttribute('viewBox', '-.5 -.5 6 6'); s.setAttribute('class', 'idn'); s.setAttribute('role', 'img');
  s.setAttribute('aria-label', 'Visual fingerprint of this certificate'); s.innerHTML = `<rect x="-.5" y="-.5" width="6" height="6" fill="#F6F6F6"/><g fill="#0A0A0A">${r}</g>`; return s;
}
function certCard(i, state, label) {
  const w = el('div', 'tilt'), c = el('div', 'card cert reg-corners spotlight tilt-inner'); w.append(c); c.append(seal(state, label));
  c.append(el('span', 'card-tag', i.is_ca ? 'CERTIFICATE AUTHORITY' : 'WEBSITE CERTIFICATE'), el('h3', 'h3', i.subject));
  const dl = el('dl'), rows = [['Issued by', i.self_signed ? i.issuer + ' (itself)' : i.issuer], ['Valid from', i.not_before.slice(0, 10)], ['Valid until', i.not_after.slice(0, 10)],
    ['Names', i.san.length ? i.san.join(', ') : 'none'], ['Algorithm', i.sig_alg + ', ' + i.key], ['Serial', i.serial]];
  rows.forEach(([k, v]) => dl.append(el('dt', '', k), el('dd', '', v)));
  const fp = el('dd', 'fp'); fp.append(identicon(i.fingerprint), el('span', '', i.fingerprint)); dl.append(el('dt', '', 'Fingerprint'), fp); c.append(dl); return w;
}
function pemBlock(title, pem, file) {
  const d = el('details'); d.append(el('summary', '', title), el('pre', '', pem));
  const b = el('button', 'btn btn-secondary btn-sm', 'Download ' + file); b.dataset.cur = 'save'; b.onclick = () => { const a = el('a'); a.href = URL.createObjectURL(new Blob([pem])); a.download = file; a.click(); };
  d.append(b); return d;
}
function busy(btn, fn) { return async () => { btn.disabled = true; try { await fn(); } finally { btn.disabled = false; } }; }
function fail(out, e) { out.replaceChildren(el('p', 'err', e.message)); }
function done(k) { S.done.add(k); document.querySelector(`#steps a[data-k=${k}]`).textContent = document.querySelector(`#steps a[data-k=${k}]`).textContent.replace(' ✓', '') + ' ✓';
  $('prog-n').textContent = S.done.size + ' / 4'; $('prog').style.setProperty('--value', S.done.size * 25 + '%'); }
/* steps */
$('ca-go').onclick = busy($('ca-go'), async () => {
  const out = $('ca-out');
  try { const r = await api('/api/ca', {name: $('ca-name').value}); S.ca = r; $('ca-pem').value = r.cert;
    out.replaceChildren(certCard(r.info, 'ok', 'CA'), pemBlock('Authority certificate (public)', r.cert, 'ca.crt'), pemBlock('Authority private key (keep secret)', r.key, 'ca.key')); done('ca'); toast('Authority created');
  } catch (e) { fail(out, e); }
});
$('issue-go').onclick = busy($('issue-go'), async () => {
  const out = $('issue-out');
  try { if (!S.ca) throw new Error('Create an authority on sheet 01 first.');
    const r = await api('/api/issue', {ca_cert: S.ca.cert, ca_key: S.ca.key, hostname: $('host').value, days: $('days').value, expired: $('expired').checked});
    S.leaf = r; $('leaf-pem').value = r.cert; $('visit').value = $('host').value;
    out.replaceChildren(certCard(r.info, 'ok', 'SIGNED'), pemBlock('Certificate (public)', r.cert, $('host').value + '.crt'), pemBlock('Private key (stays on the server)', r.key, $('host').value + '.key')); done('issue'); toast('Certificate signed');
  } catch (e) { fail(out, e); }
});
async function check() {
  const out = $('check-out');
  try {
    const r = await api('/api/verify', {cert: $('leaf-pem').value, ca_cert: $('ca-pem').value, hostname: $('visit').value});
    const box = el('div'); box.append(certCard(r.info, r.valid ? 'ok' : 'bad', r.valid ? 'TRUSTED' : 'REJECTED'));
    const ul = el('div', 'out-list');
    r.checks.forEach((c, n) => { const a = el('div', 'alert ' + (c.ok ? 'alert-accent' : 'alert-danger')); a.style.animationDelay = n * 180 + 'ms';
      a.append(el('span', 'alert-tag', c.ok ? 'PASS' : 'FAIL')); const t = el('span'); t.append(el('b', '', c.name + '. '), document.createTextNode(c.detail)); a.append(t); ul.append(a); });
    box.append(ul, el('p', 'h3 verdict', r.valid ? 'The browser shows the padlock.' : 'The browser shows a security warning.')); out.replaceChildren(box); done('check');
  } catch (e) { fail(out, e); }
}
$('check-go').onclick = busy($('check-go'), check);
$('swap').onclick = busy($('swap'), async () => { try { const r = await api('/api/ca', {name: 'Different Authority'}); $('ca-pem').value = r.cert; await check(); } catch (e) { fail($('check-out'), e); } });
$('tamper').onclick = busy($('tamper'), async () => {
  const L = $('leaf-pem').value.split('\n'), i = L.length - 3;
  if (i < 2) return fail($('check-out'), new Error('Sign a certificate first.'));
  const p = Math.min(8, L[i].length - 3); L[i] = L[i].slice(0, p) + (L[i][p] === 'A' ? 'B' : 'A') + L[i].slice(p + 1); $('leaf-pem').value = L.join('\n'); await check(); toast('One character changed');
});
$('restore').onclick = () => { if (S.leaf) { $('leaf-pem').value = S.leaf.cert; if (S.ca) $('ca-pem').value = S.ca.cert; check(); toast('Original restored'); } };
$('lab-go').onclick = busy($('lab-go'), async () => {
  const out = $('lab-out'); out.replaceChildren(el('div', 'empty', 'Knocking on five gates…'));
  try {
    const r = await api('/api/lab'), g = el('div', 'gates');
    r.results.forEach(x => { const c = el('div', 'card gate wait spotlight'); c.append(el('span', 'card-tag', 'GATE'), el('h3', 'card-title', x.name), el('p', 'text-sm text-soft', x.why), el('div', 'd', x.detail)); g.append(c); }); out.replaceChildren(g);
    r.results.forEach((x, n) => setTimeout(() => { const c = g.children[n]; c.classList.remove('wait'); c.classList.add('revealed'); c.querySelector('.card-tag').replaceWith(el('span', 'badge ' + (x.accepted ? 'badge-accent' : 'badge-danger'), x.accepted ? 'OPEN' : 'SHUT')); c.append(seal(x.accepted ? 'ok' : 'bad', x.accepted ? 'OPEN' : 'SHUT')); }, 300 + n * 400));
    setTimeout(() => { done('lab'); toast('Gauntlet complete'); }, 300 + r.results.length * 400);
  } catch (e) { fail(out, e); }
});
/* handshake figure */
const HS = [
  {from: 'c', t: 'ClientHello', cap: 'The browser says: I speak TLS 1.3, here are my ciphers and a one-time public key.'},
  {from: 's', t: 'ServerHello', cap: 'The server picks AES-256-GCM and sends its own one-time key. Both sides now compute the same secret.'},
  {from: 's', t: 'Certificate + signature', enc: true, cap: 'The line turns solid: everything is encrypted from here. The server shows its certificate and signs the conversation to prove it owns the key.'},
  {from: 'v', t: 'Checking the seal', cap: 'The browser runs the checks from sheet 03: signature, dates and website name.'},
  {from: 'c', t: 'Finished', cap: 'Both sides confirm nobody tampered with the handshake. Application data can flow.'}];
let hi = -1, timer = null;
const dots = $('dots'); HS.forEach(() => dots.append(el('i')));
function place(side) { const T = $('track'), P = $('packet'), nw = T.querySelector('.node').offsetWidth + 8; return side === 'c' ? nw : T.offsetWidth - nw - P.offsetWidth; }
function step(n) {
  hi = n; const T = $('track'), P = $('packet'), s = HS[n], nodes = T.querySelectorAll('.node');
  P.textContent = s.t; P.style.transition = 'none'; P.classList.add('show');
  const a = s.from === 's' ? 's' : 'c', b = s.from === 'c' ? 's' : 'c';
  P.style.left = place(a) + 'px'; void P.offsetWidth; P.style.transition = ''; P.style.left = place(b) + 'px';
  nodes.forEach(x => x.classList.remove('on')); nodes[s.from === 's' ? 1 : 0].classList.add('on');
  if (s.from === 'v') nodes[0].classList.add('on');
  if (s.enc) { T.classList.add('enc'); $('wire-note').textContent = 'encrypted'; }
  $('cap').textContent = s.cap; [...dots.children].forEach((d, i) => d.classList.toggle('on', i <= n));
  $('hs-play').textContent = n === HS.length - 1 ? 'Replay handshake' : 'Play handshake';
}
function reset() { clearTimeout(timer); hi = -1; $('track').classList.remove('enc'); $('wire-note').textContent = 'unencrypted'; $('packet').classList.remove('show'); [...dots.children].forEach(d => d.classList.remove('on')); document.querySelectorAll('.node').forEach(n => n.classList.remove('on')); }
function play() { reset(); (function next() { step(++hi); if (hi < HS.length - 1) timer = setTimeout(next, 2300); })(); }
$('hs-play').onclick = play;
$('hs-next').onclick = () => { clearTimeout(timer); step(hi >= HS.length - 1 ? (reset(), 0) : hi + 1); };
