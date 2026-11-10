/* Junbi link expander (Cloudflare Worker).
   A Google Maps "Copy link" gives a short link (https://maps.app.goo.gl/…). A web page cannot see where it leads,
   so Junbi asks this worker: it asks Google, and answers with the full Google Maps link (place name, address and,
   when Google includes it, the pin). Nothing is stored about anyone; answers are cached by link for 30 days.
   Free plan: 100,000 requests a day, no card. Only Junbi's own site may call it.

   It is also Junbi's invite mailbox (/invites): when someone invites a Gmail, a note "X invited you to trip Y"
   waits here until that person opens Junbi. Only the trip name, the two e-mails and the Drive file ids are kept,
   for 30 days or until they join. Whoever asks must show a Google sign-in made for Junbi; they only ever see
   notes addressed to their own e-mail. Needs a KV namespace bound as INVITES (free: 1,000 writes a day). */

const ALLOWED_ORIGINS = ['https://attawit43559.github.io'];
const SHORT = /^https:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps)\/[A-Za-z0-9_-]+/;
const MAPS = /^https:\/\/((www|maps)\.)?google\.[a-z.]+\/maps|^https:\/\/maps\.google\.[a-z.]+\//i;
const CLIENT_ID = '593453832447-qhu0itir9firda9csuivrknitqs5es2r.apps.googleusercontent.com';   // only sign-ins made for Junbi
const BROWSER = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';
    const cors = ALLOWED_ORIGINS.includes(origin) ? { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin' } : null;
    if (!cors) return json({ error: 'not_allowed' }, 403, {});
    if (request.method === 'OPTIONS') return new Response(null, { headers: { ...cors, 'Access-Control-Allow-Methods': 'GET, POST', 'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Max-Age': '86400' } });
    const path = new URL(request.url).pathname;
    if (path.startsWith('/invites')) return invites(request, env, cors, path);
    if (request.method !== 'GET') return json({ error: 'method' }, 405, cors);

    const link = (new URL(request.url).searchParams.get('u') || '').trim();
    if (!SHORT.test(link)) return json({ error: 'not_a_maps_link' }, 400, cors);

    const cacheKey = new Request('https://junbi-link-cache/' + encodeURIComponent(link));
    const cached = await caches.default.match(cacheKey);
    if (cached) return json(await cached.json(), 200, cors);

    let url = link;
    try {
      for (let hop = 0; hop < 6 && !MAPS.test(url); hop++) {
        const r = await fetch(url, { redirect: 'manual', headers: { 'User-Agent': BROWSER, 'Accept-Language': 'en' } });
        const next = r.headers.get('Location');
        if (next) {
          url = new URL(next, url).href;
          const cont = new URL(url).searchParams.get('continue');   // Google's cookie page in some countries
          if (/^https:\/\/consent\.google\./.test(url) && cont) url = cont;
          continue;
        }
        // some answers are a small page that points onward
        const body = (await r.text()).slice(0, 300000);
        const m = body.match(/https:\/\/(?:www\.|maps\.)?google\.[a-z.]+\/maps[^"'\s<>\\]*/i);
        if (m) url = m[0].replace(/&amp;/g, '&');
        break;
      }
    } catch (e) {
      return json({ error: 'google_unreachable' }, 502, cors);
    }
    if (!MAPS.test(url)) return json({ error: 'unreadable' }, 422, cors);

    const answer = { url };
    ctx.waitUntil(caches.default.put(cacheKey, new Response(JSON.stringify(answer), { headers: { 'Cache-Control': 'max-age=2592000' } })));
    return json(answer, 200, cors);
  }
};

/* ---------- invite mailbox ---------- */
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const KEEP = 30 * 24 * 3600;
async function who(request) {
  const token = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!token || token.length > 4096) return null;
  const r = await fetch('https://oauth2.googleapis.com/tokeninfo?access_token=' + encodeURIComponent(token));
  if (!r.ok) return null;
  const t = await r.json();
  if (CLIENT_ID && t.aud !== CLIENT_ID && t.azp !== CLIENT_ID) return null;
  if (!t.email || String(t.email_verified) !== 'true') return null;
  return String(t.email).toLowerCase();
}
async function box(email) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(email));
  return 'inv:' + [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('');
}
const clean = (v, n) => String(v || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, n);
async function invites(request, env, cors, path) {
  if (!env.INVITES) return json({ error: 'no_mailbox' }, 503, cors);
  const me = await who(request);
  if (!me) return json({ error: 'sign_in' }, 401, cors);
  const now = Math.floor(Date.now() / 1000);
  const read = async key => { try { return (JSON.parse(await env.INVITES.get(key) || '[]') || []).filter(x => x && x.at > now - KEEP); } catch (_) { return []; } };
  const write = (key, list) => list.length ? env.INVITES.put(key, JSON.stringify(list.slice(-20)), { expirationTtl: KEEP }) : env.INVITES.delete(key);

  if (request.method === 'GET' && path === '/invites') return json({ invites: await read(await box(me)) }, 200, cors);
  if (request.method !== 'POST') return json({ error: 'method' }, 405, cors);
  let b = {};
  try { b = await request.json(); } catch (_) { return json({ error: 'bad_request' }, 400, cors); }
  const tripId = clean(b.tripId, 12);
  if (!/^[A-Za-z0-9]{6}$/.test(tripId)) return json({ error: 'bad_request' }, 400, cors);

  if (path === '/invites/remove') {          // joined or not interested: only your own mailbox
    const key = await box(me), list = await read(key);
    await write(key, list.filter(x => x.tripId !== tripId));
    return json({ ok: true }, 200, cors);
  }
  if (path === '/invites') {                 // leave a note for a friend
    const to = clean(b.to, 200).toLowerCase(), spec = clean(b.spec, 1500);
    if (!EMAIL.test(to) || to === me) return json({ error: 'bad_email' }, 400, cors);
    if (!/^[-\w]{10,}(\.[-\w]{10,}){0,40}$/.test(spec)) return json({ error: 'bad_request' }, 400, cors);
    const key = await box(to), list = (await read(key)).filter(x => x.tripId !== tripId);
    list.push({ tripId, spec, name: clean(b.name, 80), from: clean(b.from, 60), fromEmail: me, at: now });
    await write(key, list);
    return json({ ok: true }, 200, cors);
  }
  return json({ error: 'not_found' }, 404, cors);
}

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...headers } });
}
