"""One-time port of My Trip's page to Junbi: own Google sign-in + Drive storage (backend.js),
the user's own Gemini key, new name and storage keys that never touch My Trip's data on the same site."""
import pathlib, re
p = pathlib.Path('/home/claude/junbi/index.html'); s = p.read_text()
def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= 1, ('missing', old[:80])
    if count == 1: assert n == 1, ('not unique', old[:80], n)
    s = s.replace(old, new)

# ---- name, icons, scripts ----
rep('<meta name="apple-mobile-web-app-title" content="My Trip">', '<meta name="apple-mobile-web-app-title" content="Junbi">')
rep('<link rel="apple-touch-icon" href="icons/apple-touch-icon.png?v=14">', '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png?v=1">')
rep('<script src="https://accounts.google.com/gsi/client" async></script>', '<script src="backend.js"></script>')
rep('<title>My Trip</title>', '<title>Junbi</title>')
# storage keys: the same site also hosts My Trip, so nothing may share its names
s = s.replace('"mytrip-', '"junbi-app-').replace("'mytrip-", "'junbi-app-").replace('`mytrip-', '`junbi-app-')
assert 'mytrip-' not in s.replace('mytrip-share', ''), [m.start() for m in re.finditer('mytrip-', s)][:5]
rep('String(t.name || "My Trip")', 'String(t.name || "Junbi")')

# ---- talking to the backend in the browser instead of Apps Script ----
rep('const CONNECTED = /^https:\\/\\/script\\.google\\.com\\//.test(API_URL);', 'const CONNECTED = true;')
old_api = s[s.index('async function api(action, body={}, signal){'):s.index('/* writes wait in an outbox')]
rep(old_api, '''async function api(action, body={}, signal){
  if(signal && signal.aborted) throw {code:"cancelled"};
  try { return await JunbiBackend.call(action, body); }
  catch(e){
    const code = (e && e.code) || "server_error";
    if(code === "auth_required" && action !== "login") needLogin();
    if(code === "reauth") needReconnect();
    if(code === "missing_GEMINI_API_KEY" || code === "bad_ai_key") aiNeeded(code);
    throw {code};
  }
}
''')
rep("if(e.code==='offline'||e.code==='server_error'){setTimeout(flush,8000);break;}", "if(e.code==='offline'||e.code==='server_error'||e.code==='reauth'||e.code==='drive_busy'){setTimeout(flush,e.code==='reauth'?60000:8000);break;}")
rep('function fail(e){ toast(e && e.code === "offline" ? "ไม่มีอินเทอร์เน็ต ลองใหม่อีกครั้ง" : e && e.code === "not_connected" ? "ยังไม่ได้เชื่อม Google Sheet" : "เชื่อมต่อไม่สำเร็จ ลองใหม่อีกครั้ง"); }',
    'function fail(e){ const c = e && e.code; if(c === "missing_GEMINI_API_KEY" || c === "bad_ai_key") return; toast(c === "offline" ? "ไม่มีอินเทอร์เน็ต ลองใหม่อีกครั้ง" : c === "reauth" ? "ต้องเชื่อม Google Drive อีกครั้งก่อน" : c === "rate_limited" ? "AI ฟรีใช้ครบโควตาชั่วคราว ลองใหม่อีกสักครู่" : "เชื่อมต่อไม่สำเร็จ ลองใหม่อีกครั้ง"); }')

# ---- sign-in page ----
old_login = s[s.index('function vLogin(){'):s.index('/* the iPhone shortcut')]
rep(old_login, '''function vLogin(){
  return `<main class="screen login">
    <img class="wordmark" src="icons/logo-wordmark.svg" alt="Junbi">
    <p class="tagline">วางแผนเที่ยวกับครอบครัว ข้อมูลอยู่ใน Google Drive ของคุณเอง</p>
    <button class="g-btn" data-act="google-login" ${S.loggingIn ? "disabled" : ""}><svg viewBox="0 0 48 48" width="20" height="20" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.5l6.7-6.7C35.6 2.4 30.2 0 24 0 14.6 0 6.6 5.4 2.7 13.2l7.8 6.1C12.4 13.6 17.7 9.5 24 9.5z"/><path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4 7.1-10 7.1-17.5z"/><path fill="#FBBC05" d="M10.5 28.7c-.5-1.4-.8-3-.8-4.7s.3-3.2.8-4.7l-7.8-6.1C1 16.6 0 20.2 0 24s1 7.4 2.7 10.8l7.8-6.1z"/><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.5-5.8c-2.1 1.4-4.8 2.3-8.4 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.8 6.1C6.6 42.6 14.6 48 24 48z"/></svg>${S.loggingIn ? "กำลังเข้าสู่ระบบ…" : "เข้าสู่ระบบด้วย Google"}</button>
    ${/\\bLine\\/|FBAN|FBAV|Instagram|MicroMessenger/i.test(navigator.userAgent) ? `<p class="note" style="max-width:300px">Google ไม่ให้เข้าสู่ระบบในเบราว์เซอร์ของแอปแชต กดเมนู ⋯ แล้วเลือก "เปิดใน Safari" หรือ "เปิดในเบราว์เซอร์" ก่อนนะ</p>` : ""}
    ${S.loginErr ? `<p class="err" role="alert">${esc(S.loginErr)}</p>` : ""}
    <ul class="promise"><li>${ic("check",16)}ฟรี ไม่มีค่าใช้จ่าย</li><li>${ic("check",16)}ทริปและไฟล์ตั๋วเก็บในโฟลเดอร์ Junbi ใน Drive ของคุณ แอปเห็นเฉพาะไฟล์ที่แอปสร้าง</li><li>${ic("check",16)}ใช้ AI ฟรีของ Google ด้วยบัญชีคุณเอง (เปิดทีหลังได้)</li></ul>
    <a class="muted small" href="privacy.html" target="_blank" rel="noopener">นโยบายความเป็นส่วนตัว</a>
  </main>`;
}
''')
# no iPhone shortcut (it needed a server); account sheet gets AI and Drive instead
old_acc = s[s.index('function vAccount(){'):s.index('function vJoin(){')]
rep(old_acc, '''function vAccount(){
  const key = JunbiBackend.aiKey();
  return `<div class="scrim" data-act="close-sheet"><div class="sheet" role="dialog" aria-modal="true" aria-label="บัญชี" data-stop="1">
    <div class="hd"><h2>${esc(S.myName)}</h2><button class="round" data-act="close-sheet" aria-label="ปิด">${ic("close")}</button></div>
    <p class="muted small" style="margin-top:-8px">${esc(S.user && S.user.email || "")}</p>
    <div class="menu">
      <button data-act="ai-setup">${ic("spark",20)}<span class="grow">AI ผู้ช่วย</span><span class="muted small">${key ? "เชื่อมแล้ว" : "ยังไม่เชื่อม"}</span></button>
      <a href="https://drive.google.com/drive/search?q=Junbi" target="_blank" rel="noopener">${ic("file",20)}<span class="grow">ข้อมูลของฉันใน Google Drive</span>${ic("ext",16)}</a>
      <a href="privacy.html" target="_blank" rel="noopener">${ic("info",20)}<span class="grow">นโยบายความเป็นส่วนตัว</span>${ic("ext",16)}</a>
      <button class="danger" data-act="logout">${ic("leave",20)}ออกจากระบบ</button>
    </div>
  </div></div>`;
}
/* connecting the person's own free Gemini key: get it from Google AI Studio, copy, come back, paste */
function vAiSetup(s){
  const key = JunbiBackend.aiKey(), mask = k => k.slice(0, 6) + "••••" + k.slice(-4);
  const why = s.why === "missing_GEMINI_API_KEY" ? `<p class="note">${ic("info",18)}<span>ส่วนนี้ใช้ AI ช่วย เชื่อม AI ฟรีครั้งเดียว ใช้เวลาประมาณ 1 นาที</span></p>` : s.why === "bad_ai_key" ? `<p class="err">คีย์ AI ใช้ไม่ได้แล้ว ลองสร้างคีย์ใหม่</p>` : "";
  return `<div class="scrim" data-act="close-sheet"><div class="sheet ai-setup" role="dialog" aria-modal="true" aria-label="เชื่อม AI" data-stop="1">
    <div class="hd"><h2>AI ผู้ช่วย</h2><button class="round" data-act="close-sheet" aria-label="ปิด">${ic("close")}</button></div>
    ${why}
    ${key && !s.editing ? `<div class="ai-ok">${ic("check",20)}<span><b>เชื่อม AI แล้ว</b><br><span class="muted small">Gemini · คีย์ ${esc(mask(key))}</span></span></div>
      <p class="muted small">AI ใช้อ่านตั๋วและใบจอง ช่วยดูแผน แปลการ์ดแท็กซี่และข้อมูลฉุกเฉิน</p>
      <div class="menu"><button data-act="ai-change">${ic("edit",20)}เปลี่ยนคีย์</button><button class="danger" data-act="ai-remove">${ic("trash",20)}เลิกเชื่อม AI</button></div>` : `
      <p class="muted small">ใช้ Gemini ของ Google ฟรีด้วยบัญชีของคุณเอง คีย์เก็บในเครื่องนี้เท่านั้น</p>
      <ol class="ai-steps">
        <li><span class="n">1</span><span class="grow">เปิดหน้า Google AI Studio แล้วกด <b>Create API key</b></span><a class="pill-btn" href="https://aistudio.google.com/apikey" target="_blank" rel="noopener" data-act="ai-get-key">เปิด${ic("ext",14)}</a></li>
        <li><span class="n">2</span><span class="grow">กด <b>คัดลอก</b> ที่คีย์ (ขึ้นต้นด้วย AIza…) แล้วกลับมาที่แอปนี้</span></li>
        <li><span class="n">3</span><span class="grow">กดวางคีย์</span><button class="pill-btn primary" data-act="ai-paste" ${s.busy ? "disabled" : ""}>วางคีย์</button></li>
      </ol>
      <form class="ai-key-row" data-form="ai-key"><label class="sr" for="ai-key">คีย์ Gemini</label><input id="ai-key" name="key" placeholder="หรือวางคีย์ตรงนี้" autocomplete="off" autocapitalize="off" spellcheck="false" value="${esc(s.key || "")}" data-bind="sheet:key"><button type="submit" ${s.busy ? "disabled" : ""}>${s.busy ? "กำลังลอง…" : "ใช้คีย์นี้"}</button></form>
      ${s.err ? `<p class="err" role="alert">${esc(s.err)}</p>` : ""}
      <details class="ai-more"><summary>เรื่องความเป็นส่วนตัวและโควตา</summary><p class="muted small">คำขอ AI ส่งตรงจากเครื่องคุณไปที่ Google ไม่ผ่านเซิร์ฟเวอร์ของ Junbi · แบบฟรีมีโควตาต่อวัน ถ้าครบแอปจะบอกให้ลองใหม่ทีหลัง · ในแบบฟรี Google อาจใช้ข้อความที่ส่งไปเพื่อปรับปรุงบริการ ข้อมูลฉุกเฉินจะแปลครั้งเดียวแล้วเก็บไว้</p></details>`}
  </div></div>`;
}
''')
rep('  if(s.kind === "account") return vAccount();', '  if(s.kind === "account") return vAccount();\n  if(s.kind === "ai-setup") return vAiSetup(s);')
rep('    <button data-act="account">${ic("info",20)}บัญชีและคำสั่งลัด</button>', '    <button data-act="account">${ic("info",20)}บัญชีและ AI</button>')

# ---- invitations come with Drive sharing (next step); joining by code needs the trip file shared first ----
old_inv = s[s.index('    <section class="card stack" style="gap:14px">\n      <h2 style="font-size:18px;font-weight:500">ลิงก์ชวนเพื่อน</h2>'):s.index('    <section class="stack">\n      <div class="sec-h"><h2>ผู้ร่วมทริป</h2>')]
rep(old_inv, '''    <section class="card stack" style="gap:10px">
      <h2 style="font-size:18px;font-weight:500">ชวนเพื่อนร่วมทริป</h2>
      <p class="muted small">กำลังทำให้แชร์ทริปผ่าน Google Drive ได้ เร็วๆ นี้จะชวนครอบครัวมาแก้แผนด้วยกันได้</p>
    </section>
''')
rep('    <form class="join-row" data-form="join">', '    ${"" ? `<form class="join-row" data-form="join">')
rep('placeholder="รหัสทริปจากเพื่อน" autocomplete="off" value="${esc(S.joinCode)}" data-bind="root:joinCode"><button type="submit">เข้าร่วม</button></form>', 'placeholder="รหัสทริปจากเพื่อน" autocomplete="off" value="${esc(S.joinCode)}" data-bind="root:joinCode"><button type="submit">เข้าร่วม</button></form>` : ""}\n    ${!JunbiBackend.aiKey() && !S.aiCardHidden ? `<button class="ai-card" data-act="ai-setup">${ic("spark",22)}<span class="grow"><b>เชื่อม AI ฟรี</b><br><span class="muted small">ให้แอปอ่านตั๋ว ช่วยดูแผน และแปลภาษาให้ ตั้งครั้งเดียว 1 นาที</span></span>${ic("chev")}</button>` : ""}')

# ---- actions ----
rep('    case "logout": logout(); break;', '''    case "logout": logout(); break;
    case "google-login": S.loggingIn = true; S.loginErr = ""; render(); JunbiBackend.signIn(); break;
    case "reconnect": JunbiBackend.signIn(""); break;
    case "ai-setup": S.sheet = {kind:"ai-setup"}; render(); break;
    case "ai-change": if(S.sheet && S.sheet.kind === "ai-setup"){ S.sheet.editing = true; render(); } break;
    case "ai-remove": JunbiBackend.setAiKey(""); if(S.sheet) S.sheet.editing = false; render(); toast("เลิกเชื่อม AI แล้ว"); break;
    case "ai-get-key": break;
    case "ai-paste": {
      let txt = ""; try { txt = await navigator.clipboard.readText(); } catch(_){}
      const k = (String(txt).match(/AIza[0-9A-Za-z_\\-]{30,}/) || [""])[0];
      if(!k){ if(S.sheet){ S.sheet.err = "ยังไม่เจอคีย์ในคลิปบอร์ด คัดลอกคีย์จาก Google AI Studio แล้วกดอีกครั้ง หรือวางในช่องด้านล่าง"; render(); } break; }
      aiTry(k); break; }''')
rep('function setSession(sess){', '''/* the AI key: try it once, keep it only when Google answers */
async function aiTry(k){
  const s = S.sheet; if(!s || s.kind !== "ai-setup" || s.busy) return;
  s.busy = true; s.err = ""; s.key = k; render();
  try { await JunbiBackend.testAiKey(k); JunbiBackend.setAiKey(k); s.editing = false; s.why = ""; s.key = ""; toast("เชื่อม AI แล้ว");
    if(s.then){ const f = s.then; S.sheet = null; render(); f(); return; } }
  catch(e){ s.err = e && e.code === "bad_ai_key" ? "คีย์นี้ใช้ไม่ได้ ตรวจว่าคัดลอกครบ (ขึ้นต้นด้วย AIza)" : e && e.code === "offline" ? "ไม่มีอินเทอร์เน็ต ลองใหม่อีกครั้ง" : e && e.code === "rate_limited" ? "คีย์ใช้ได้ แต่โควตาฟรีเต็มชั่วคราว ลองใหม่อีกสักครู่" : "ตอนนี้เชื่อม AI ไม่ได้ ลองใหม่อีกครั้ง"; }
  finally { s.busy = false; render(); }
}
function aiNeeded(code){
  if(S.sheet && S.sheet.kind === "ai-setup") return;
  setTimeout(() => { S.sheet = {kind:"ai-setup", why:code}; render(); }, 0);
}
/* the Drive key lasts an hour: when it runs out the app asks once, saved changes wait meanwhile */
function needReconnect(){
  if(document.getElementById("reauth")) return;
  const b = document.createElement("button");
  b.id = "reauth"; b.className = "reauth"; b.type = "button";
  b.innerHTML = "เชื่อม Google Drive อีกครั้งเพื่อบันทึกข้อมูล";
  b.onclick = () => JunbiBackend.signIn("");
  document.body.appendChild(b);
}
function setSession(sess){''')
rep('''  if(S.view === "login") return;
  try { localStorage.removeItem(SESSION_KEY); } catch(_){}''', '''  if(S.view === "login") return;
  try { localStorage.removeItem(SESSION_KEY); } catch(_){}
  JunbiBackend.signOut();''')
rep('''  try { await api("logout"); } catch(_){}
  try { localStorage.removeItem(SESSION_KEY); } catch(_){}
  try { google.accounts.id.disableAutoSelect(); } catch(_){}''', '''  JunbiBackend.signOut();
  try { localStorage.removeItem(SESSION_KEY); } catch(_){}''')
# the ai-key form
i = s.index('document.addEventListener("submit"') if 'document.addEventListener("submit"' in s else -1
assert i > 0
j = s.index('{', s.index('=>', i)) + 1
s = s[:j] + '\n  if(e.target && e.target.dataset && e.target.dataset.form === "ai-key"){ e.preventDefault(); const k = (String(S.sheet && S.sheet.key || "").match(/AIza[0-9A-Za-z_\\-]{30,}/) || [""])[0]; if(!k){ S.sheet.err = "คีย์ต้องขึ้นต้นด้วย AIza ลองคัดลอกใหม่"; render(); return; } aiTry(k); return; }' + s[j:]

# ---- boot: finish the Google sign-in, refresh an expired Drive key, then open the app ----
rep('''(() => {
  let sess = null; try { sess = JSON.parse(localStorage.getItem(SESSION_KEY)); } catch(_){}
  setSession(sess && sess.token ? sess : null);''', '''(async () => {
  let back = null; try { back = await JunbiBackend.finishSignIn(); } catch(_){}
  let err = null; try { err = sessionStorage.getItem("junbi-auth-error"); sessionStorage.removeItem("junbi-auth-error"); } catch(_){}
  const u = JunbiBackend.user();
  if(back && C.lastUser && C.lastUser !== back.uid){ C.trips = {}; C.items = {}; C.myTrips = []; C.outbox = []; }
  if(back){ C.lastUser = back.uid; persist(); }
  setSession(u ? {token:"drive", user:u} : null);
  if(err && !u) S.loginErr = err === "access_denied" ? "ยังไม่ได้อนุญาตให้ Junbi ใช้ Google Drive ลองใหม่อีกครั้ง" : "เข้าสู่ระบบไม่สำเร็จ ลองใหม่อีกครั้ง";
  if(err === "drive_scope_missing") S.loginErr = "ต้องติ๊กอนุญาตให้ Junbi เก็บไฟล์ใน Google Drive ด้วย ลองเข้าสู่ระบบอีกครั้ง";
  // an hour-old Drive key: get a new one quietly from Google (once a minute at most)
  const quiet = () => { let last = 0; try { last = +sessionStorage.getItem("junbi-refresh") || 0; } catch(_){} return Date.now() - last > 60000; };
  if(u && !JunbiBackend.tokenOk() && navigator.onLine){
    if(err === "interaction_required" || err === "login_required" || err === "consent_required") needReconnect();
    else if(quiet()){ try { sessionStorage.setItem("junbi-refresh", String(Date.now())); } catch(_){} JunbiBackend.refresh(); return; }
  }''')
rep('''  const refresh = () => { checkUpdate(); if(!S.token) return; flush();''', '''  const refresh = () => { checkUpdate(); if(!S.token) return;
    if(!JunbiBackend.tokenOk() && navigator.onLine && !busyForm()){ let last = 0; try { last = +sessionStorage.getItem("junbi-refresh") || 0; } catch(_){} if(Date.now() - last > 60000){ try { sessionStorage.setItem("junbi-refresh", String(Date.now())); } catch(_){} JunbiBackend.refresh(); return; } }
    flush();''')

# ---- styles for the new parts ----
rep('.login h1{font-size:28px;margin:0}', '''.login h1{font-size:28px;margin:0}
.login .wordmark{width:230px;max-width:70vw;height:auto}
.login .tagline{margin:-6px 0 6px;color:var(--muted);max-width:300px;line-height:1.5}
.g-btn{display:inline-flex;align-items:center;gap:12px;height:52px;padding:0 24px;border-radius:999px;border:0;background:#fff;color:#1f1f1f;font:inherit;font-weight:500;font-size:16px;box-shadow:0 0 0 1px #dadce0,0 2px 6px rgba(0,0,0,.08);cursor:pointer}
.g-btn:disabled{opacity:.6}
.login .promise{list-style:none;padding:0;margin:8px 0 0;display:flex;flex-direction:column;gap:8px;text-align:left;max-width:320px;font-size:14px;color:var(--muted)}
.login .promise li{display:flex;gap:8px;align-items:flex-start}.login .promise svg{flex:none;margin-top:3px;color:#0B4A8C}
.ai-card{display:flex;align-items:center;gap:12px;width:100%;text-align:left;padding:14px 16px;border-radius:18px;border:0;background:var(--surface);color:inherit;font:inherit;box-shadow:inset 0 0 0 1px var(--line)}
.ai-card>svg:first-child{color:#0B4A8C;flex:none}
.ai-steps{list-style:none;padding:0;margin:4px 0;display:flex;flex-direction:column;gap:12px}
.ai-steps li{display:flex;align-items:center;gap:10px;font-size:15px}
.ai-steps .n{width:26px;height:26px;border-radius:50%;background:var(--tile);display:grid;place-items:center;font-weight:600;font-size:13px;flex:none}
.ai-steps .pill-btn{flex:none;display:inline-flex;gap:4px;align-items:center;text-decoration:none}
.ai-key-row{display:flex;gap:8px}.ai-key-row input{flex:1;min-width:0;height:44px;border-radius:14px;border:0;box-shadow:inset 0 0 0 1px var(--line);background:var(--surface);padding:0 12px;font-size:14px}
.ai-key-row button{height:44px;border-radius:14px;border:0;background:var(--ink);color:var(--bg);padding:0 14px;font:inherit;font-weight:500}
.ai-ok{display:flex;gap:10px;align-items:center;padding:12px 14px;border-radius:16px;background:var(--tile)}.ai-ok>svg{color:#0B4A8C}
.ai-more summary{cursor:pointer;font-size:14px;color:var(--muted)}
.menu a{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit}
.reauth{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(84px + env(safe-area-inset-bottom));z-index:60;border:0;border-radius:999px;background:#0B4A8C;color:#fff;padding:12px 18px;font:inherit;font-weight:500;box-shadow:0 6px 20px rgba(11,74,140,.35)}''')
p.write_text(s)
print('patched', len(s))

# ---- leftovers of the Apps Script version ----
s = pathlib.Path('/home/claude/junbi/index.html').read_text()
def cut(a, b):
    global s
    i = s.index(a); j = s.index(b, i); s = s[:i] + s[j:]
s = s.replace('  if(S.view === "login") mountGoogleButton();\n', '')
cut('/* the iPhone shortcut', 'function vAccount(){')
cut('const GOOGLE_CLIENT_ID', 'const SESSION_KEY')
cut('let gisReady = false;', 'function afterLogin(){')
import re as _re
s = _re.sub(r'const API_URL = "[^"]*";\n', '', s)
assert 'mountGoogleButton' not in s and 'API_URL' not in s and 'google.accounts' not in s
pathlib.Path('/home/claude/junbi/index.html').write_text(s)
print('cleaned', len(s))
