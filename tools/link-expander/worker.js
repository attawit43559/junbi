/* Junbi link expander (Cloudflare Worker).
   A Google Maps "Copy link" gives a short link (https://maps.app.goo.gl/…). A web page cannot see where it leads,
   so Junbi asks this worker: it asks Google, and answers with the full Google Maps link (place name, address and,
   when Google includes it, the pin). Nothing is stored about anyone; answers are cached by link for 30 days.
   Free plan: 100,000 requests a day, no card. Only Junbi's own site may call it. */

const ALLOWED_ORIGINS = ['https://attawit43559.github.io'];
const SHORT = /^https:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps)\/[A-Za-z0-9_-]+/;
const MAPS = /^https:\/\/((www|maps)\.)?google\.[a-z.]+\/maps|^https:\/\/maps\.google\.[a-z.]+\//i;
const BROWSER = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';
    const cors = ALLOWED_ORIGINS.includes(origin) ? { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin' } : null;
    if (!cors) return json({ error: 'not_allowed' }, 403, {});
    if (request.method === 'OPTIONS') return new Response(null, { headers: { ...cors, 'Access-Control-Allow-Methods': 'GET' } });
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

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...headers } });
}
