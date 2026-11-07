# Junbi

วางแผนเที่ยวกับครอบครัว ใช้ฟรี ข้อมูลทุกอย่างอยู่ในบัญชี Google ของผู้ใช้เอง

- **เปิดใช้:** https://attawit43559.github.io/junbi/ (เพิ่มไปยังหน้าจอโฮมได้)
- **ล็อกอิน:** บัญชี Google ของผู้ใช้
- **ข้อมูล:** ไฟล์ JSON หนึ่งไฟล์ต่อทริป และไฟล์ตั๋ว/ใบจอง ในโฟลเดอร์ `Junbi` ใน Google Drive ของผู้ใช้ (สิทธิ์ `drive.file` เห็นเฉพาะไฟล์ที่แอปสร้าง)
- **AI:** คีย์ Gemini ฟรีของผู้ใช้ เก็บในเครื่อง เรียก Google ตรงจากเบราว์เซอร์
- **ไม่มีเซิร์ฟเวอร์:** ผู้พัฒนาไม่มีฐานข้อมูลของใคร และไม่มีค่าใช้จ่าย

## ไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `index.html` | ตัวแอป (มาจาก My Trip) |
| `backend.js` | สร้างจาก `tools/build-backend.py`: กฎของทริปจาก My Trip commit `b42487d` + ที่เก็บบน Drive, ล็อกอิน, Gemini |
| `tools/backend-shim.js`, `tools/backend-browser.js` | ส่วนที่เขียนสำหรับเบราว์เซอร์ แก้ที่นี่แล้วรัน `python3 tools/build-backend.py` |
| `tools/vendor/my-trip-b42487d-Code.gs` | สำเนาหลังบ้านของ My Trip commit `b42487d` สำหรับสร้าง `backend.js` ซ้ำได้ตรงรุ่น |
| `sw.js` | เก็บตัวแอปไว้ในเครื่อง ใช้ออฟไลน์ได้ |
| `plan-export.js` | ส่งออกหน้าสรุปทริปและหน้ารายวัน |
| `lang-en.js` | ข้อความภาษาอังกฤษ |
| `privacy.html` | นโยบายความเป็นส่วนตัว |

Google Cloud project: `junbi-513612` (OAuth client แบบ Web, redirect `https://attawit43559.github.io/junbi/`)

ไฟล์อยู่ใน Drive ของผู้ใช้ แต่การล็อกอินและโควตาการเรียก Drive API ยังผ่าน Google Cloud project ของ Junbi ซึ่งใช้ร่วมกันทุกคน

Junbi ไม่ใช้คีย์ Google Maps ของ My Trip: ลิงก์ Maps ที่แชร์เข้ามาอ่านจากลิงก์ และสถานที่ที่ AI แนะนำจะเปิดเป็นผลค้นหาใน Google Maps ให้ผู้ใช้ตรวจเอง คำสั่งลัด iPhone ของ My Trip ผูกกับหลังบ้านเดิมและไม่ได้ใช้ใน Junbi ส่วน Android ใช้ Web Share Target ของแอปที่ติดตั้งแล้ว ไฟล์ที่แชร์จะจับคู่ด้วย Gemini ของผู้ใช้และเก็บใน Drive ของผู้ใช้
