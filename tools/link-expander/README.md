# ตัวเปิดลิงก์ Google Maps (Cloudflare Worker)

ลิงก์ที่ได้จากการกด Share → Copy link ใน Google Maps เป็นลิงก์สั้น (`https://maps.app.goo.gl/…`)
หน้าเว็บอย่าง Junbi มองไม่เห็นว่าลิงก์นี้พาไปที่ไหน ตัวเปิดลิงก์นี้ถาม Google ให้ แล้วตอบลิงก์เต็มกลับมา
Junbi จึงได้ชื่อและที่อยู่ของสถานที่โดยไม่ต้องพิมพ์ ส่วนปุ่มเปิด Google Maps ใช้ลิงก์ที่คัดลอกมาเสมอ

- ฟรี 100,000 ครั้งต่อวัน ไม่ต้องใส่บัตร
- ไม่เก็บข้อมูลใคร จำผลไว้ตามลิงก์ 30 วันเพื่อตอบเร็วขึ้น
- รับเฉพาะลิงก์ Google Maps และเฉพาะจากเว็บ Junbi (`https://attawit43559.github.io`)

## ติดตั้ง (ประมาณ 10 นาที ทำครั้งเดียว)

1. สมัครบัญชีที่ <https://dash.cloudflare.com/sign-up> ใช้อีเมลกับรหัสผ่าน แล้วยืนยันอีเมล
2. ในหน้า Cloudflare เลือก **Workers & Pages** ที่เมนูซ้าย → กด **Create** (หรือ **Create application**)
3. เลือก **Start with Hello World!** (หรือ **Create Worker**) → ตั้งชื่อ `junbi-links` → กด **Deploy**
   - ถ้า Cloudflare ถามชื่อ subdomain ของบัญชี (`<ชื่อ>.workers.dev`) ตั้งชื่ออะไรก็ได้
4. กด **Edit code** → ลบโค้ดเดิมทั้งหมด → วางโค้ดจากไฟล์ `worker.js` ในโฟลเดอร์นี้ → กด **Deploy**
5. คัดลอกที่อยู่ของ worker ที่แสดงอยู่ เช่น `https://junbi-links.<ชื่อ>.workers.dev`
6. ใส่ที่อยู่นี้ใน `backend.js` ที่บรรทัด `const LINK_EXPANDER = '...';`

ติดตั้งแล้วที่ `https://junbi-links.attawit-charoensri.workers.dev` (8 พ.ย. 2026)

ถ้าไม่ได้ตั้ง `LINK_EXPANDER` Junbi ยังใช้ได้ปกติ: วางลิงก์แล้วพิมพ์ชื่อสถานที่เอง ปุ่มเปิด Google Maps ยังพาไปที่เดียวกับที่คัดลอกมา

## ตู้คำชวน (คำชวนขึ้นที่หน้าแรกของเพื่อน)

worker ตัวเดียวกันนี้เก็บคำชวนเข้าทริปไว้ให้เพื่อนเห็นที่หน้าแรกของ Junbi ต้องมีที่เก็บข้อมูล KV 1 อัน

1. Cloudflare → **Storage & Databases → Workers KV** → **Create** ตั้งชื่อ `junbi-invites`
2. **Workers & Pages** → `junbi-links` → **Settings → Bindings** → **Add binding → KV namespace**
   ตั้งชื่อตัวแปร `INVITES` เลือก `junbi-invites` → **Save**
3. วางโค้ด `worker.js` ล่าสุด แล้ว **Deploy**

- ฟรี: เขียน 1,000 ครั้งต่อวัน (ประมาณ 1,000 คำชวน) อ่าน 100,000 ครั้งต่อวัน เกินแล้วหยุดชั่วคราว ไม่มีการเก็บเงิน
- เก็บแค่ชื่อทริป ชื่อ/อีเมลคนชวน และรหัสไฟล์ ใช้อีเมลคนถูกชวนแบบเข้ารหัส (SHA-256) เป็นชื่อตู้ ลบเมื่อเข้าร่วม/ไม่สนใจ หรือหลัง 30 วัน
- ตรวจกับ Google ว่าคนที่ถามล็อกอิน Junbi ด้วยอีเมลนั้นจริง (`CLIENT_ID` ใน `worker.js`)
- ถ้าไม่มี KV คำชวนยังส่งทางอีเมลของ Google Drive ได้ตามปกติ แค่ไม่ขึ้นที่หน้าแรก

## ทดสอบหลังติดตั้ง

เปิด Junbi → เพิ่มที่สนใจ → วางลิงก์ เช่น `https://maps.app.goo.gl/2X41bCX67Rmbvg3b8`
ควรขึ้นชื่อ **Centre The Bakery** และที่อยู่ในกินซ่าเอง

การเปิดที่อยู่ของ worker ในเบราว์เซอร์ตรงๆ จะได้ `{"error":"not_allowed"}` เป็นเรื่องปกติ เพราะรับเฉพาะคำขอจากเว็บ Junbi
