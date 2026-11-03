/* ---- stand-ins for the Apps Script services the trip rules use ---- */
const LS = {
  get(k){ try { return localStorage.getItem(k); } catch(_) { return null; } },
  set(k, v){ try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch(_) {} }
};
const AI_KEY = 'junbi-ai-key', AI_MODEL = 'junbi-ai-model';
const pad = n => String(n).padStart(2, '0');
const Utilities = {
  getUuid: () => (crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); })),
  formatDate(date, tz, fmt){
    let y, mo, d, h, mi;
    if(!tz || tz === 'UTC' || tz === 'GMT'){ y = date.getUTCFullYear(); mo = date.getUTCMonth() + 1; d = date.getUTCDate(); h = date.getUTCHours(); mi = date.getUTCMinutes(); }
    else {
      const p = {}; new Intl.DateTimeFormat('en-GB', {timeZone: tz, year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hourCycle:'h23'}).formatToParts(date).forEach(x => p[x.type] = x.value);
      y = +p.year; mo = +p.month; d = +p.day; h = +p.hour; mi = +p.minute;
    }
    return fmt.replace('yyyy', y).replace('MM', pad(mo)).replace('dd', pad(d)).replace('HH', pad(h)).replace('mm', pad(mi));
  },
  sleep(){},   // the browser versions wait with await instead
  DigestAlgorithm: {}
};
const MEMO = new Map();
const CacheService = { getScriptCache: () => ({
  get: k => MEMO.has(k) && MEMO.get(k).until > Date.now() ? MEMO.get(k).v : null,
  put: (k, v, sec) => { MEMO.set(k, {v, until: Date.now() + (sec || 600) * 1000}); },
  remove: k => { MEMO.delete(k); }
}) };
const PropertiesService = { getScriptProperties: () => ({
  getProperty(name){
    if(name === 'GEMINI_API_KEY') return LS.get(AI_KEY);
    if(name === 'GEMINI_MODEL') return LS.get(AI_MODEL);
    if(name === 'AI_PROVIDER') return 'gemini';
    return null;
  },
  setProperty(){}
}) };
const LockService = { getScriptLock: () => ({ waitLock(){}, releaseLock(){} }) };
