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
| `backend.js` | สร้างจาก `tools/build-backend.py`: กฎของทริปจาก My Trip (Code.gs) + ที่เก็บบน Drive, ล็อกอิน, Gemini |
| `tools/backend-shim.js`, `tools/backend-browser.js` | ส่วนที่เขียนสำหรับเบราว์เซอร์ แก้ที่นี่แล้วรัน `python3 tools/build-backend.py` |
| `sw.js` | เก็บตัวแอปไว้ในเครื่อง ใช้ออฟไลน์ได้ |
| `plan-export.js` | ส่งออกภาพแผนรายวัน |
| `privacy.html` | นโยบายความเป็นส่วนตัว |

Google Cloud project: `junbi-513612` (OAuth client แบบ Web, redirect `https://attawit43559.github.io/junbi/`)
