/* Junbi link expander (Cloudflare Worker).
   A Google Maps "Copy link" gives a short link (https://maps.app.goo.gl/…). A web page cannot see where it leads,
   so Junbi asks this worker: it asks Google, and answers with the full Google Maps link (place name, address and,
   when Google includes it, the pin). Nothing is stored about anyone; answers are cached by link for 30 days.
   Free plan: 100,000 requests a day, no card. Only Junbi's own site may call it.

   It is also Junbi's invite mailbox (/invites): when someone invites a Gmail, a note "X invited you to trip Y"
   waits here until that person opens Junbi. Only the trip name, the two e-mails and the Drive file ids are kept,
   for 30 days or until they join. Whoever asks must show a Google sign-in made for Junbi; they only ever see
   notes addressed to their own e-mail. Needs a KV namespace bound as INVITES (free: 1,000 writes a day).
   The same store keeps plans shared for friends to copy (/plans): places, ideas, travel and notes, no bookings,
   and what the iPhone shortcut drops (/drop with a personal key; taken by the owner's Junbi with /drops/take, 14 days). */

const ALLOWED_ORIGINS = ['https://attawit43559.github.io'];
const SHORT = /^https:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps)\/[A-Za-z0-9_-]+/;
const MAPS = /^https:\/\/((www|maps)\.)?google\.[a-z.]+\/maps|^https:\/\/maps\.google\.[a-z.]+\//i;
const CLIENT_ID = '593453832447-qhu0itir9firda9csuivrknitqs5es2r.apps.googleusercontent.com';   // only sign-ins made for Junbi
const BROWSER = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';
    // the iPhone shortcut (no web page, no Origin): drop a shared place or file for its owner's Junbi
    if (request.method === 'POST' && new URL(request.url).pathname === '/drop' && !origin) return drop(request, env);
    const cors = ALLOWED_ORIGINS.includes(origin) ? { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin' } : null;
    if (!cors) return json({ error: 'not_allowed' }, 403, {});
    if (request.method === 'OPTIONS') return new Response(null, { headers: { ...cors, 'Access-Control-Allow-Methods': 'GET, POST', 'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Max-Age': '86400' } });
    const path = new URL(request.url).pathname;
    if (path.startsWith('/invites') || path.startsWith('/plans') || path.startsWith('/drops')) return invites(request, env, cors, path);
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
  if (Number(request.headers.get('Content-Length') || 0) > 400000) return json({ error: 'too_big' }, 413, cors);
  let b = {};
  try { b = await request.json(); } catch (_) { return json({ error: 'bad_request' }, 400, cors); }

  // the iPhone shortcut: this person's key, and what it dropped (taken once, then gone)
  if (path === '/drops/key') {
    const mine = await box(me), kk = 'dke:' + mine.slice(4);
    let key = b.reset ? '' : await env.INVITES.get(kk);
    if (!key) {
      const oldKey = await env.INVITES.get(kk);
      if (oldKey) await env.INVITES.delete('dk:' + oldKey);
      key = 'jb' + [...crypto.getRandomValues(new Uint8Array(16))].map(x => x.toString(16).padStart(2, '0')).join('');
      await env.INVITES.put('dk:' + key, mine.slice(4));
      await env.INVITES.put(kk, key);
    }
    return json({ key }, 200, cors);
  }
  if (path === '/drops/take') {
    const id = (await box(me)).slice(4), listKey = 'drops:' + id;
    const list = JSON.parse(await env.INVITES.get(listKey) || '[]');
    if (!list.length) return json({ drops: [] }, 200, cors);
    const out = [];
    for (const d of list) {
      if (d.file) { const f = await env.INVITES.get('dropf:' + d.file); if (f) out.push({ text: d.text || '', at: d.at, file: JSON.parse(f) }); await env.INVITES.delete('dropf:' + d.file); }
      else out.push({ text: d.text || '', at: d.at });
    }
    await env.INVITES.delete(listKey);
    return json({ drops: out }, 200, cors);
  }

  // a plan shared for friends to copy: a snapshot under a 24-character code, kept for a year after the last share
  if (path === '/plans' || path === '/plans/get') {
    const key = String(b.key || '');
    if (!/^[a-f0-9]{24}$/.test(key)) return json({ error: 'bad_request' }, 400, cors);
    const got = await env.INVITES.get('plan:' + key);
    const old = got ? JSON.parse(got) : null;
    if (path === '/plans/get') return old ? json({ plan: old.plan }, 200, cors) : json({ error: 'copy_not_found' }, 404, cors);
    if (old && old.owner !== me) return json({ error: 'not_yours' }, 403, cors);
    if (!b.plan || typeof b.plan !== 'object' || !b.plan.trip) return json({ error: 'bad_request' }, 400, cors);
    await env.INVITES.put('plan:' + key, JSON.stringify({ owner: me, plan: b.plan, at: Math.floor(Date.now() / 1000) }), { expirationTtl: 365 * 24 * 3600 });
    return json({ ok: true, key }, 200, cors);
  }
  const tripId = clean(b.tripId, 12);
  if (!/^[A-Za-z0-9]{6}$/.test(tripId)) return json({ error: 'bad_request' }, 400, cors);

  if (path === '/invites/remove') {          // joined or not interested: only your own mailbox
    const key = await box(me), list = await read(key);
    await write(key, list.filter(x => x.tripId !== tripId));
    return json({ ok: true }, 200, cors);
  }
  if (path === '/invites/cancel') {          // the one who invited takes it back
    const to = clean(b.to, 200).toLowerCase();
    if (!EMAIL.test(to)) return json({ error: 'bad_email' }, 400, cors);
    const key = await box(to), list = await read(key);
    await write(key, list.filter(x => !(x.tripId === tripId && x.fromEmail === me)));
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

/* the shortcut posts { key, url: <what was shared>, data: <base64 of a picture / PDF, or the same text> }
   (the same shape as My Trip's shortcut, with action "shareAny"); answers { ok, data: { message } } for its notification */
async function drop(request, env) {
  const say = (message, status = 200) => json({ ok: status === 200, message, data: { message } }, status, {});
  if (!env.INVITES) return say('Junbi ยังไม่พร้อม ลองใหม่ภายหลัง', 503);
  if (Number(request.headers.get('Content-Length') || 0) > 12000000) return say('ไฟล์ใหญ่เกินไป (ไม่เกิน 8 MB)', 413);
  let b = {};
  try { b = await request.json(); } catch (_) { return say('ส่งไม่สำเร็จ ลองใหม่อีกครั้ง', 400); }
  const key = String(b.key || '').trim();
  const id = /^jb[a-f0-9]{32}$/.test(key) ? await env.INVITES.get('dk:' + key) : null;
  if (!id) return say('รหัสไม่ถูกต้อง เปิด Junbi → โปรไฟล์ → คัดลอกรหัสใหม่', 401);
  const text = clean(b.url, 2000);
  let data = String(b.data || '').replace(/\s/g, '');
  const now = Math.floor(Date.now() / 1000), listKey = 'drops:' + id;
  const list = JSON.parse(await env.INVITES.get(listKey) || '[]').filter(d => d.at > now - 14 * 86400).slice(-9);
  const entry = { text, at: now };
  // a picture or PDF comes as base64 that is not just the shared text again
  let bytes = null;
  try { if (data && data.length > 200) { const bin = atob(data.slice(0, 64)); if (bin.startsWith('%PDF') || bin.charCodeAt(0) === 0xFF || bin.startsWith('\x89PNG') || /ftyp(heic|heix|mif1)/.test(bin)) bytes = data; } } catch (_) {}
  if (bytes) {
    if (bytes.length > 11000000) return say('ไฟล์ใหญ่เกินไป (ไม่เกิน 8 MB)', 413);
    const head = atob(bytes.slice(0, 64));
    const mime = head.startsWith('%PDF') ? 'application/pdf' : head.charCodeAt(0) === 0xFF ? 'image/jpeg' : head.startsWith('\x89PNG') ? 'image/png' : 'image/heic';
    entry.file = [...crypto.getRandomValues(new Uint8Array(8))].map(x => x.toString(16).padStart(2, '0')).join('');
    await env.INVITES.put('dropf:' + entry.file, JSON.stringify({ mime, data: bytes }), { expirationTtl: 14 * 86400 });
  } else if (!/https?:\/\//.test(text)) {
    return say('ส่งได้เฉพาะลิงก์สถานที่ รูป หรือ PDF', 400);
  }
  list.push(entry);
  await env.INVITES.put(listKey, JSON.stringify(list), { expirationTtl: 14 * 86400 });
  return say(entry.file ? 'ส่งไฟล์เข้า Junbi แล้ว เปิดแอปเพื่อให้ AI แนบเข้าทริป' : 'ส่งเข้า Junbi แล้ว เปิดแอปครั้งหน้าจะเข้าทริปให้เอง');
}

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...headers } });
}
